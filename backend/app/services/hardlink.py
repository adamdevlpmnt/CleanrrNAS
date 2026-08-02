import os
from typing import Dict, List, Set, Tuple, Optional
from app.utils.logging import get_logger

logger = get_logger(__name__)

class HardlinkAnalyzer:
    def build_inode_map(self, directories: List[str], extensions: List[str]) -> Dict[Tuple[int, int], List[str]]:
        inode_map: Dict[Tuple[int, int], List[str]] = {}
        for directory in directories:
            for root, _, files in os.walk(directory):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in extensions:
                        file_path = os.path.join(root, file)
                        if os.path.islink(file_path):
                            continue
                        try:
                            st = os.stat(file_path)
                            key = (st.st_dev, st.st_ino)
                            if key not in inode_map:
                                inode_map[key] = []
                            inode_map[key].append(file_path)
                        except Exception as e:
                            logger.error(f"Failed to stat {file_path} for inode map: {e}")
        return inode_map

    def get_library_inodes(self, library_paths: Set[str]) -> Set[Tuple[int, int]]:
        inodes = set()
        for path in library_paths:
            try:
                st = os.stat(path)
                inodes.add((st.st_dev, st.st_ino))
            except Exception as e:
                # File might not exist on disk even if Sonarr/Radarr thinks it does
                logger.debug(f"Could not stat library file {path}: {e}")
        return inodes

    def is_hardlinked_to_library(self, file_inode: Tuple[int, int], library_inodes: Set[Tuple[int, int]]) -> bool:
        return file_inode in library_inodes

    def compute_real_gain(self, file_path: str, nlink: int, inode_key: Tuple[int, int], inode_map: Dict[Tuple[int, int], List[str]], files_to_delete: Optional[Set[str]] = None) -> int:
        try:
            st = os.stat(file_path)
            size = st.st_size
        except:
            return 0
            
        if nlink == 1:
            return size
            
        linked_files = set(inode_map.get(inode_key, []))
        if files_to_delete:
            remaining_links = len(linked_files - set(files_to_delete))
            if remaining_links == 0:
                return size
        return 0

    def get_linked_paths(self, inode_key: Tuple[int, int], inode_map: Dict[Tuple[int, int], List[str]]) -> List[str]:
        return inode_map.get(inode_key, [])
