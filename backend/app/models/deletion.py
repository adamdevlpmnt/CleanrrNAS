from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, Boolean, ForeignKey
from app.database import Base

class DeletionLog(Base):
    __tablename__ = "deletion_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(BigInteger)
    real_space_freed = Column(BigInteger)
    status_at_deletion = Column(String)
    reason = Column(Text)
    deleted_at = Column(DateTime, default=datetime.utcnow)
    scan_session_id = Column(Integer, ForeignKey("scan_sessions.id"), nullable=True)
    torrent_hash = Column(String, nullable=True)
    torrent_removed = Column(Boolean, default=False)
