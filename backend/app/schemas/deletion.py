from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from .file import ScannedFileResponse

class DeletionPreviewRequest(BaseModel):
    file_ids: List[int]

class DeletionPreviewResponse(BaseModel):
    files: List[ScannedFileResponse]
    total_size: int
    real_gain: int
    warnings: List[str]

class DeletionExecuteRequest(BaseModel):
    file_ids: List[int]
    confirm: bool = True

class DeletionExecuteResponse(BaseModel):
    deleted_count: int
    space_freed: int
    errors: List[str]

class DeletionLogResponse(BaseModel):
    id: int
    file_path: str
    file_name: str
    file_size: Optional[int]
    real_space_freed: Optional[int]
    status_at_deletion: Optional[str]
    reason: Optional[str]
    deleted_at: datetime
    scan_session_id: Optional[int]
    torrent_hash: Optional[str]
    torrent_removed: bool

    model_config = ConfigDict(from_attributes=True)
