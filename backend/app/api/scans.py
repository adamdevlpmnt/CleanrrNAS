from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.scan import ScanSession
from app.schemas.scan import ScanSessionResponse, ScanProgressResponse
from app.services.scanner import get_scanner_service

router = APIRouter(prefix="/api/scans", tags=["scans"])

@router.post("/", response_model=ScanSessionResponse)
def start_scan(db: Session = Depends(get_db)):
    scanner = get_scanner_service()
    if not scanner:
        raise HTTPException(status_code=500, detail="Scanner service not initialized")
        
    latest = scanner.get_latest_scan()
    # Check if a scan is running (by looking at progress)
    # Just a simple logic here
    session_id = scanner.start_scan()
    session = db.query(ScanSession).filter(ScanSession.id == session_id).first()
    return session

@router.get("/", response_model=List[ScanSessionResponse])
def list_scans(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    scans = db.query(ScanSession).order_by(ScanSession.started_at.desc()).offset(offset).limit(limit).all()
    return scans

@router.get("/latest", response_model=ScanSessionResponse)
def get_latest_scan(db: Session = Depends(get_db)):
    scanner = get_scanner_service()
    if not scanner:
        raise HTTPException(status_code=500, detail="Scanner service not initialized")
    scan = scanner.get_latest_scan()
    if not scan:
        raise HTTPException(status_code=404, detail="No completed scans found")
    return scan

@router.get("/{scan_id}", response_model=ScanSessionResponse)
def get_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(ScanSession).filter(ScanSession.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@router.get("/{scan_id}/progress", response_model=ScanProgressResponse)
def get_scan_progress(scan_id: int):
    scanner = get_scanner_service()
    if not scanner:
        raise HTTPException(status_code=500, detail="Scanner service not initialized")
    progress = scanner.get_progress(scan_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found for this scan")
    return progress
