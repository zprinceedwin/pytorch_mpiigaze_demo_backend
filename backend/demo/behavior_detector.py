import time
import numpy as np
from typing import Tuple, Optional
import logging


class BehaviorDetector:
    def __init__(self):
        # Screen boundaries for "looking at screen" detection
        # Adjust these based on your setup
        self.screen_bounds = {
            "x_min": -0.4,  # Left boundary
            "x_max": 0.4,  # Right boundary
            "y_min": -0.3,  # Top boundary
            "y_max": 0.3  # Bottom boundary
        }

        # Behavior tracking
        self.looking_away_start = None
        self.total_distraction_time = 0.0
        self.alert_count = 0
        self.session_start = time.time()
        self.behavior_log = []

        # Thresholds
        self.distraction_threshold = 2.0  # seconds
        self.critical_threshold = 4.0  # seconds

        # State tracking
        self.current_state = "INITIALIZING"
        self.last_alert_time = 0

        logging.info("BehaviorDetector initialized")

    def is_looking_at_screen(self, gaze_pitch: float, gaze_yaw: float) -> bool:
        """
        Determine if gaze is within screen boundaries
        gaze_pitch: vertical gaze angle (radians)
        gaze_yaw: horizontal gaze angle (radians)
        """
        return (self.screen_bounds["x_min"] <= gaze_yaw <= self.screen_bounds["x_max"] and
                self.screen_bounds["y_min"] <= gaze_pitch <= self.screen_bounds["y_max"])

    def update_behavior(self, gaze_pitch: float, gaze_yaw: float) -> dict:
        """
        Update behavior state based on current gaze
        Returns status dictionary with current state and metrics
        """
        current_time = time.time()
        looking_at_screen = self.is_looking_at_screen(gaze_pitch, gaze_yaw)

        if looking_at_screen:
            # Student is looking at screen
            if self.looking_away_start is not None:
                # Was looking away, now returned to screen
                distraction_duration = current_time - self.looking_away_start
                self.total_distraction_time += distraction_duration

                # Log the distraction event
                self.behavior_log.append({
                    "timestamp": current_time,
                    "event": "DISTRACTION_END",
                    "duration": distraction_duration
                })

                self.looking_away_start = None
                self.current_state = "RETURNED_TO_SCREEN"
            else:
                self.current_state = "FOCUSED"

        else:
            # Student is looking away from screen
            if self.looking_away_start is None:
                # Just started looking away
                self.looking_away_start = current_time
                self.current_state = "DISTRACTED"

                self.behavior_log.append({
                    "timestamp": current_time,
                    "event": "DISTRACTION_START",
                    "gaze_pitch": gaze_pitch,
                    "gaze_yaw": gaze_yaw
                })
            else:
                # Still looking away - check duration
                duration_away = current_time - self.looking_away_start

                if duration_away > self.critical_threshold:
                    # Critical alert - looking away too long
                    if current_time - self.last_alert_time > 2.0:  # Don't spam alerts
                        self.alert_count += 1
                        self.last_alert_time = current_time
                        self.behavior_log.append({
                            "timestamp": current_time,
                            "event": "CRITICAL_ALERT",
                            "duration": duration_away
                        })
                    self.current_state = "CRITICAL_ALERT"

                elif duration_away > self.distraction_threshold:
                    self.current_state = "WARNING"
                else:
                    self.current_state = "DISTRACTED"

        # Calculate session metrics
        session_duration = current_time - self.session_start
        focus_percentage = max(0, 100 * (1 - self.total_distraction_time / session_duration))

        return {
            "state": self.current_state,
            "alert_count": self.alert_count,
            "total_distraction_time": self.total_distraction_time,
            "session_duration": session_duration,
            "focus_percentage": focus_percentage,
            "current_gaze": {"pitch": gaze_pitch, "yaw": gaze_yaw},
            "looking_at_screen": looking_at_screen,
            "recent_events": self.behavior_log[-5:] if self.behavior_log else []
        }

    def get_status_color(self) -> Tuple[int, int, int]:
        """Get BGR color for current status"""
        color_map = {
            "FOCUSED": (0, 255, 0),  # Green
            "DISTRACTED": (0, 255, 255),  # Yellow
            "WARNING": (0, 165, 255),  # Orange
            "CRITICAL_ALERT": (0, 0, 255),  # Red
            "RETURNED_TO_SCREEN": (255, 0, 255),  # Magenta
            "INITIALIZING": (128, 128, 128)  # Gray
        }
        return color_map.get(self.current_state, (255, 255, 255))

    def reset_session(self):
        """Reset all tracking for new session"""
        self.looking_away_start = None
        self.total_distraction_time = 0.0
        self.alert_count = 0
        self.session_start = time.time()
        self.behavior_log = []
        self.current_state = "INITIALIZING"
        logging.info("Behavior session reset")