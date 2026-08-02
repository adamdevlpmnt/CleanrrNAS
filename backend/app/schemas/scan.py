from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class ScanSessionCreate(BaseModel):
    pass

class ScanSessionResponse(BaseModel):
    id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    total_files_scanned: int
    orphan_count: int
    protected_count: int
    total_size_scanned: int
    reclaimable_size: int
    error_message: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class ScanProgressResponse(BaseModel):
    scan_id: int
    status: str
    progress_percent: float
    files_scanned: int
    current_file: Optional[str]
