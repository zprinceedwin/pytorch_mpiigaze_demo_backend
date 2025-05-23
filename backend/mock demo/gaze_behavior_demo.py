import cv2
import numpy as np
import time
import logging
import sys
import os
from omegaconf import OmegaConf
import pathlib

# Add the parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ptgaze.demo import Demo
from ptgaze.main import load_mode_config
from ptgaze.utils import expanduser_all, download_ethxgaze_model, check_path_all
from behavior_detector import BehaviorDetector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuizSecureDemo:
    def __init__(self):
        self.setup_ptgaze_demo()
        self.behavior_detector = BehaviorDetector()
        self.running = False

    def setup_ptgaze_demo(self):
        """Use the exact same setup as the working ptgaze command"""
        try:
            # Create fake args object like ptgaze command line
            class Args:
                mode = 'eth-xgaze'
                device = 'cuda'
                face_detector = 'mediapipe'
                image = None
                video = None
                camera = None
                output_dir = None
                ext = None
                no_screen = True  # Don't show ptgaze's own display
                debug = False

            args = Args()

            # Use the exact same config loading as ptgaze main
            config = load_mode_config(args)
            expanduser_all(config)

            # Download model if needed (same as ptgaze main)
            download_ethxgaze_model()

            # Check paths (same as ptgaze main)
            check_path_all(config)

            # Create the working Demo object
            self.ptgaze_demo = Demo(config)

            logger.info("✅ ETH-XGaze demo initialized successfully using actual ptgaze system")

        except Exception as e:
            logger.error(f"❌ Failed to initialize ptgaze demo: {e}")
            raise

    def run_demo(self):
        """Main demo loop using actual ptgaze processing"""
        logger.info("🚀 Starting QuizSecure with Actual ETH-XGaze")
        logger.info("Press 'q' to quit, 'r' to reset session")

        try:
            # Use ptgaze's camera setup
            cap = self.ptgaze_demo.cap
            if not cap or not cap.isOpened():
                raise RuntimeError("Cannot open camera")

            self.running = True

            while self.running:
                # Use ptgaze's frame reading
                ok, frame = cap.read()
                if not ok:
                    break

                # Process with actual ptgaze system
                processed_frame, gaze_data = self.process_with_ptgaze(frame)

                # Show the result
                cv2.imshow('QuizSecure - Real ETH-XGaze Demo', processed_frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.running = False
                elif key == ord('r'):
                    self.behavior_detector.reset_session()
                    logger.info("Session reset")

        except Exception as e:
            logger.error(f"Demo error: {e}")
        finally:
            self.cleanup()

    def process_with_ptgaze(self, frame):
        """Process frame using actual ptgaze system"""
        try:
            # Use ptgaze's actual processing pipeline
            undistorted = cv2.undistort(
                frame,
                self.ptgaze_demo.gaze_estimator.camera.camera_matrix,
                self.ptgaze_demo.gaze_estimator.camera.dist_coefficients
            )

            # Set the frame for ptgaze visualizer
            self.ptgaze_demo.visualizer.set_image(frame.copy())

            # Detect faces using ptgaze
            faces = self.ptgaze_demo.gaze_estimator.detect_faces(undistorted)

            gaze_pitch, gaze_yaw = 0.0, 0.0  # Default values

            if faces:
                face = faces[0]  # Use first face

                # Estimate gaze using actual ETH-XGaze
                self.ptgaze_demo.gaze_estimator.estimate_gaze(undistorted, face)

                # Get the actual gaze angles
                if hasattr(face, 'normalized_gaze_angles') and face.normalized_gaze_angles is not None:
                    gaze_pitch, gaze_yaw = face.normalized_gaze_angles

                    # Update behavior detection with real gaze data
                    behavior_status = self.behavior_detector.update_behavior(gaze_pitch, gaze_yaw)
                else:
                    behavior_status = {"state": "NO_GAZE", "alert_count": 0}

                # Draw ptgaze visualizations
                self.ptgaze_demo._draw_face_bbox(face)
                self.ptgaze_demo._draw_gaze_vector(face)

            else:
                behavior_status = {"state": "NO_FACE", "alert_count": 0}

            # Get the processed frame from ptgaze
            result_frame = self.ptgaze_demo.visualizer.image

            # Add our behavior overlay
            result_frame = self.add_behavior_overlay(result_frame, behavior_status, gaze_pitch, gaze_yaw)

            return result_frame, behavior_status

        except Exception as e:
            logger.error(f"Processing error: {e}")
            return frame, {"state": "ERROR", "alert_count": 0}

    def add_behavior_overlay(self, frame, behavior_status, gaze_pitch, gaze_yaw):
        """Add behavior detection overlay to ptgaze frame"""

        # Status overlay background
        cv2.rectangle(frame, (10, 10), (500, 120), (0, 0, 0), -1)

        # Get status color
        status_color = self.behavior_detector.get_status_color()
        state = behavior_status.get('state', 'UNKNOWN')

        # Status information
        cv2.putText(frame, f"QuizSecure Status: {state}", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        cv2.putText(frame, f"Alerts: {behavior_status.get('alert_count', 0)}", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.putText(frame, f"Focus: {behavior_status.get('focus_percentage', 0):.1f}%", (20, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.putText(frame, f"ETH-XGaze: P={gaze_pitch:.3f} Y={gaze_yaw:.3f}", (20, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Controls
        cv2.putText(frame, "Press 'q' to quit, 'r' to reset", (20, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        return frame

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'ptgaze_demo') and self.ptgaze_demo.cap:
            self.ptgaze_demo.cap.release()
        cv2.destroyAllWindows()
        logger.info("Demo cleanup completed")


if __name__ == "__main__":
    try:
        demo = QuizSecureDemo()
        demo.run_demo()
    except Exception as e:
        logger.error(f"Failed to start demo: {e}")
        print(f"\n❌ Demo failed: {e}")
        print("\nMake sure your ETH-XGaze is working: ptgaze --mode eth-xgaze --device cuda")