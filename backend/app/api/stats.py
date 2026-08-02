from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.stats import DashboardStats, ConnectionStatus
from app.services.scanner import get_scanner_service
from app.services.sonarr import SonarrClient
from app.services.radarr import RadarrClient
from app.services.qbittorrent import QBittorrentClient
from app.config import get_settings

router = APIRouter(prefix="/api/stats", tags=["stats"])
settings = get_settings()

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    scanner = get_scanner_service()
    latest_scan = scanner.get_latest_scan() if scanner else None
    
    # Test connections
    sonarr = SonarrClient(settings.SONARR_URL, settings.SONARR_API_KEY)
    s_conn, s_ver = sonarr.test_connection()
    
    radarr = RadarrClient(settings.RADARR_URL, settings.RADARR_API_KEY)
    r_conn, r_ver = radarr.test_connection()
    
    qbit = QBittorrentClient(settings.QBITTORRENT_URL, settings.QBITTORRENT_USERNAME, settings.QBITTORRENT_PASSWORD)
    q_conn, _ = qbit.test_connection()
    
    conn_status = ConnectionStatus(
        sonarr_connected=s_conn,
        radarr_connected=r_conn,
        qbittorrent_connected=q_conn,
        sonarr_version=s_ver,
        radarr_version=r_ver
    )
    
    if latest_scan:
        return DashboardStats(
            total_downloads_size=latest_scan.total_size_scanned,
            reclaimable_size=latest_scan.reclaimable_size,
            protected_count=latest_scan.protected_count,
            orphan_count=latest_scan.orphan_count,
            last_scan_date=latest_scan.completed_at,
            connection_status=conn_status
        )
    else:
        return DashboardStats(
            total_downloads_size=0,
            reclaimable_size=0,
            protected_count=0,
            orphan_count=0,
            last_scan_date=None,
            connection_status=conn_status
        )
