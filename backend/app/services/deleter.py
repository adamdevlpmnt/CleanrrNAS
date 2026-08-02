import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.file import ScannedFile
from app.models.deletion import DeletionLog
from app.schemas.deletion import DeletionPreviewResponse, DeletionExecuteResponse
from app.services.qbittorrent import QBittorrentClient
from app.utils.logging import get_logger

logger = get_logger(__name__)

class DeletionService:
    def preview_deletion(self, file_ids: List[int], db: Session) -> DeletionPreviewResponse:
        files = db.query(ScannedFile).filter(ScannedFile.id.in_(file_ids)).all()
        total_size = 0
        real_gain = 0
        warnings = []
        
        for f in files:
            total_size += f.file_size
            try:
                st = os.stat(f.file_path)
                if st.st_nlink == 1:
                    real_gain += f.file_size
                else:
                    warnings.append(f"File {f.file_name} still has {st.st_nlink} hardlinks, deleting it may not free space.")
            except Exception as e:
                warnings.append(f"File {f.file_name} cannot be accessed: {e}")
                
            if not f.status.startswith("ORPHAN"):
                warnings.append(f"File {f.file_name} has status {f.status}, deleting it might cause issues.")
                
        return DeletionPreviewResponse(
            files=files, # Note: Pydantic handles ORM objects with from_attributes
            total_size=total_size,
            real_gain=real_gain,
            warnings=warnings
        )
        
    def execute_deletion(self, file_ids: List[int], db: Session, qbit_client: QBittorrentClient = None) -> DeletionExecuteResponse:
        files = db.query(ScannedFile).filter(ScannedFile.id.in_(file_ids)).all()
        deleted_count = 0
        space_freed = 0
        errors = []
        
        for f in files:
            try:
                if os.path.exists(f.file_path):
                    st = os.stat(f.file_path)
                    os.remove(f.file_path)
                    freed = st.st_size if st.st_nlink == 1 else 0
                    space_freed += freed
                    deleted_count += 1
                    
                    torrent_removed = False
                    if f.torrent_hash and qbit_client:
                        # Optionally remove torrent if it was the only file
                        qbit_client.delete_torrent(f.torrent_hash, delete_files=False)
                        torrent_removed = True
                        
                    log = DeletionLog(
                        file_path=f.file_path,
                        file_name=f.file_name,
                        file_size=f.file_size,
                        real_space_freed=freed,
                        status_at_deletion=f.status,
                        reason="Manual deletion via API",
                        scan_session_id=f.scan_session_id,
                        torrent_hash=f.torrent_hash,
                        torrent_removed=torrent_removed
                    )
                    db.add(log)
                    
                    # Remove empty dirs
                    dir_path = os.path.dirname(f.file_path)
                    try:
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                    except:
                        pass
                else:
                    errors.append(f"File {f.file_path} does not exist.")
            except Exception as e:
                errors.append(f"Failed to delete {f.file_path}: {e}")
                logger.error(f"Deletion error for {f.file_path}: {e}")
                
        db.commit()
        return DeletionExecuteResponse(deleted_count=deleted_count, space_freed=space_freed, errors=errors)
