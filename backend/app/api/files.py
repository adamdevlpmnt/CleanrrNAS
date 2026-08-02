from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.database import get_db
from app.models.file import ScannedFile
from app.schemas.file import ScannedFileResponse, FileListResponse, FileListSummary
from app.services.scanner import get_scanner_service

router = APIRouter(prefix="/api/files", tags=["files"])

@router.get("/", response_model=FileListResponse)
def list_files(
    status: Optional[str] = None,
    media_type: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "file_size",
    sort_dir: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    scanner = get_scanner_service()
    latest_scan = scanner.get_latest_scan() if scanner else None
    scan_id = latest_scan.id if latest_scan else None
    
    if not scan_id:
        return FileListResponse(
            items=[], total=0, page=page, page_size=page_size,
            summary=FileListSummary(total_count=0, total_size=0, total_reclaimable=0)
        )

    query = db.query(ScannedFile).filter(ScannedFile.scan_session_id == scan_id)
    
    if status:
        query = query.filter(ScannedFile.status == status)
    if media_type:
        query = query.filter(ScannedFile.media_type == media_type)
    if search:
        query = query.filter(ScannedFile.file_name.ilike(f"%{search}%"))
        
    # Stats before pagination
    total_count = query.count()
    
    total_size = db.query(func.sum(ScannedFile.file_size)).filter(ScannedFile.scan_session_id == scan_id)
    if status: total_size = total_size.filter(ScannedFile.status == status)
    if media_type: total_size = total_size.filter(ScannedFile.media_type == media_type)
    if search: total_size = total_size.filter(ScannedFile.file_name.ilike(f"%{search}%"))
    ts_val = total_size.scalar() or 0
    
    total_rec = db.query(func.sum(ScannedFile.real_space_gain)).filter(ScannedFile.scan_session_id == scan_id)
    if status: total_rec = total_rec.filter(ScannedFile.status == status)
    if media_type: total_rec = total_rec.filter(ScannedFile.media_type == media_type)
    if search: total_rec = total_rec.filter(ScannedFile.file_name.ilike(f"%{search}%"))
    tr_val = total_rec.scalar() or 0
    
    summary = FileListSummary(total_count=total_count, total_size=ts_val, total_reclaimable=tr_val)
    
    # Sorting
    if hasattr(ScannedFile, sort_by):
        col = getattr(ScannedFile, sort_by)
        if sort_dir == "desc":
            col = col.desc()
        query = query.order_by(col)
        
    # Pagination
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    return FileListResponse(
        items=items,
        total=total_count,
        page=page,
        page_size=page_size,
        summary=summary
    )

@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    scanner = get_scanner_service()
    latest_scan = scanner.get_latest_scan() if scanner else None
    if not latest_scan:
        return {}
        
    stats = db.query(ScannedFile.status, func.count(ScannedFile.id), func.sum(ScannedFile.file_size)).filter(ScannedFile.scan_session_id == latest_scan.id).group_by(ScannedFile.status).all()
    
    res = {}
    for s in stats:
        res[s[0]] = {"count": s[1], "size": s[2]}
    return res

@router.get("/all-deletable-ids")
def get_all_deletable_ids(search: Optional[str] = None, db: Session = Depends(get_db)):
    scanner = get_scanner_service()
    latest_scan = scanner.get_latest_scan() if scanner else None
    if not latest_scan:
        return {"ids": [], "count": 0}
    
    query = db.query(ScannedFile.id).filter(
        ScannedFile.scan_session_id == latest_scan.id,
        ScannedFile.status == "ORPHAN_SAFE"
    )
    if search:
        query = query.filter(ScannedFile.file_name.ilike(f"%{search}%"))
    
    ids = [row[0] for row in query.all()]
    return {"ids": ids, "count": len(ids)}

@router.get("/{file_id}", response_model=ScannedFileResponse)
def get_file(file_id: int, db: Session = Depends(get_db)):
    f = db.query(ScannedFile).filter(ScannedFile.id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    return f
