from fastapi import APIRouter
from app.config import get_settings
from app.schemas.stats import ConnectionStatus
from app.services.sonarr import SonarrClient
from app.services.radarr import RadarrClient
from app.services.qbittorrent import QBittorrentClient

router = APIRouter(prefix="/api/health", tags=["health"])
settings = get_settings()

@router.get("/")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@router.get("/connections", response_model=ConnectionStatus)
def test_connections():
    sonarr = SonarrClient(settings.SONARR_URL, settings.SONARR_API_KEY)
    s_conn, s_ver = sonarr.test_connection()
    
    radarr = RadarrClient(settings.RADARR_URL, settings.RADARR_API_KEY)
    r_conn, r_ver = radarr.test_connection()
    
    qbit = QBittorrentClient(settings.QBITTORRENT_URL, settings.QBITTORRENT_USERNAME, settings.QBITTORRENT_PASSWORD)
    q_conn, _ = qbit.test_connection()
    
    return ConnectionStatus(
        sonarr_connected=s_conn,
        radarr_connected=r_conn,
        qbittorrent_connected=q_conn,
        sonarr_version=s_ver,
        radarr_version=r_ver
    )
