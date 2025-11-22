from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from datetime import datetime, timezone
from app.database import Base

class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    has_motion = Column(Boolean, nullable=False)
    motion_score = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)
    status = Column(String(50), default='completed', nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)