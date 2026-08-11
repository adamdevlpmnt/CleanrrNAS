from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SONARR_URL: str = ""
    SONARR_API_KEY: str = ""
    RADARR_URL: str = ""
    RADARR_API_KEY: str = ""
    QBITTORRENT_URL: str = ""
    QBITTORRENT_USERNAME: str = ""
    QBITTORRENT_PASSWORD: str = ""
    DOWNLOADS_PATH: str = "/data"
    SONARR_LIBRARY_PATHS: str = "/data/Series_4K"
    RADARR_LIBRARY_PATHS: str = "/data/Film"
    DATABASE_URL: str = "sqlite:////config/mediacleaner.db"
    HIT_AND_RUN_DAYS: int = 7
    VIDEO_EXTENSIONS: str = ".mkv,.mp4,.avi,.ts,.wmv,.m4v,.mov,.flv,.webm"
    LOG_LEVEL: str = "INFO"
    APP_PORT: int = 9876
    QBITTORRENT_PATH_MAPPING: str = ""

    def get_qbittorrent_path_mapping(self) -> dict[str, str]:
        mapping = {}
        if self.QBITTORRENT_PATH_MAPPING:
            parts = self.QBITTORRENT_PATH_MAPPING.split(",")
            for part in parts:
                if ":" in part:
                    src, dst = part.split(":", 1)
                    mapping[src.strip()] = dst.strip()
        return mapping

    def get_sonarr_library_paths(self) -> list[str]:
        return [p.strip() for p in self.SONARR_LIBRARY_PATHS.split(",") if p.strip()]

    def get_radarr_library_paths(self) -> list[str]:
        return [p.strip() for p in self.RADARR_LIBRARY_PATHS.split(",") if p.strip()]

    def get_library_paths(self) -> list[str]:
        return self.get_sonarr_library_paths() + self.get_radarr_library_paths()

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()

