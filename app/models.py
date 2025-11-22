from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AnalysisVideo(BaseModel):
    id: int
    filename: str
    has_motion: bool
    motion_score: Optional[float] = None
    processing_time: Optional[float] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    has_motion: bool
    motion_score: Optional[float] = None
