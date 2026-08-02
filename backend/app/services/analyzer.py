import os
from dataclasses import dataclass
from typing import Dict, Set, Tuple, Optional, Any
from app.services.filesystem import FileStats

@dataclass
class FileClassification:
    status: str
    status_reason: str
    real_space_gain: int
    media_type: Optional[str]
    media_title: Optional[str]
    torrent_info: Optional[Dict[str, Any]]

class FileAnalyzer:
    def classify_file(self, file_stats: FileStats, library_inodes: Set[Tuple[int, int]], library_paths: Set[str], seeding_paths: Dict[str, Dict], inode_map: Dict[Tuple[int, int], list[str]]) -> FileClassification:
        abs_path = os.path.abspath(file_stats.path)
        file_inode = (file_stats.device_id, file_stats.inode)
        
        # 1. Is it inside library paths?
        if any(abs_path.startswith(os.path.abspath(lib_dir)) for lib_dir in library_paths):
            return self._build_result("PROTECTED_LIBRARY", "File is located within a media library directory", 0)

        # 2. Is it hardlinked to library?
        if file_inode in library_inodes:
            return self._build_result("PROTECTED_HARDLINK", "File is hardlinked to a library item", 0)

        # 3. Is it in active torrents?
        torrent_info = self._match_torrent(abs_path, seeding_paths)
        if torrent_info:
            state = torrent_info.get("state", "")
            if state in ("downloading", "stalledDL", "metaDL"):
                return self._build_result("PROTECTED_DOWNLOADING", "File is currently downloading in qBittorrent", 0, torrent_info=torrent_info)
            else:
                return self._build_result("PROTECTED_SEEDING", "File is recently completed and seeding in qBittorrent", 0, torrent_info=torrent_info)

        # 4. Is it orphan safe?
        if file_stats.nlink == 1:
            return self._build_result("ORPHAN_SAFE", "File has no other hardlinks and is safe to delete", file_stats.size)

        # 5. Is it orphan no gain?
        linked_paths = inode_map.get(file_inode, [])
        other_paths = [p for p in linked_paths if p != abs_path]
        if other_paths:
            reason = f"File has hardlinks elsewhere (e.g. {other_paths[0]}) but not in known libraries"
            return self._build_result("ORPHAN_NO_GAIN", reason, 0)
            
        return self._build_result("UNKNOWN", "Unable to determine file status confidently", 0)

    def _match_torrent(self, file_path: str, seeding_paths: Dict[str, Dict]) -> Optional[Dict]:
        for torrent_path, t_info in seeding_paths.items():
            if file_path.startswith(torrent_path) or file_path == torrent_path:
                return t_info
        return None

    def _match_media(self, file_path: str, library_paths: Set[str]) -> Optional[Dict]:
        # Simple extraction based on folder logic could go here
        return None

    def _build_result(self, status: str, reason: str, gain: int, media_type: str = None, media_title: str = None, torrent_info: Dict = None) -> FileClassification:
        return FileClassification(
            status=status,
            status_reason=reason,
            real_space_gain=gain,
            media_type=media_type,
            media_title=media_title,
            torrent_info=torrent_info
        )
