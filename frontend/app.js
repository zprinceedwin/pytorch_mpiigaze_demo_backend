// QuizSecure Frontend JavaScript

class QuizSecureApp {
    constructor() {
        this.ws = null;
        this.reconnectInterval = null;
        this.isConnected = false;
        this.currentStatus = 'INITIALIZING';
        this.alertCount = 0;
        this.focusPercentage = 100;
        this.sessionTime = 0;

        this.initializeApp();
    }

    initializeApp() {
        this.setupEventListeners();
        this.connectWebSocket();
    }

    setupEventListeners() {
        // Navigation buttons
        const studentBtn = document.getElementById('studentBtn');
        const instructorBtn = document.getElementById('instructorBtn');
        const startDemo = document.getElementById('startDemo');
        const viewDashboard = document.getElementById('viewDashboard');

        if (studentBtn) {
            studentBtn.addEventListener('click', () => {
                window.location.href = '/student';
            });
        }

        if (instructorBtn) {
            instructorBtn.addEventListener('click', () => {
                window.location.href = '/instructor';
            });
        }

        if (startDemo) {
            startDemo.addEventListener('click', () => {
                window.location.href = '/student';
            });
        }

        if (viewDashboard) {
            viewDashboard.addEventListener('click', () => {
                window.location.href = '/instructor';
            });
        }

        // Student interface buttons
        const resetSession = document.getElementById('resetSession');
        const testAlert = document.getElementById('testAlert');

        if (resetSession) {
            resetSession.addEventListener('click', () => {
                this.resetSession();
            });
        }

        if (testAlert) {
            testAlert.addEventListener('click', () => {
                this.showAlert('Test Alert', 'This is a test of the alert system.');
            });
        }

        // Instructor interface buttons
        const resetAllSessions = document.getElementById('resetAllSessions');
        if (resetAllSessions) {
            resetAllSessions.addEventListener('click', () => {
                this.resetSession();
            });
        }
    }

    connectWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.updateConnectionStatus(true);

                if (this.reconnectInterval) {
                    clearInterval(this.reconnectInterval);
                    this.reconnectInterval = null;
                }
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

        } catch (error) {
            console.error('Error connecting to WebSocket:', error);
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (!this.reconnectInterval) {
            this.reconnectInterval = setInterval(() => {
                console.log('Attempting to reconnect...');
                this.connectWebSocket();
            }, 3000);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'gaze_update':
                this.updateGazeData(data);
                break;
            case 'session_reset':
                this.handleSessionReset();
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    updateGazeData(data) {
        // Update camera feed
        if (data.frame) {
            const cameraFeed = document.getElementById('cameraFeed');
            const liveStudentFeed = document.getElementById('liveStudentFeed');
            const loadingMessage = document.getElementById('loadingMessage');
            const studentLoadMsg = document.getElementById('studentLoadMsg');

            if (cameraFeed) {
                cameraFeed.src = `data:image/jpeg;base64,${data.frame}`;
                cameraFeed.classList.remove('hidden');
                if (loadingMessage) loadingMessage.style.display = 'none';
            }

            if (liveStudentFeed) {
                liveStudentFeed.src = `data:image/jpeg;base64,${data.frame}`;
                liveStudentFeed.classList.remove('hidden');
                if (studentLoadMsg) studentLoadMsg.style.display = 'none';
            }
        }

        // Update status
        this.currentStatus = data.status;
        this.alertCount = data.alerts || 0;
        this.focusPercentage = data.focus || 0;
        this.sessionTime = data.session_time || 0;

        this.updateStatusDisplay();
        this.updateMetrics();
        this.updateGazeInfo(data.gaze);

        // Check for alerts
        if (data.status === 'CRITICAL_ALERT' && this.alertCount > 0) {
            this.showAlert('Attention Required', 'Please return your focus to the exam.');
            this.logAlert(data.status, 'Critical attention deviation detected');
        }
    }

    updateStatusDisplay() {
        const statusElements = [
            document.getElementById('currentStatus'),
            document.getElementById('studentStatus')
        ];

        statusElements.forEach(element => {
            if (element) {
                element.textContent = this.currentStatus;

                // Remove all status classes
                element.classList.remove('status-focused', 'status-distracted', 'status-warning', 'status-alert');

                // Add appropriate class based on status
                switch (this.currentStatus) {
                    case 'FOCUSED':
                        element.classList.add('status-focused');
                        break;
                    case 'DISTRACTED':
                        element.classList.add('status-distracted');
                        break;
                    case 'WARNING':
                        element.classList.add('status-warning');
                        break;
                    case 'CRITICAL_ALERT':
                        element.classList.add('status-alert');
                        break;
                }
            }
        });

        // Update instructor dashboard counts
        const focusedCount = document.getElementById('focusedCount');
        if (focusedCount) {
            focusedCount.textContent = this.currentStatus === 'FOCUSED' ? '1' : '0';
        }

        const alertsCount = document.getElementById('alertsCount');
        if (alertsCount) {
            alertsCount.textContent = this.alertCount;
        }
    }

    updateMetrics() {
        // Update alert count
        const alertElements = [
            document.getElementById('alertCount'),
            document.getElementById('studentAlerts')
        ];
        alertElements.forEach(element => {
            if (element) element.textContent = this.alertCount;
        });

        // Update focus percentage
        const focusElements = [
            document.getElementById('focusPercentage'),
            document.getElementById('studentFocus')
        ];
        focusElements.forEach(element => {
            if (element) element.textContent = `${Math.round(this.focusPercentage)}%`;
        });

        // Update focus bar
        const focusBar = document.getElementById('focusBar');
        if (focusBar) {
            focusBar.style.width = `${this.focusPercentage}%`;

            // Change color based on focus level
            if (this.focusPercentage >= 80) {
                focusBar.className = 'bg-green-400 h-2 rounded-full transition-all';
            } else if (this.focusPercentage >= 60) {
                focusBar.className = 'bg-yellow-400 h-2 rounded-full transition-all';
            } else {
                focusBar.className = 'bg-red-400 h-2 rounded-full transition-all';
            }
        }

        // Update session time
        const timeElements = [
            document.getElementById('sessionTime'),
            document.getElementById('studentTime')
        ];
        timeElements.forEach(element => {
            if (element) {
                const minutes = Math.floor(this.sessionTime / 60);
                const seconds = this.sessionTime % 60;
                element.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        });
    }

    updateGazeInfo(gazeData) {
        if (gazeData) {
            const gazePitch = document.getElementById('gazePitch');
            const gazeYaw = document.getElementById('gazeYaw');

            if (gazePitch) gazePitch.textContent = gazeData.pitch.toFixed(3);
            if (gazeYaw) gazeYaw.textContent = gazeData.yaw.toFixed(3);
        }

        const gazeStatus = document.getElementById('gazeStatus');
        if (gazeStatus) {
            gazeStatus.textContent = this.isConnected ? 'Active' : 'Disconnected';
            gazeStatus.className = this.isConnected ? 'text-green-400' : 'text-red-400';
        }
    }

    updateConnectionStatus(connected) {
        // Update any connection indicators
        const indicators = document.querySelectorAll('.pulse');
        indicators.forEach(indicator => {
            if (connected) {
                indicator.classList.add('bg-green-500');
                indicator.classList.remove('bg-red-500');
            } else {
                indicator.classList.add('bg-red-500');
                indicator.classList.remove('bg-green-500');
            }
        });
    }

    showAlert(title, message) {
        const modal = document.getElementById('alertModal');
        const alertMessage = document.getElementById('alertMessage');

        if (modal && alertMessage) {
            alertMessage.textContent = message;
            modal.classList.remove('hidden');
            modal.classList.add('flex');

            // Auto-close after 5 seconds
            setTimeout(() => {
                this.closeAlert();
            }, 5000);
        }
    }

    closeAlert() {
        const modal = document.getElementById('alertModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    logAlert(type, message) {
        const recentAlerts = document.getElementById('recentAlerts');
        if (recentAlerts) {
            const now = new Date();
            const timeString = now.toLocaleTimeString();

            const alertElement = document.createElement('div');
            alertElement.className = 'p-2 bg-red-900 bg-opacity-50 rounded text-xs';
            alertElement.innerHTML = `
                <div class="font-bold text-red-400">${type}</div>
                <div class="text-gray-300">${message}</div>
                <div class="text-gray-500 text-xs">${timeString}</div>
            `;

            // Remove "no alerts" message
            const noAlerts = recentAlerts.querySelector('.text-gray-400');
            if (noAlerts) noAlerts.remove();

            // Add new alert at the top
            recentAlerts.insertBefore(alertElement, recentAlerts.firstChild);

            // Keep only last 5 alerts
            const alerts = recentAlerts.children;
            while (alerts.length > 5) {
                recentAlerts.removeChild(alerts[alerts.length - 1]);
            }
        }
    }

    resetSession() {
        if (this.ws && this.isConnected) {
            this.ws.send(JSON.stringify({ action: 'reset_session' }));
        }
    }

    handleSessionReset() {
        this.alertCount = 0;
        this.focusPercentage = 100;
        this.sessionTime = 0;
        this.currentStatus = 'FOCUSED';

        this.updateStatusDisplay();
        this.updateMetrics();

        // Clear alerts
        const recentAlerts = document.getElementById('recentAlerts');
        if (recentAlerts) {
            recentAlerts.innerHTML = '<div class="text-gray-400 text-center py-4">No alerts yet</div>';
        }
    }
}

// Student interface specific functions
function initStudentInterface() {
    // Student-specific initialization
    console.log('Student interface initialized');
}

// Instructor interface specific functions
function initInstructorInterface() {
    // Instructor-specific initialization
    console.log('Instructor interface initialized');
}

// Global alert function
function closeAlert() {
    const modal = document.getElementById('alertModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.quizSecureApp = new QuizSecureApp();
});