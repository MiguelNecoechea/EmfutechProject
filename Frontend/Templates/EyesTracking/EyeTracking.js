class EyeTrackingCalibration {
    constructor() {
        this.calibrationArea = document.getElementById('calibrationArea');
        if (!this.calibrationArea) {
            throw new Error('Element with ID "calibrationArea" not found.');
        }

        this.buttons = document.getElementById('button-container');
        this.startGaze = document.getElementById('startGaze');
        this.calibrateTracking = document.getElementById('calibrateTracking');
        this.startTesting = document.getElementById('startTesting');
        this.endTesting = document.getElementById('endTesting');

        this.startRegressor = document.getElementById('startRegressor');
        this.connectAura = document.getElementById('connectAura');
        this.startEmotions = document.getElementById('startEmotions');


        if (!this.startGaze || !this.calibrateTracking || !this.startTesting || !this.endTesting) {
            throw new Error('One or more button elements not found.');
        }

        this.points = [];
        this.currentX = 0;
        this.currentY = 0;
        this.currentPointIndex = 0;
        this.isCalibrating = false;
        this.resizeTimeout = null;
        this.setupEventListeners();
        this.setupIPCListeners();
    }

    setupEventListeners() {
        this.startGaze.addEventListener('click', () => this.sendCommandToBackend('start_eye_gaze'));
        this.calibrateTracking.addEventListener('click', () => this.sendCommandToBackend('calibrate_eye_tracking'));
        this.startTesting.addEventListener('click', () => this.sendCommandToBackend('start_testing'));
        this.endTesting.addEventListener('click', () => this.sendCommandToBackend('stop_testing'));
        this.startRegressor.addEventListener('click', () => this.sendCommandToBackend('start_regressor'));
        this.connectAura.addEventListener('click', () => this.sendCommandToBackend('connect_aura'));
        this.startEmotions.addEventListener('click', () => this.sendCommandToBackend('start_emotions'));


        window.addEventListener('resize', () => {
            if (this.resizeTimeout) {
                clearTimeout(this.resizeTimeout);
            }

            this.resizeTimeout = setTimeout(() => {
                if (this.isCalibrating) {
                    this.updatePointPositions();
                }
            }, 250);
        });

        document.addEventListener('fullscreenchange', () => {
            if (this.isCalibrating) {
                setTimeout(() => {
                    this.updatePointPositions();
                }, 100);
            }
        });
    }

    setupIPCListeners() {
        window.electronAPI.onPythonMessage((response) => {
            console.log('Received from Python:', response);
            if (response.status === 'start-calibration') {
                console.log("Starting calibration");
                this.initializeCalibration();
            }
        });
    }

    async sendCommandToBackend(command) {
        try {
            const response = await window.electronAPI.sendPythonCommand(command);
        } catch (error) {
            console.error(`Error sending ${command} to backend:`, error);
        }
    }

    async initializeCalibration() {
        try {
            await window.electronAPI.sendPythonCommand('start_recording_training_data');

            this.buttons.style.display = 'none';
            await document.documentElement.requestFullscreen();
            setTimeout(() => {
                const calibrationPoints = this.generateCalibrationPoints();
                this.points = calibrationPoints.map(pos => this.createPoint(pos.x, pos.y));
                this.showNextPoint();
            }, 1000);
        } catch (error) {
            console.error('Error initializing calibration:', error);
            this.handleError(error);
        }
    }

    generateCalibrationPoints() {
        const padding = Math.min(window.innerWidth, window.innerHeight) * 0.05;
        const width = window.innerWidth;
        const height = window.innerHeight;
        return [
            { x: padding, y: padding },
            { x: width / 2, y: padding },
            { x: width - padding, y: padding },
            { x: padding, y: height / 2 },
            { x: width / 2, y: height / 2 },
            { x: width - padding, y: height / 2 },
            { x: padding, y: height - padding },
            { x: width / 2, y: height - padding },
            { x: width - padding, y: height - padding }
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

        if (this.currentPointIndex > 0 && this.currentPointIndex <= this.points.length) {
            const currentPoint = this.points[this.currentPointIndex - 1];
            this.currentX = parseInt(currentPoint.dataset.x);
            this.currentY = parseInt(currentPoint.dataset.y);

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
            console.log(this.currentX, this.currentY);

            try {
                await new Promise(resolve => setTimeout(resolve, 500));
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
            this.buttons.style.display = 'block';
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
    }

    handleError(error) {
        console.error('Calibration error:', error);
        this.isCalibrating = false;
        this.reset();
        alert('An error occurred during calibration. Please try again.');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new EyeTrackingCalibration();
});