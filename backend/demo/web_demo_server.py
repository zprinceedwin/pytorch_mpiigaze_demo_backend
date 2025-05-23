from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse
import asyncio
import json
import cv2
import base64
import numpy as np
import sys
import os
import pathlib
import uvicorn
import time
import logging
from typing import Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add paths for imports
current_dir = pathlib.Path(__file__).parent.absolute()
project_root = current_dir.parent
demo_dir = project_root / "demo"

# Add to Python path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(demo_dir))

print(f"Current dir: {current_dir}")
print(f"Project root: {project_root}")
print(f"Demo dir: {demo_dir}")
print(f"Demo dir exists: {demo_dir.exists()}")

# Import your working demo
try:
    # Change to demo directory before importing
    original_cwd = os.getcwd()
    os.chdir(str(demo_dir))

    from gaze_behavior_demo import QuizSecureDemo
    from behavior_detector import BehaviorDetector

    # Change back
    os.chdir(original_cwd)

    print("✅ Successfully imported your ETH-XGaze demo!")
    IMPORTS_WORKING = True

except Exception as e:
    print(f"❌ Failed to import demo: {e}")
    print("Available files in demo directory:")
    if demo_dir.exists():
        for file in demo_dir.iterdir():
            print(f"  {file.name}")
    IMPORTS_WORKING = False
    QuizSecureDemo = None
    BehaviorDetector = None

app = FastAPI(title="QuizSecure ETH-XGaze Backend")

# Global variables
connected_clients: Set[WebSocket] = set()
demo_instance = None
demo_task = None


class WebETHXGazeDemo:
    def __init__(self):
        self.web_clients = set()
        self.is_running = False

        if IMPORTS_WORKING:
            try:
                # Change to demo directory for initialization
                original_cwd = os.getcwd()
                os.chdir(str(demo_dir))

                # Initialize your actual ETH-XGaze demo
                self.eth_xgaze_demo = QuizSecureDemo()
                print("✅ ETH-XGaze demo initialized!")

                # Change back
                os.chdir(original_cwd)

                self.has_eth_xgaze = True
            except Exception as e:
                print(f"❌ Failed to initialize ETH-XGaze: {e}")
                self.has_eth_xgaze = False
        else:
            self.has_eth_xgaze = False

        # Fallback camera for basic demo
        if not self.has_eth_xgaze:
            try:
                self.cap = cv2.VideoCapture(0)
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                print("✅ Fallback camera initialized")
            except Exception as e:
                print(f"❌ Fallback camera failed: {e}")
                self.cap = None

    async def broadcast_to_clients(self, data):
        """Broadcast data to all connected web clients"""
        print(f"🔍 DEBUG: broadcast_to_clients called, {len(self.web_clients)} clients")

        if not self.web_clients:
            print("🔍 DEBUG: No clients to broadcast to")
            return

        # Convert numpy types to Python types for JSON serialization
        def make_json_safe(obj):
            if isinstance(obj, dict):
                return {k: make_json_safe(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_safe(v) for v in obj]
            elif isinstance(obj, (np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, (np.int32, np.int64)):
                return int(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj

        # Make data JSON-safe
        safe_data = make_json_safe(data)

        disconnected = set()
        for client in self.web_clients:
            try:
                await client.send_text(json.dumps(safe_data))
                print(f"🔍 DEBUG: Sent data to client successfully")
            except Exception as e:
                print(f"🔍 DEBUG: Failed to send to client: {e}")
                disconnected.add(client)

        # Remove disconnected clients
        self.web_clients -= disconnected

    async def run_eth_xgaze_loop(self):
        """Run the actual ETH-XGaze processing loop"""
        print("🔍 DEBUG: run_eth_xgaze_loop called")

        if not self.has_eth_xgaze:
            print("🔍 DEBUG: No ETH-XGaze, running fallback")
            print("🔍 DEBUG: Available demo methods:")
            if hasattr(self, 'eth_xgaze_demo'):
                print(f"🔍 DEBUG: eth_xgaze_demo type: {type(self.eth_xgaze_demo)}")
                print(
                    f"🔍 DEBUG: eth_xgaze_demo methods: {[m for m in dir(self.eth_xgaze_demo) if not m.startswith('_')]}")

                if hasattr(self.eth_xgaze_demo, 'behavior_detector'):
                    print(f"🔍 DEBUG: behavior_detector available: {type(self.eth_xgaze_demo.behavior_detector)}")
                else:
                    print("🔍 DEBUG: No behavior_detector found")
            await self.run_fallback_loop()
            return

        try:
            # Change to demo directory
            original_cwd = os.getcwd()
            os.chdir(str(demo_dir))
            print("🔍 DEBUG: Changed to demo directory")

            # Try to get camera
            cap = None

            if hasattr(self.eth_xgaze_demo, 'cap') and self.eth_xgaze_demo.cap:
                cap = self.eth_xgaze_demo.cap
                print("🔍 DEBUG: Using ETH-XGaze demo camera")
            else:
                print("🔍 DEBUG: Initializing new camera...")
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    print("🔍 DEBUG: New camera initialized successfully")
                else:
                    print("🔍 DEBUG: Failed to open camera")

            if not cap or not cap.isOpened():
                print("🔍 DEBUG: No camera available - running simulation")
                await self.run_no_camera_loop()
                return

            print("🔍 DEBUG: Starting processing loop...")
            self.is_running = True
            frame_count = 0

            while self.is_running:
                frame_count += 1
                if frame_count % 30 == 0:  # Print every 30 frames
                    print(f"🔍 DEBUG: Processing frame {frame_count}")

                # Read frame
                ret, frame = cap.read()
                if not ret:
                    print("🔍 DEBUG: Failed to read frame")
                    await asyncio.sleep(0.1)
                    continue

                # USE ACTUAL ETH-XGAZE PROCESSING HERE
                try:
                    if hasattr(self.eth_xgaze_demo, 'process_with_ptgaze'):
                        print("🔍 DEBUG: Using real ETH-XGaze processing")
                        processed_frame, behavior_status = self.eth_xgaze_demo.process_with_ptgaze(frame)

                        # Get real behavior data
                        if hasattr(self.eth_xgaze_demo, 'behavior_detector'):
                            # The behavior detector should already be updated by process_with_ptgaze
                            behavior_data = {
                                'state': self.eth_xgaze_demo.behavior_detector.current_state,
                                'alert_count': self.eth_xgaze_demo.behavior_detector.alert_count,
                                'focus_percentage': 100 * (
                                            1 - self.eth_xgaze_demo.behavior_detector.total_distraction_time /
                                            max(1, time.time() - self.eth_xgaze_demo.behavior_detector.session_start)),
                                'session_duration': time.time() - self.eth_xgaze_demo.behavior_detector.session_start,
                                'looking_at_screen': True  # You can get this from your behavior detector
                            }

                            # Get real gaze data if available
                            gaze_data = {'pitch': 0.0, 'yaw': 0.0}
                            if 'current_gaze' in behavior_status:
                                gaze_data = behavior_status['current_gaze']

                            print(
                                f"🔍 DEBUG: Real behavior state: {behavior_data['state']}, alerts: {behavior_data['alert_count']}")

                        else:
                            behavior_data = {
                                'state': 'NO_BEHAVIOR_DETECTOR',
                                'alert_count': 0,
                                'focus_percentage': 100,
                                'session_duration': frame_count,
                                'looking_at_screen': True
                            }
                            gaze_data = {'pitch': 0.0, 'yaw': 0.0}

                    else:
                        print("🔍 DEBUG: No process_with_ptgaze method, using basic processing")
                        processed_frame = frame.copy()
                        cv2.putText(processed_frame, f"No ETH-XGaze Processing", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                        behavior_data = {
                            'state': 'NO_PROCESSING',
                            'alert_count': 0,
                            'focus_percentage': 100,
                            'session_duration': frame_count,
                            'looking_at_screen': True
                        }
                        gaze_data = {'pitch': 0.0, 'yaw': 0.0}

                except Exception as e:
                    print(f"🔍 DEBUG: Processing error: {e}")
                    processed_frame = frame.copy()
                    behavior_data = {
                        'state': 'ERROR',
                        'alert_count': 0,
                        'focus_percentage': 100,
                        'session_duration': frame_count,
                        'looking_at_screen': True
                    }
                    gaze_data = {'pitch': 0.0, 'yaw': 0.0}

                # Convert to base64
                _, buffer = cv2.imencode('.jpg', processed_frame)
                frame_base64 = base64.b64encode(buffer).decode('utf-8')

                # Real web data with actual behavior
                web_data = {
                    'type': 'gaze_update',
                    'frame': frame_base64,
                    'status': behavior_data['state'],
                    'alerts': behavior_data['alert_count'],
                    'focus': round(behavior_data['focus_percentage'], 1),
                    'session_time': int(behavior_data['session_duration']),
                    'gaze': gaze_data,
                    'looking_at_screen': behavior_data['looking_at_screen'],
                    'system': 'ETH-XGaze-Real'
                }

                # Debug broadcast
                if frame_count % 30 == 0:
                    print(
                        f"🔍 DEBUG: Status: {web_data['status']}, Focus: {web_data['focus']}%, Alerts: {web_data['alerts']}")

                # Broadcast to clients
                await self.broadcast_to_clients(web_data)

                # Control frame rate
                await asyncio.sleep(0.033)  # 30 FPS

        except Exception as e:
            print(f"🔍 DEBUG: Exception in ETH-XGaze loop: {e}")
            import traceback
            traceback.print_exc()

    async def run_fallback_loop(self):
        """Fallback demo loop"""
        print("🔄 Running fallback demo...")

        if not hasattr(self, 'cap') or self.cap is None:
            # No camera available
            await self.run_no_camera_loop()
            return

        self.is_running = True

        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    await asyncio.sleep(0.1)
                    continue

                # Basic face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

                # Draw faces
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # Simulate gaze
                    center = (x + w // 2, y + h // 2)
                    end_x = center[0] + int(30 * np.sin(time.time() * 0.5))
                    end_y = center[1] + int(20 * np.cos(time.time() * 0.3))
                    cv2.arrowedLine(frame, center, (end_x, end_y), (255, 255, 0), 2)

                # Add status text
                cv2.putText(frame, "Fallback Demo - Basic Face Detection", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                # Convert to base64
                _, buffer = cv2.imencode('.jpg', frame)
                frame_base64 = base64.b64encode(buffer).decode('utf-8')

                # Simple behavior data
                web_data = {
                    'type': 'gaze_update',
                    'frame': frame_base64,
                    'status': 'FOCUSED' if len(faces) > 0 else 'NO_FACE',
                    'alerts': 0,
                    'focus': 100.0 if len(faces) > 0 else 50.0,
                    'session_time': int(time.time() % 3600),
                    'gaze': {'pitch': 0.1 * np.sin(time.time()), 'yaw': 0.1 * np.cos(time.time())},
                    'looking_at_screen': len(faces) > 0,
                    'system': 'Fallback'
                }

                await self.broadcast_to_clients(web_data)
                await asyncio.sleep(0.1)

            except Exception as e:
                print(f"❌ Fallback loop error: {e}")
                await asyncio.sleep(1)

    async def run_no_camera_loop(self):
        """Demo without camera"""
        print("📷 No camera - running simulation...")
        self.is_running = True

        while self.is_running:
            # Create black frame with text
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "QuizSecure ETH-XGaze Demo", (150, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, "Camera not available", (200, 250),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.putText(frame, f"System: {'ETH-XGaze' if self.has_eth_xgaze else 'Fallback'}", (220, 300),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Convert to base64
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')

            # Simulate data
            web_data = {
                'type': 'gaze_update',
                'frame': frame_base64,
                'status': 'SIMULATED',
                'alerts': 0,
                'focus': 85.0,
                'session_time': int(time.time() % 3600),
                'gaze': {'pitch': 0.05 * np.sin(time.time()), 'yaw': 0.05 * np.cos(time.time())},
                'looking_at_screen': True,
                'system': 'Simulation'
            }

            await self.broadcast_to_clients(web_data)
            await asyncio.sleep(0.2)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global demo_instance, demo_task

    await websocket.accept()
    connected_clients.add(websocket)

    # Initialize demo if needed
    if demo_instance is None:
        print("🚀 Initializing WebETHXGazeDemo...")
        demo_instance = WebETHXGazeDemo()

    demo_instance.web_clients.add(websocket)

    # Start demo task if not running
    if demo_task is None or demo_task.done():
        print("🚀 Starting demo task...")
        demo_task = asyncio.create_task(demo_instance.run_eth_xgaze_loop())

    try:
        while True:
            # Handle client messages
            message = await websocket.receive_text()
            data = json.loads(message)

            if data.get('action') == 'reset_session':
                if demo_instance.has_eth_xgaze:
                    demo_instance.eth_xgaze_demo.behavior_detector.reset_session()

                await websocket.send_text(json.dumps({
                    'type': 'session_reset',
                    'message': 'Session reset'
                }))

    except WebSocketDisconnect:
        connected_clients.discard(websocket)
        if demo_instance:
            demo_instance.web_clients.discard(websocket)
        print(f"Client disconnected. Remaining: {len(connected_clients)}")


@app.get("/")
async def root():
    return {"message": "QuizSecure ETH-XGaze Backend", "eth_xgaze_available": IMPORTS_WORKING}


@app.get("/status")
async def get_status():
    return {
        "status": "running",
        "eth_xgaze_available": IMPORTS_WORKING,
        "connected_clients": len(connected_clients),
        "demo_active": demo_instance is not None
    }


@app.get("/student")
async def student_page():
    html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>QuizSecure Student</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white">
    <div class="container mx-auto p-4">
        <h1 class="text-3xl font-bold mb-6">QuizSecure - ETH-XGaze Student Interface</h1>

        <div class="grid grid-cols-3 gap-6">
            <div class="col-span-2">
                <div class="bg-gray-800 rounded-lg p-4">
                    <h2 class="text-xl font-bold mb-4">Live Camera Feed</h2>
                    <img id="cameraFeed" class="w-full rounded-lg" alt="Camera Feed" style="min-height: 400px; background: #374151;">
                </div>
            </div>

            <div class="bg-gray-800 rounded-lg p-6">
                <h2 class="text-xl font-bold mb-4">System Status</h2>

                <div class="mb-4">
                    <div class="text-sm text-gray-400">Current Status</div>
                    <div id="status" class="text-2xl font-bold text-green-400">INITIALIZING</div>
                </div>

                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span>Alerts:</span>
                        <span id="alerts" class="font-bold">0</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Focus:</span>
                        <span id="focus" class="font-bold">100%</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Time:</span>
                        <span id="time" class="font-bold">00:00</span>
                    </div>
                    <div class="flex justify-between">
                        <span>System:</span>
                        <span id="system" class="font-bold text-blue-400">Loading...</span>
                    </div>
                </div>

                <div class="mt-6">
                    <div class="text-sm text-gray-400 mb-2">Gaze Data</div>
                    <div class="text-xs space-y-1">
                        <div>Pitch: <span id="gazePitch">0.000</span></div>
                        <div>Yaw: <span id="gazeYaw">0.000</span></div>
                    </div>
                </div>

                <button id="resetBtn" class="w-full mt-6 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg">
                    Reset Session
                </button>
            </div>
        </div>
    </div>

    <script>
        const ws = new WebSocket('ws://localhost:8000/ws');

        ws.onopen = function() {
            console.log('Connected to QuizSecure backend');
        };

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);

            if (data.type === 'gaze_update') {
                document.getElementById('cameraFeed').src = 'data:image/jpeg;base64,' + data.frame;
                document.getElementById('status').textContent = data.status;
                document.getElementById('alerts').textContent = data.alerts;
                document.getElementById('focus').textContent = data.focus.toFixed(1) + '%';
                document.getElementById('system').textContent = data.system;

                if (data.gaze) {
                    document.getElementById('gazePitch').textContent = data.gaze.pitch.toFixed(3);
                    document.getElementById('gazeYaw').textContent = data.gaze.yaw.toFixed(3);
                }

                const minutes = Math.floor(data.session_time / 60);
                const seconds = data.session_time % 60;
                document.getElementById('time').textContent = 
                    String(minutes).padStart(2, '0') + ':' + String(seconds).padStart(2, '0');
            }
        };

        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };

        document.getElementById('resetBtn').onclick = function() {
            ws.send(JSON.stringify({action: 'reset_session'}));
        };
    </script>
</body>
</html>
'''
    return HTMLResponse(html_content)


if __name__ == "__main__":
    print("🚀 Starting QuizSecure ETH-XGaze Backend Server")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Demo directory: {demo_dir}")
    print(f"✅ ETH-XGaze available: {IMPORTS_WORKING}")
    print("🌐 Server will be available at: http://localhost:8000")
    print("👤 Student interface: http://localhost:8000/student")

    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        print("Try running the test_server.py first to check basic FastAPI setup")