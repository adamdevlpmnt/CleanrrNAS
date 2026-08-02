import os
from dataclasses import dataclass
from typing import Generator, List, Optional
from app.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class FileStats:
    path: str
    name: str
    size: int
    inode: int
    device_id: int
    nlink: int
    mtime: float

class FilesystemService:
    def scan_video_files(self, directory: str, extensions: List[str], exclude_dirs: Optional[List[str]] = None) -> Generator[FileStats, None, None]:
        exclude_dirs = [os.path.abspath(d) for d in (exclude_dirs or [])]
        
        for root, dirs, files in os.walk(directory):
            abs_root = os.path.abspath(root)
            
            # Skip excluded directories
            if any(abs_root.startswith(ex) for ex in exclude_dirs):
                dirs[:] = []
                continue
                
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions:
                    file_path = os.path.join(root, file)
                    if os.path.islink(file_path):
                        continue
                        
                    stats = self.get_file_stat(file_path)
                    if stats:
                        yield stats

    def get_file_stat(self, path: str) -> Optional[FileStats]:
        try:
            st = os.stat(path)
            return FileStats(
                path=path,
                name=os.path.basename(path),
                size=st.st_size,
                inode=st.st_ino,
                device_id=st.st_dev,
                nlink=st.st_nlink,
                mtime=st.st_mtime
            )
        except Exception as e:
            logger.error(f"Failed to stat file {path}: {e}")
            return None

    def get_directory_size(self, directory: str) -> int:
        total_size = 0
        for dirpath, _, filenames in os.walk(directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except:
                        pass
        return total_size
