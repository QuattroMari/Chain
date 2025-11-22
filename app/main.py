import os
import shutil
import uuid
import tempfile
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.database import get_db, engine, Base
from app.schema import Video
from app.models import AnalysisVideo
from app.video_analyzer import analyze_video_with_timing
from contextlib import asynccontextmanager

TEMP_UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "video_uploads")
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 мб


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="Video Analysis Service",
    description="Тестовый микросервис для анализа видео",
    version="1.0.0",
    lifespan=lifespan
)

video_analysis_total = Counter(
    'video_analysis_total',
    'Total number of videos analyzed'
)

video_analysis_processing_time_seconds = Histogram(
    'video_analysis_processing_time_seconds',
    'Time spent processing videos',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)
 
video_analysis_errors_total = Counter(
    'video_analysis_errors_total',
    'Total number of errors during video analysis'
)

video_analysis_motion_detected_total = Counter(
    'video_analysis_motion_detected_total',
    'Total number of videos with detected motion'
)


def validate_video_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid content type"
        )


@app.post("/analyze", response_model=AnalysisVideo, status_code=200)
async def analyze_video_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = None
    video_id = None
    
    try:
        validate_video_file(file)
        
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(TEMP_UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)} MB"
            )
        
        video_record = Video(
            filename=file.filename,
            has_motion=False,
            status="processing",
            created_at=datetime.now(timezone.utc)
        )
        
        try:
            db.add(video_record)
            db.commit()
            db.refresh(video_record)
            video_id = video_record.id
        except Exception as e:
            db.rollback()
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        try:
            result = analyze_video_with_timing(file_path)
            video_record.has_motion = result["has_motion"]
            video_record.motion_score = result.get("motion_score")
            video_record.processing_time = result.get("processing_time")
            video_record.status = "completed"
            
            db.commit()
            db.refresh(video_record)
            
            video_analysis_total.inc()
            if result.get("processing_time"):
                video_analysis_processing_time_seconds.observe(result["processing_time"])
            
            if result["has_motion"]:
                video_analysis_motion_detected_total.inc()
            
        except ValueError as e:
            video_analysis_errors_total.inc()
            
            if video_id:
                video_record = db.query(Video).filter(Video.id == video_id).first()
                if video_record:
                    video_record.status = "failed"
                    db.commit()
            
            raise HTTPException(status_code=400, detail=str(e))
        
        return AnalysisVideo.model_validate(video_record)
    
    except HTTPException:
        raise
    
    except Exception as e:
        video_analysis_errors_total.inc()

        if video_id:
            try:
                video_record = db.query(Video).filter(Video.id == video_id).first()
                if video_record:
                    video_record.status = "failed"
                    db.commit()
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


@app.get("/metrics")
async def get_metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    video_analysis_errors_total.inc()
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    video_analysis_errors_total.inc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
