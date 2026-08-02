from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text
from app.database import Base

class ScanSession(Base):
    __tablename__ = "scan_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String, default="pending")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_files_scanned = Column(Integer, default=0)
    orphan_count = Column(Integer, default=0)
    protected_count = Column(Integer, default=0)
    total_size_scanned = Column(BigInteger, default=0)
    reclaimable_size = Column(BigInteger, default=0)
    error_message = Column(Text, nullable=True)
