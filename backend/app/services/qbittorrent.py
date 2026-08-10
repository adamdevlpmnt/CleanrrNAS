import httpx
from typing import Tuple, List, Dict, Optional
import time
from app.utils.logging import get_logger

logger = get_logger(__name__)

class QBittorrentClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = httpx.Client(timeout=30.0)
        self._authenticated = False

    def _login(self) -> bool:
        if not self.base_url or not self.username:
            return False
        try:
            resp = self.client.post(
                f"{self.base_url}/api/v2/auth/login",
                data={"username": self.username, "password": self.password}
            )
            resp.raise_for_status()
            if resp.text == "Ok.":
                self._authenticated = True
                return True
            return False
        except Exception as e:
            logger.error(f"QBittorrent login failed: {e}")
            return False

    def _ensure_auth(self) -> bool:
        if not self._authenticated:
            return self._login()
        return True

    def test_connection(self) -> Tuple[bool, str]:
        if not self._ensure_auth():
            return False, "Login failed"
        try:
            resp = self.client.get(f"{self.base_url}/api/v2/app/version")
            resp.raise_for_status()
            return True, resp.text
        except Exception as e:
            if getattr(e, "response", None) and e.response.status_code == 403: # type: ignore
                self._authenticated = False
                if self._login():
                    return self.test_connection()
            logger.error(f"QBittorrent connection test failed: {e}")
            return False, str(e)

    def get_torrents(self, filter_type: str = "all") -> List[Dict]:
        if not self._ensure_auth():
            return []
        try:
            resp = self.client.get(f"{self.base_url}/api/v2/torrents/info", params={"filter": filter_type})
            if resp.status_code == 403:
                self._authenticated = False
                if self._ensure_auth():
                    resp = self.client.get(f"{self.base_url}/api/v2/torrents/info", params={"filter": filter_type})
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to get QBittorrent torrents: {e}")
            return []

    def get_torrent_files(self, torrent_hash: str) -> List[Dict]:
        if not self._ensure_auth():
            return []
        try:
            resp = self.client.get(f"{self.base_url}/api/v2/torrents/files", params={"hash": torrent_hash})
            if resp.status_code == 403:
                self._authenticated = False
                if self._ensure_auth():
                    resp = self.client.get(f"{self.base_url}/api/v2/torrents/files", params={"hash": torrent_hash})
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to get files for torrent {torrent_hash}: {e}")
            return []

    def get_active_seeding_paths(self, min_days: int = 7) -> Dict[str, Dict]:
        torrents = self.get_torrents()
        seeding_paths = {}
        now = time.time()
        
        for t in torrents:
            completion_time = t.get("completion_on", 0)
            if completion_time <= 0:
                is_active = True
            else:
                days_since_completion = (now - completion_time) / (24 * 3600)
                is_active = days_since_completion < min_days or t.get("state") in ("downloading", "stalledDL", "metaDL")

            if is_active:
                content_path = t.get("content_path")
                if content_path:
                    seeding_paths[content_path] = t
        return seeding_paths

    def get_all_torrent_paths(self) -> Dict[str, Dict]:
        torrents = self.get_torrents()
        all_paths = {}
        for t in torrents:
            content_path = t.get("content_path")
            if content_path:
                all_paths[content_path] = {
                    "hash": t.get("hash"),
                    "name": t.get("name"),
                    "state": t.get("state"),
                    "completion_on": t.get("completion_on"),
                    "seeding_time": t.get("seeding_time"),
                    "ratio": t.get("ratio"),
                    "save_path": t.get("save_path"),
                    "content_path": content_path
                }
        return all_paths

    def delete_torrent(self, torrent_hash: str, delete_files: bool = False):
        if not self._ensure_auth():
            return
        try:
            self.client.post(
                f"{self.base_url}/api/v2/torrents/delete",
                data={"hashes": torrent_hash, "deleteFiles": str(delete_files).lower()}
            )
        except Exception as e:
            logger.error(f"Failed to delete torrent {torrent_hash}: {e}")

    def __del__(self):
        try:
            self.client.close()
        except:
            pass
