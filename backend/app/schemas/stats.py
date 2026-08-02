from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ConnectionStatus(BaseModel):
    sonarr_connected: bool
    radarr_connected: bool
    qbittorrent_connected: bool
    sonarr_version: Optional[str] = None
    radarr_version: Optional[str] = None

class DashboardStats(BaseModel):
    total_downloads_size: int
    reclaimable_size: int
    protected_count: int
    orphan_count: int
    last_scan_date: Optional[datetime]
    connection_status: ConnectionStatus
