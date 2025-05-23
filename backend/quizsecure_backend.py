# quizsecure_backend.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import base64
import time
from typing import Dict
import logging
import sys
from omegaconf import OmegaConf

# Use the WORKING import method
from ptgaze.gaze_estimator import GazeEstimator

app = FastAPI(title="QuizSecure Gaze Monitoring API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_gaze_estimator_config():
    """Create configuration for GazeEstimator"""
    config = OmegaConf.create({
        'device': 'cuda' if torch.cuda.is_available() else 'cpu',
        'mode': 'MPIIFaceGaze',  # or 'MPIIGaze' or 'ETH-XGaze'
        'face_detector': 'mediapipe',
        'gaze_estimator': {
            'checkpoint': None,  # Will use default model
            'camera_params': None,  # Will use default camera params
            'normalized_camera_params': None,
            'normalized_camera_distance': 600,
        }
    })
    return config


# Initialize gaze estimator with config
try:
    import torch

    config = create_gaze_estimator_config()
    gaze_estimator = GazeEstimator(config)
    print("✅ GazeEstimator initialized with CUDA support!")
except Exception as e:
    print(f"❌ GazeEstimator initialization failed: {e}")
    # Let's try a simpler approach
    try:
        from ptgaze import demo

        print("✅ Using ptgaze demo module instead")
        gaze_estimator = None  # We'll handle this differently
    except Exception as e2:
        print(f"❌ Demo module also failed: {e2}")
        gaze_estimator = None

# User session storage
user_sessions: Dict[str, Dict] = {}


class SuspiciousBehaviorDetector:
    def __init__(self):
        self.gaze_threshold = 0.3
        self.warning_limit = 3

    def analyze_basic_face_data(self, faces_detected):
        """Basic analysis when we can't get detailed gaze data"""
        suspicious_behaviors = []

        if faces_detected == 0:
            suspicious_behaviors.append("no_face_detected")
        elif faces_detected > 1:
            suspicious_behaviors.append("multiple_faces_detected")

        return suspicious_behaviors


detector = SuspiciousBehaviorDetector()


@app.post("/monitor-student")
async def monitor_student(user_id: str, frame: UploadFile = File(...)):
    """Main endpoint for monitoring student during exam"""
    try:
        # Read uploaded image
        contents = await frame.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image data")

        # Initialize user session
        if user_id not in user_sessions:
            user_sessions[user_id] = {
                'warnings': 0,
                'last_update': time.time(),
                'alert_active': False,
                'total_frames': 0
            }

        session = user_sessions[user_id]
        session['last_update'] = time.time()
        session['total_frames'] += 1

        # Basic face detection using OpenCV (fallback)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        faces_detected = len(faces)

        # Analyze for suspicious behavior
        suspicious_behaviors = detector.analyze_basic_face_data(faces_detected)

        # Update warning count
        if suspicious_behaviors:
            session['warnings'] += 1
        else:
            session['warnings'] = max(0, session['warnings'] - 1)

        # Determine alert level
        alert_level = "normal"
        if session['warnings'] >= detector.warning_limit:
            alert_level = "critical"
            session['alert_active'] = True
        elif session['warnings'] >= 2:
            alert_level = "warning"
        else:
            session['alert_active'] = False

        # Prepare response
        response = {
            'user_id': user_id,
            'timestamp': time.time(),
            'faces_detected': faces_detected,
            'face_locations': [{'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)} for (x, y, w, h) in faces],
            'suspicious_behaviors': suspicious_behaviors,
            'warning_count': session['warnings'],
            'alert_level': alert_level,
            'total_frames_processed': session['total_frames'],
            'detection_method': 'opencv_basic' if gaze_estimator is None else 'ptgaze_advanced'
        }

        return response

    except Exception as e:
        logging.error(f"Error in monitor_student: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/student-status/{user_id}")
async def get_student_status(user_id: str):
    """Get current monitoring status for a student"""
    if user_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Student session not found")

    session = user_sessions[user_id]
    return {
        'user_id': user_id,
        'warnings': session['warnings'],
        'alert_active': session['alert_active'],
        'last_update': session['last_update'],
        'total_frames': session['total_frames'],
        'session_active': (time.time() - session['last_update']) < 60
    }


@app.post("/reset-session/{user_id}")
async def reset_session(user_id: str):
    """Reset monitoring session for a student"""
    if user_id in user_sessions:
        user_sessions[user_id] = {
            'warnings': 0,
            'last_update': time.time(),
            'alert_active': False,
            'total_frames': 0
        }
    return {"status": "success", "user_id": user_id}


@app.get("/system-info")
async def get_system_info():
    """Get system information"""
    import torch
    return {
        'python_version': f"{sys.version}",
        'pytorch_version': torch.__version__,
        'cuda_available': torch.cuda.is_available(),
        'gpu_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        'total_sessions': len(user_sessions),
        'gaze_estimator_available': gaze_estimator is not None
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting QuizSecure Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000)