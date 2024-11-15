class EyeTrackingCalibration {
    constructor() {
        this.calibrationArea = document.getElementById('calibrationArea');
        this.pointsContainer = document.getElementById('calibration-points-container');
        if (!this.calibrationArea || !this.pointsContainer) {
            throw new Error('Calibration elements not found.');
        }

        this.points = [];
        this.currentX = 0;
        this.currentY = 0;
        this.currentPointIndex = 0;
        this.isCalibrating = false;
        this.resizeTimeout = null;

        // Add resize and fullscreen listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
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

    async initializeCalibration() {
        try {
            await window.electronAPI.sendPythonCommand('start_recording_training_data');

            // Launch calibration UI in fullscreen (already handled by window settings)
            // await document.documentElement.requestFullscreen(); // Optional: Remove if window is already fullscreen
            setTimeout(() => {
                const calibrationPoints = this.generateCalibrationPoints();
                this.points = calibrationPoints.map(pos => this.createPoint(pos.x, pos.y));
                this.showNextPoint();
            }, 1000);

            this.isCalibrating = true;
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
            this.points[this.currentPointIndex - 1].classList.remove('active');
        }

        if (this.currentPointIndex < this.points.length) {
            const currentPoint = this.points[this.currentPointIndex];
            currentPoint.classList.add('active');
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
            // Calibration completed
            await this.finishCalibration();
        }
    }

    createPoint(x, y) {
        const point = document.createElement('div');
        point.className = 'calibration-point';
        point.style.left = `${x}px`;
        point.style.top = `${y}px`;
        point.dataset.x = x;
        point.dataset.y = y;
        this.pointsContainer.appendChild(point);
        return point;
    }

    async finishCalibration() {
        try {
            this.isCalibrating = false;
            await window.electronAPI.sendPythonCommand('stop_recording_training_data');
            if (document.fullscreenElement) {
                await document.exitFullscreen();
            }
            // Optionally, close the calibration window
            window.close();
        } catch (error) {
            console.error('Error finishing calibration:', error);
        } finally {
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

export { EyeTrackingCalibration }; 