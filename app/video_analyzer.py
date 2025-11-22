import os
import cv2
import time
from typing import Dict, Optional


def analyze_video(file_path: str, frame_skip: int = 10, motion_threshold: float = 0.01) -> Dict:
    if not os.path.exists(file_path):
        raise ValueError(f"Video file not found: {file_path}")
    
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {file_path}")
    
    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if total_frames == 0:
            raise ValueError("Video file is empty")
        
        if fps <= 0:
            raise ValueError("Invalid video FPS")
        
        bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,       
            varThreshold=50,    
            detectShadows=True 
        )
        
        frames_with_motion = 0
        frames_analyzed = 0
        frame_number = 0
        
        if total_frames > 1000:
            frame_skip = max(frame_skip, 20)
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            frame_number += 1
            if frame_number % frame_skip != 0:
                continue
            
            fg_mask = bg_subtractor.apply(frame)
            motion_pixels = cv2.countNonZero(fg_mask)
            total_pixels = frame.shape[0] * frame.shape[1]
            
            if total_pixels > 0:
                motion_ratio = motion_pixels / total_pixels
                if motion_ratio > motion_threshold:
                    frames_with_motion += 1
            
            frames_analyzed += 1
            
        if frames_analyzed > 0:
            motion_score = (frames_with_motion / frames_analyzed) * 100.0
        else:
            motion_score = 0.0
        
        has_motion = motion_score > 1.0
        
        return {
            "has_motion": has_motion,
            "motion_score": round(motion_score, 2),
            "frames_analyzed": frames_analyzed,
            "total_frames": total_frames
        }
    
    except Exception as e:
        raise ValueError(f"Error during video analysis: {str(e)}")
    
    finally:
        cap.release()


def analyze_video_with_timing(file_path: str, **kwargs) -> Dict:
    start_time = time.time()
    
    try:
        result = analyze_video(file_path, **kwargs)
        processing_time = time.time() - start_time
        result["processing_time"] = round(processing_time, 2)
        return result
    
    except Exception as e:
        processing_time = time.time() - start_time
        raise ValueError(f"{str(e)} (processing time: {round(processing_time, 2)}s)")

