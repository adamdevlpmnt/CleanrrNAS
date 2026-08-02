from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

class ScannedFileResponse(BaseModel):
    id: int
    scan_session_id: int
    file_path: str
    file_name: str
    file_size: int
    inode: Optional[int]
    device_id: Optional[int]
    hardlink_count: int
    status: str
    status_reason: Optional[str]
    real_space_gain: int
    media_type: Optional[str]
    media_title: Optional[str]
    quality_info: Optional[str]
    torrent_hash: Optional[str]
    torrent_name: Optional[str]
    completion_date: Optional[datetime]
    seeding_time_seconds: Optional[int]
    linked_paths: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FileListSummary(BaseModel):
    total_count: int
    total_size: int
    total_reclaimable: int

class FileListResponse(BaseModel):
    items: List[ScannedFileResponse]
    total: int
    page: int
    page_size: int
    summary: FileListSummary
