import threading
import time
import json
from datetime import datetime
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from app.models.scan import ScanSession
from app.models.file import ScannedFile
from app.services.sonarr import SonarrClient
from app.services.radarr import RadarrClient
from app.services.qbittorrent import QBittorrentClient
from app.services.filesystem import FilesystemService
from app.services.hardlink import HardlinkAnalyzer
from app.services.analyzer import FileAnalyzer
from app.schemas.scan import ScanProgressResponse
from app.utils.logging import get_logger
from app.database import SessionLocal

logger = get_logger(__name__)

class ScannerService:
    _scan_progress: Dict[int, ScanProgressResponse] = {}
    
    def __init__(self, settings, db_session_factory):
        self.settings = settings
        self.db_session_factory = db_session_factory
        
    def start_scan(self) -> int:
        db = self.db_session_factory()
        try:
            session = ScanSession(status="pending")
            db.add(session)
            db.commit()
            db.refresh(session)
            session_id = session.id
            
            self.__class__._scan_progress[session_id] = ScanProgressResponse(
                scan_id=session_id, status="pending", progress_percent=0.0, files_scanned=0, current_file=None
            )
            
            thread = threading.Thread(target=self._run_scan, args=(session_id,), daemon=True)
            thread.start()
            
            return session_id
        finally:
            db.close()

    def _run_scan(self, session_id: int):
        db = self.db_session_factory()
        try:
            session = db.query(ScanSession).filter(ScanSession.id == session_id).first()
            if not session:
                return
                
            session.status = "running"
            db.commit()
            self._update_progress(session_id, "running", 5.0, 0, "Connecting to APIs...")
            
            # API connections
            sonarr = SonarrClient(self.settings.SONARR_URL, self.settings.SONARR_API_KEY)
            radarr = RadarrClient(self.settings.RADARR_URL, self.settings.RADARR_API_KEY)
            qbit = QBittorrentClient(self.settings.QBITTORRENT_URL, self.settings.QBITTORRENT_USERNAME, self.settings.QBITTORRENT_PASSWORD)
            
            self._update_progress(session_id, "running", 10.0, 0, "Fetching Sonarr/Radarr libraries...")
            sonarr_paths = sonarr.get_all_library_file_paths()
            radarr_paths = radarr.get_all_library_file_paths()
            all_lib_paths = sonarr_paths.union(radarr_paths)
            
            self._update_progress(session_id, "running", 20.0, 0, "Fetching qBittorrent seeding paths...")
            seeding_paths = qbit.get_active_seeding_paths(min_days=self.settings.HIT_AND_RUN_DAYS)
            
            fs_svc = FilesystemService()
            hl_svc = HardlinkAnalyzer()
            analyzer = FileAnalyzer()
            
            self._update_progress(session_id, "running", 30.0, 0, "Building library inodes...")
            library_inodes = hl_svc.get_library_inodes(all_lib_paths)
            
            self._update_progress(session_id, "running", 40.0, 0, "Building download directory inode map...")
            exts = [ext.strip() for ext in self.settings.VIDEO_EXTENSIONS.split(",")]
            library_dirs = [self.settings.SONARR_LIBRARY_PATH, self.settings.RADARR_LIBRARY_PATH]
            
            # Build map including downloads and libraries to catch cross-links correctly if needed
            inode_map = hl_svc.build_inode_map([self.settings.DOWNLOADS_PATH] + library_dirs, exts)
            
            self._update_progress(session_id, "running", 60.0, 0, "Scanning download files...")
            
            total_size = 0
            reclaimable_size = 0
            orphan_count = 0
            protected_count = 0
            scanned_files_list = []
            
            # Scan downloads directory, excluding the library directories
            file_gen = fs_svc.scan_video_files(self.settings.DOWNLOADS_PATH, exts, exclude_dirs=library_dirs)
            
            # Since generator doesn't have length, we just increment counter
            count = 0
            for stats in file_gen:
                count += 1
                if count % 10 == 0:
                    self._update_progress(session_id, "running", min(60.0 + (count * 0.1), 95.0), count, stats.name)
                
                classification = analyzer.classify_file(stats, library_inodes, set(library_dirs), seeding_paths, inode_map)
                
                total_size += stats.size
                if classification.status.startswith("ORPHAN"):
                    orphan_count += 1
                    reclaimable_size += classification.real_space_gain
                elif classification.status.startswith("PROTECTED"):
                    protected_count += 1
                    
                linked_paths = hl_svc.get_linked_paths((stats.device_id, stats.inode), inode_map)
                
                scanned_file = ScannedFile(
                    scan_session_id=session_id,
                    file_path=stats.path,
                    file_name=stats.name,
                    file_size=stats.size,
                    inode=stats.inode,
                    device_id=stats.device_id,
                    hardlink_count=stats.nlink,
                    status=classification.status,
                    status_reason=classification.status_reason,
                    real_space_gain=classification.real_space_gain,
                    media_type=classification.media_type,
                    media_title=classification.media_title,
                    torrent_hash=classification.torrent_info.get("hash") if classification.torrent_info else None,
                    torrent_name=classification.torrent_info.get("name") if classification.torrent_info else None,
                    completion_date=datetime.fromtimestamp(classification.torrent_info.get("completion_on")) if classification.torrent_info and classification.torrent_info.get("completion_on", 0) > 0 else None,
                    linked_paths=json.dumps(linked_paths)
                )
                scanned_files_list.append(scanned_file)
                
                if len(scanned_files_list) >= 100:
                    db.bulk_save_objects(scanned_files_list)
                    db.commit()
                    scanned_files_list = []
                    
            if scanned_files_list:
                db.bulk_save_objects(scanned_files_list)
                db.commit()
                
            self._update_progress(session_id, "completed", 100.0, count, None)
            
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            session.total_files_scanned = count
            session.orphan_count = orphan_count
            session.protected_count = protected_count
            session.total_size_scanned = total_size
            session.reclaimable_size = reclaimable_size
            db.commit()
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            session = db.query(ScanSession).filter(ScanSession.id == session_id).first()
            if session:
                session.status = "failed"
                session.error_message = str(e)
                session.completed_at = datetime.utcnow()
                db.commit()
            self._update_progress(session_id, "failed", 0.0, 0, str(e))
        finally:
            db.close()
            
    def _update_progress(self, session_id: int, status: str, percent: float, files_scanned: int, current_file: Optional[str]):
        self.__class__._scan_progress[session_id] = ScanProgressResponse(
            scan_id=session_id,
            status=status,
            progress_percent=percent,
            files_scanned=files_scanned,
            current_file=current_file
        )
        
    def get_progress(self, session_id: int) -> Optional[ScanProgressResponse]:
        return self.__class__._scan_progress.get(session_id)
        
    def get_latest_scan(self) -> Optional[ScanSession]:
        db = self.db_session_factory()
        try:
            return db.query(ScanSession).filter(ScanSession.status == "completed").order_by(ScanSession.started_at.desc()).first()
        finally:
            db.close()

# Singleton instance initialized in lifespan
scanner_service = None
def get_scanner_service():
    return scanner_service
def set_scanner_service(svc):
    global scanner_service
    scanner_service = svc
