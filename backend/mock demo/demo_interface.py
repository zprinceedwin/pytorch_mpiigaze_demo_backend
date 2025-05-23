import tkinter as tk
from tkinter import ttk
import threading
import time


class DemoControlInterface:
    def __init__(self, behavior_detector):
        self.behavior_detector = behavior_detector
        self.root = tk.Tk()
        self.root.title("QuizSecure - Behavior Monitor")
        self.root.geometry("400x300")

        self.setup_ui()
        self.running = False

    def setup_ui(self):
        # Status display
        self.status_frame = ttk.LabelFrame(self.root, text="Current Status")
        self.status_frame.pack(fill="x", padx=10, pady=5)

        self.status_label = ttk.Label(self.status_frame, text="Status: Initializing", font=("Arial", 12))
        self.status_label.pack(pady=5)

        # Metrics display
        self.metrics_frame = ttk.LabelFrame(self.root, text="Session Metrics")
        self.metrics_frame.pack(fill="x", padx=10, pady=5)

        self.alerts_label = ttk.Label(self.metrics_frame, text="Alerts: 0")
        self.alerts_label.pack()

        self.focus_label = ttk.Label(self.metrics_frame, text="Focus: 100%")
        self.focus_label.pack()

        self.time_label = ttk.Label(self.metrics_frame, text="Session Time: 00:00")
        self.time_label.pack()

        # Control buttons
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(fill="x", padx=10, pady=10)

        self.reset_button = ttk.Button(self.control_frame, text="Reset Session",
                                       command=self.reset_session)
        self.reset_button.pack(side="left", padx=5)

        # Event log
        self.log_frame = ttk.LabelFrame(self.root, text="Recent Events")
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = tk.Text(self.log_frame, height=8, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Start update loop
        self.update_display()

    def update_display(self):
        if hasattr(self.behavior_detector, 'current_state'):
            # Update status
            self.status_label.config(text=f"Status: {self.behavior_detector.current_state}")

            # Update metrics
            self.alerts_label.config(text=f"Alerts: {self.behavior_detector.alert_count}")

            session_time = time.time() - self.behavior_detector.session_start
            minutes = int(session_time // 60)
            seconds = int(session_time % 60)
            self.time_label.config(text=f"Session Time: {minutes:02d}:{seconds:02d}")

            # Update focus percentage
            if session_time > 0:
                focus_pct = 100 * (1 - self.behavior_detector.total_distraction_time / session_time)
                self.focus_label.config(text=f"Focus: {focus_pct:.1f}%")

        # Schedule next update
        self.root.after(1000, self.update_display)

    def reset_session(self):
        self.behavior_detector.reset_session()
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, "Session reset\n")
        self.log_text.config(state="disabled")

    def run(self):
        self.root.mainloop()