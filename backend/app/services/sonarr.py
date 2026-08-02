import httpx
from typing import Tuple, List, Set, Dict
from app.utils.logging import get_logger

logger = get_logger(__name__)

class SonarrClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.Client(
            headers={"X-Api-Key": self.api_key},
            timeout=30.0
        )

    def test_connection(self) -> Tuple[bool, str]:
        if not self.base_url or not self.api_key:
            return False, "Not configured"
        try:
            resp = self.client.get(f"{self.base_url}/api/v3/system/status")
            resp.raise_for_status()
            data = resp.json()
            return True, data.get("version", "Unknown")
        except Exception as e:
            logger.error(f"Sonarr connection test failed: {e}")
            return False, str(e)

    def get_series(self) -> List[Dict]:
        try:
            resp = self.client.get(f"{self.base_url}/api/v3/series")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to get Sonarr series: {e}")
            return []

    def get_episode_files(self, series_id: int) -> List[Dict]:
        try:
            resp = self.client.get(f"{self.base_url}/api/v3/episodefile?seriesId={series_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to get Sonarr episode files for series {series_id}: {e}")
            return []

    def get_all_library_file_paths(self) -> Set[str]:
        paths = set()
        series_list = self.get_series()
        for series in series_list:
            ep_files = self.get_episode_files(series["id"])
            for f in ep_files:
                if "path" in f:
                    paths.add(f["path"])
        return paths

    def get_root_folders(self) -> List[Dict]:
        try:
            resp = self.client.get(f"{self.base_url}/api/v3/rootfolder")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to get Sonarr root folders: {e}")
            return []

    def __del__(self):
        try:
            self.client.close()
        except:
            pass
