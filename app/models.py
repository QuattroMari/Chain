from pydantic import BaseModel
from typing import List, Optional, Float
from datetime import datetime
import uuid

class AnalysisVideo(BaseModel):
    id: int
    filename: str
    has_motion: bool
    motion_score: Optional[Float] = None
    processing_time: Optional[Float] = None
    status: str
    created_at: datetime

    class config:
        from_attributes = True

class AnalysisResult(BaseModel):
    has_motion: bool
    motion_score: Optional[Float] = None
