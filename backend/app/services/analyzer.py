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
    quality_info: Optional[str] = None

class FileAnalyzer:
    def classify_file(self, file_stats: FileStats, library_inodes: Set[Tuple[int, int]], library_paths: Set[str], seeding_paths: Dict[str, Dict], inode_map: Dict[Tuple[int, int], list[str]], library_file_info: Dict[str, Dict] = None) -> FileClassification:
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

        # 4. Is it orphan safe or no gain?
        status = "UNKNOWN"
        reason = "Unable to determine file status confidently"
        gain = 0
        
        if file_stats.nlink == 1:
            status = "ORPHAN_SAFE"
            reason = "File has no other hardlinks and is safe to delete"
            gain = file_stats.size
        else:
            linked_paths = inode_map.get(file_inode, [])
            other_paths = [p for p in linked_paths if p != abs_path]
            if other_paths:
                status = "ORPHAN_NO_GAIN"
                reason = f"File has hardlinks elsewhere (e.g. {other_paths[0]}) but not in known libraries"
                gain = 0
                
        if status in ("ORPHAN_SAFE", "ORPHAN_NO_GAIN"):
            media_title = None
            media_type = None
            quality_info = None
            
            if library_file_info:
                match = self._find_library_match(abs_path, library_file_info)
                if match:
                    media_title = match.get("title", "")
                    episode = match.get("episode", "")
                    if episode:
                        media_title = f"{media_title} {episode}"
                    quality_kept = match.get("quality", "")
                    media_type = match.get("source", "")
                    quality_info = f"Release gardée: {quality_kept}"
                    
            return self._build_result(status, reason, gain, media_type, media_title, torrent_info=None, quality_info=quality_info)

        return self._build_result("UNKNOWN", "Unable to determine file status confidently", 0)

    def _find_library_match(self, file_path: str, library_file_info: Dict[str, Dict]) -> Optional[Dict]:
        """Try to find a matching library entry for an orphan file based on parent directory name."""
        import re
        # Get the parent directory name of the orphan file (e.g. "Breaking.Bad.S01E01.720p...")
        parent_dir = os.path.basename(os.path.dirname(file_path))
        if not parent_dir:
            return None
        
        # Clean the name for comparison: remove quality tags, release group, etc.
        # Extract the base media name (e.g. "Breaking Bad S01E01" or "Movie Name 2023")
        clean_name = re.sub(r'[._]', ' ', parent_dir)
        # Remove common quality/release tags
        clean_name = re.sub(r'(720p|1080p|2160p|4K|REMUX|BluRay|WEB-DL|WEBRip|HDTV|x264|x265|H\.?264|H\.?265|HEVC|AVC|DTS|AAC|MULTI|VOSTFR|FRENCH|MULTi|TrueHD|Atmos|DDP5|DD5|HDR|DV|DoVi).*', '', clean_name, flags=re.IGNORECASE).strip()
        
        if len(clean_name) < 3:
            return None
        
        best_match = None
        best_score = 0
        
        for lib_path, info in library_file_info.items():
            lib_title = info.get("title", "")
            # For series: check if the series title is in the directory name
            if info.get("source") == "sonarr":
                episode_str = info.get("episode", "")
                # Check if both title and episode match
                if lib_title.lower() in clean_name.lower() and episode_str.lower().replace("e", "e").replace("s", "s") in clean_name.lower().replace("e", "e").replace("s", "s"):
                    score = len(lib_title) + len(episode_str)
                    if score > best_score:
                        best_score = score
                        best_match = info
            elif info.get("source") == "radarr":
                # For movies: extract just the title (without year) for comparison
                movie_title = re.sub(r'\s*\(\d{4}\)$', '', lib_title)
                if movie_title.lower() in clean_name.lower():
                    score = len(movie_title)
                    if score > best_score:
                        best_score = score
                        best_match = info
        
        return best_match

    def _match_torrent(self, file_path: str, seeding_paths: Dict[str, Dict]) -> Optional[Dict]:
        for torrent_path, t_info in seeding_paths.items():
            if file_path.startswith(torrent_path) or file_path == torrent_path:
                return t_info
        return None

    def _match_media(self, file_path: str, library_paths: Set[str]) -> Optional[Dict]:
        # Simple extraction based on folder logic could go here
        return None

    def _build_result(self, status: str, reason: str, gain: int, media_type: str = None, media_title: str = None, torrent_info: Dict = None, quality_info: str = None) -> FileClassification:
        return FileClassification(
            status=status,
            status_reason=reason,
            real_space_gain=gain,
            media_type=media_type,
            media_title=media_title,
            torrent_info=torrent_info,
            quality_info=quality_info
        )
