class EyeTrackingCalibration {
    constructor() {
        this.calibrationArea = document.getElementById('calibrationArea');
        this.startButton = document.getElementById('startButton');
        this.points = [];
        this.currentX = 0;
        this.currentY = 0;
        this.currentPointIndex = 0;
        this.isCalibrating = false;
        this.resizeTimeout = null;
        this.setupEventListeners();
        this.setupIPCListeners();
    }

    setupIPCListeners() {
        window.electronAPI.onPythonMessage((response) => {
            console.log('Received from Python:', response);
            // Handle various responses here
        });
    }

    setupEventListeners() {
        // Start button listener
        this.startButton.addEventListener('click', async () => {
            this.startButton.style.display = 'none';
            try {
                await this.initializeCalibration();
            } catch (err) {
                console.error('Error starting calibration:', err);
                this.handleError(err);
            }
        });

        // Window resize listener with debouncing
        window.addEventListener('resize', () => {
            if (this.resizeTimeout) {
                clearTimeout(this.resizeTimeout);
            }

            this.resizeTimeout = setTimeout(() => {
                if (this.isCalibrating) {
                    this.updatePointPositions();
                }
            }, 250); // Debounce resize events
        });

        // Fullscreen change listener
        document.addEventListener('fullscreenchange', () => {
            if (this.isCalibrating) {
                setTimeout(() => {
                    this.updatePointPositions();
                }, 100); // Small delay to ensure dimensions are updated
            }
        });
    }

    async initializeCalibration() {
        try {
            this.isCalibrating = true;
            await window.electronAPI.sendPythonCommand('start_eye_gaze');
            await window.electronAPI.sendPythonCommand('start_recording_training_data');
            await document.documentElement.requestFullscreen();

            // Create initial points after a short delay to ensure fullscreen is complete
            setTimeout(() => {
                const calibrationPoints = this.generateCalibrationPoints();
                this.points = calibrationPoints.map(pos => this.createPoint(pos.x, pos.y));
                this.showNextPoint();
            }, 100);
        } catch (error) {
            console.error('Error initializing calibration:', error);
            this.handleError(error);
        }
    }

    generateCalibrationPoints() {
        const padding = Math.min(window.innerWidth, window.innerHeight) * 0.05; // Responsive padding
        const width = window.innerWidth;
        const height = window.innerHeight;

        return [
            { x: padding, y: padding }, // Top left
            { x: width / 2, y: padding }, // Top center
            { x: width - padding, y: padding }, // Top right
            { x: padding, y: height / 2 }, // Middle left
            { x: width / 2, y: height / 2 }, // Center
            { x: width - padding, y: height / 2 }, // Middle right
            { x: padding, y: height - padding }, // Bottom left
            { x: width / 2, y: height - padding }, // Bottom center
            { x: width - padding, y: height - padding } // Bottom right
        ];
    }

    updatePointPositions() {
        const newPositions = this.generateCalibrationPoints();

        this.points.forEach((point, index) => {
            const newPos = newPositions[index];
            point.style.left = `${newPos.x}px`;
            point.style.top = `${newPos.y}px`;
            point.dataset.x = newPos.x;
            point.dataset.y = newPos.y;
        });

        // Update current point coordinates if in the middle of calibration
        if (this.currentPointIndex > 0 && this.currentPointIndex <= this.points.length) {
            const currentPoint = this.points[this.currentPointIndex - 1];
            this.currentX = parseInt(currentPoint.dataset.x);
            this.currentY = parseInt(currentPoint.dataset.y);

            // Send updated coordinates to backend
            window.electronAPI.sendPythonCommand('set_coordinates', {
                x: Math.round(this.currentX),
                y: Math.round(this.currentY)
            }).catch(err => console.error('Error updating coordinates:', err));
        }
    }

    async showNextPoint() {
        if (this.currentPointIndex > 0) {
            this.points[this.currentPointIndex - 1].style.display = 'none';
        }

        if (this.currentPointIndex < this.points.length) {
            const currentPoint = this.points[this.currentPointIndex];
            currentPoint.style.display = 'block';
            this.currentX = parseInt(currentPoint.dataset.x);
            this.currentY = parseInt(currentPoint.dataset.y);

            try {
                await window.electronAPI.sendPythonCommand('set_coordinates', {
                    x: Math.round(this.currentX),
                    y: Math.round(this.currentY)
                });

                this.currentPointIndex++;
                setTimeout(() => this.showNextPoint(), 6000);
            } catch (error) {
                console.error('Error showing next point:', error);
                this.handleError(error);
            }
        } else {
            await this.finishCalibration();
        }
    }

    createPoint(x, y) {
        const point = document.createElement('div');
        point.className = 'calibration-point';
        point.style.left = `${x}px`;
        point.style.top = `${y}px`;
        point.style.display = 'none';
        point.dataset.x = x;
        point.dataset.y = y;
        this.calibrationArea.appendChild(point);
        return point;
    }

    async finishCalibration() {
        try {
            await window.electronAPI.sendPythonCommand('stop_recording_training_data');
            await window.electronAPI.sendPythonCommand('start_regressor');

            if (document.fullscreenElement) {
                await document.exitFullscreen();
            }
        } catch (error) {
            console.error('Error finishing calibration:', error);
        } finally {
            this.isCalibrating = false;
            this.reset();
        }
    }

    reset() {
        this.points.forEach(point => point.remove());
        this.points = [];
        this.currentPointIndex = 0;
        this.startButton.style.display = 'block';
    }

    handleError(error) {
        console.error('Calibration error:', error);
        this.isCalibrating = false;
        this.reset();
        // You might want to add user-facing error handling here
        alert('An error occurred during calibration. Please try again.');
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    new EyeTrackingCalibration();
});