import threading
import time
import json
import traceback
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
            logger.info(f"[Scan {session_id}] Starting scan thread...")
            session = db.query(ScanSession).filter(ScanSession.id == session_id).first()
            if not session:
                logger.error(f"[Scan {session_id}] Session not found in DB, aborting.")
                return
                
            session.status = "running"
            db.commit()
            self._update_progress(session_id, "running", 5.0, 0, "Connecting to APIs...")
            
            # API connections
            logger.info(f"[Scan {session_id}] Connecting to Sonarr: {self.settings.SONARR_URL}")
            sonarr = SonarrClient(self.settings.SONARR_URL, self.settings.SONARR_API_KEY)
            logger.info(f"[Scan {session_id}] Connecting to Radarr: {self.settings.RADARR_URL}")
            radarr = RadarrClient(self.settings.RADARR_URL, self.settings.RADARR_API_KEY)
            logger.info(f"[Scan {session_id}] Connecting to qBittorrent: {self.settings.QBITTORRENT_URL}")
            qbit = QBittorrentClient(self.settings.QBITTORRENT_URL, self.settings.QBITTORRENT_USERNAME, self.settings.QBITTORRENT_PASSWORD)
            
            self._update_progress(session_id, "running", 10.0, 0, "Fetching Sonarr/Radarr libraries...")
            logger.info(f"[Scan {session_id}] Fetching Sonarr library paths...")
            sonarr_paths = sonarr.get_all_library_file_paths()
            logger.info(f"[Scan {session_id}] Sonarr returned {len(sonarr_paths)} paths")
            logger.info(f"[Scan {session_id}] Fetching Radarr library paths...")
            radarr_paths = radarr.get_all_library_file_paths()
            logger.info(f"[Scan {session_id}] Radarr returned {len(radarr_paths)} paths")
            all_lib_paths = sonarr_paths.union(radarr_paths)
            
            self._update_progress(session_id, "running", 20.0, 0, "Fetching qBittorrent seeding paths...")
            logger.info(f"[Scan {session_id}] Fetching qBittorrent seeding paths (HnR days: {self.settings.HIT_AND_RUN_DAYS})...")
            seeding_paths = qbit.get_active_seeding_paths(min_days=self.settings.HIT_AND_RUN_DAYS)
            logger.info(f"[Scan {session_id}] qBittorrent returned {len(seeding_paths)} active seeding paths")

            logger.info(f"[Scan {session_id}] Fetching Sonarr series details...")
            sonarr_file_info = sonarr.get_series_with_files()
            logger.info(f"[Scan {session_id}] Sonarr file info: {len(sonarr_file_info)} entries")

            logger.info(f"[Scan {session_id}] Fetching Radarr movie details...")
            radarr_file_info = radarr.get_movies_with_files()
            logger.info(f"[Scan {session_id}] Radarr file info: {len(radarr_file_info)} entries")

            library_file_info = {**sonarr_file_info, **radarr_file_info}

            
            fs_svc = FilesystemService()
            hl_svc = HardlinkAnalyzer()
            analyzer = FileAnalyzer()
            
            self._update_progress(session_id, "running", 30.0, 0, "Building library inodes...")
            logger.info(f"[Scan {session_id}] Building library inodes from {len(all_lib_paths)} library file paths...")
            library_inodes = hl_svc.get_library_inodes(all_lib_paths)
            logger.info(f"[Scan {session_id}] Built {len(library_inodes)} unique library inodes")
            
            self._update_progress(session_id, "running", 40.0, 0, "Building download directory inode map...")
            exts = [ext.strip() for ext in self.settings.VIDEO_EXTENSIONS.split(",")]
            library_dirs = [self.settings.SONARR_LIBRARY_PATH, self.settings.RADARR_LIBRARY_PATH]
            
            # Build inode map for downloads only (libraries already covered by library_inodes)
            # Using DOWNLOADS_PATH only avoids redundant scanning of library dirs
            logger.info(f"[Scan {session_id}] Building inode map for: {[self.settings.DOWNLOADS_PATH]} (extensions: {exts})")
            logger.info(f"[Scan {session_id}] Library dirs (will also be scanned for cross-links): {library_dirs}")
            inode_map = hl_svc.build_inode_map([self.settings.DOWNLOADS_PATH] + library_dirs, exts)
            logger.info(f"[Scan {session_id}] Inode map built with {len(inode_map)} unique inodes")
            
            self._update_progress(session_id, "running", 60.0, 0, "Scanning download files...")
            logger.info(f"[Scan {session_id}] Starting file scan in {self.settings.DOWNLOADS_PATH} (excluding {library_dirs})...")
            
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
                
                classification = analyzer.classify_file(stats, library_inodes, set(library_dirs), seeding_paths, inode_map, library_file_info)
                
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
                    quality_info=classification.quality_info,
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
                
            logger.info(f"[Scan {session_id}] Scan complete: {count} files scanned, {orphan_count} orphans, {protected_count} protected, reclaimable={reclaimable_size}")
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
            logger.error(f"[Scan {session_id}] Scan FAILED with exception: {e}")
            logger.error(f"[Scan {session_id}] Full traceback:\n{traceback.format_exc()}")
            try:
                session = db.query(ScanSession).filter(ScanSession.id == session_id).first()
                if session:
                    session.status = "failed"
                    session.error_message = str(e)
                    session.completed_at = datetime.utcnow()
                    db.commit()
            except Exception as db_err:
                logger.error(f"[Scan {session_id}] Failed to update session status in DB: {db_err}")
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
            return db.query(ScanSession).order_by(ScanSession.started_at.desc()).first()
        finally:
            db.close()

# Singleton instance initialized in lifespan
scanner_service = None
def get_scanner_service():
    return scanner_service
def set_scanner_service(svc):
    global scanner_service
    scanner_service = svc
