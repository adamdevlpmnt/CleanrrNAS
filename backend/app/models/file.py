from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, ForeignKey
from app.database import Base

class ScannedFile(Base):
    __tablename__ = "scanned_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_session_id = Column(Integer, ForeignKey("scan_sessions.id"))
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    inode = Column(BigInteger)
    device_id = Column(BigInteger)
    hardlink_count = Column(Integer, default=1)
    status = Column(String, nullable=False)
    status_reason = Column(Text)
    real_space_gain = Column(BigInteger, default=0)
    media_type = Column(String, nullable=True)
    media_title = Column(String, nullable=True)
    quality_info = Column(String, nullable=True)
    torrent_hash = Column(String, nullable=True)
    torrent_name = Column(String, nullable=True)
    completion_date = Column(DateTime, nullable=True)
    seeding_time_seconds = Column(Integer, nullable=True)
    hit_and_run_days = Column(Integer, nullable=True)
    linked_paths = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
