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
    SONARR_LIBRARY_PATH: str = "/data/Series_4K"
    RADARR_LIBRARY_PATH: str = "/data/Film"
    DATABASE_URL: str = "sqlite:///config/mediacleaner.db"
    HIT_AND_RUN_DAYS: int = 7
    VIDEO_EXTENSIONS: str = ".mkv,.mp4,.avi,.ts,.wmv,.m4v,.mov,.flv,.webm"
    LOG_LEVEL: str = "INFO"
    APP_PORT: int = 9876

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
