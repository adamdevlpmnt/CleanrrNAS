from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.deletion import DeletionLog
from app.schemas.deletion import (
    DeletionPreviewRequest, DeletionPreviewResponse,
    DeletionExecuteRequest, DeletionExecuteResponse,
    DeletionLogResponse
)
from app.services.deleter import DeletionService
from app.services.qbittorrent import QBittorrentClient
from app.config import get_settings

router = APIRouter(prefix="/api/deletions", tags=["deletions"])
settings = get_settings()
deleter = DeletionService()

@router.post("/preview", response_model=DeletionPreviewResponse)
def preview_deletion(req: DeletionPreviewRequest, db: Session = Depends(get_db)):
    if not req.file_ids:
        raise HTTPException(status_code=400, detail="No file IDs provided")
    return deleter.preview_deletion(req.file_ids, db)

@router.post("/execute", response_model=DeletionExecuteResponse)
def execute_deletion(req: DeletionExecuteRequest, db: Session = Depends(get_db)):
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required")
    if not req.file_ids:
        raise HTTPException(status_code=400, detail="No file IDs provided")
        
    qbit = QBittorrentClient(settings.QBITTORRENT_URL, settings.QBITTORRENT_USERNAME, settings.QBITTORRENT_PASSWORD)
    return deleter.execute_deletion(req.file_ids, db, qbit)

@router.get("/history", response_model=List[DeletionLogResponse])
def deletion_history(limit: int = Query(50, ge=1), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    logs = db.query(DeletionLog).order_by(DeletionLog.deleted_at.desc()).offset(offset).limit(limit).all()
    return logs
