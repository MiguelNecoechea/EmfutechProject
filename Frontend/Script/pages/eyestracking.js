const { ipcRenderer } = require('electron');
let remote;
try {
    remote = require('@electron/remote');
} catch (e) {
    console.warn('Error loading remote:', e);
}

class EyeTrackingCalibration {
    constructor() {
        this.calibrationArea = document.getElementById('calibrationArea');
        this.startButton = document.getElementById('startButton');
        this.points = [];
        this.currentX = 0;
        this.currentY = 0;
        this.currentPointIndex = 0;
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.startButton.addEventListener('click', async () => {
            this.startButton.style.display = 'none';
            try {
                if (remote) {
                    const win = remote.getCurrentWindow();
                    await win.setFullScreen(true);
                } else {
                    await document.documentElement.requestFullscreen();
                }
                setTimeout(() => this.initializeCalibration()); // Unified delay to ensure full-screen mode is activated
            } catch (err) {
                console.error('Error activating full-screen mode:', err);
            }
        });
    }

    /**
     * Generates the calibration points on the screen. The points are fixated in the screen, however, a future is
     * expected to move the points in a random order to improve the calibration process.
     * @returns {Array} Array of point objects with x and y coordinates.
     */
    generateCalibrationPoints() {
        const padding = 10;
        const width = window.innerWidth;
        const height = window.innerHeight;
        console.log(width, height);
        return [
            { x: padding, y: padding }, // Top-left corner
            { x: width / 2, y: padding }, // Top-center
            { x: width - padding, y: padding }, // Top-right corner

            { x: padding, y: height / 2 }, // Middle-left
            { x: width / 2, y: height / 2 }, // Center
            { x: width - padding, y: height / 2 }, // Middle-right

            { x: padding, y: height - padding }, // Bottom-left corner
            { x: width / 2, y: height - padding }, // Bottom-center
            { x: width - padding, y: height - padding } // Bottom-right corner
        ];
    }

    /**
     * Initializes the calibration process by setting up the calibration points and starting the eye gaze recording.
     */
    initializeCalibration() {
        window.addEventListener('resize', async () => {
            setTimeout(async () => {
                await eel.start_eye_gaze()();

                eel.start_recording_training_data()();

                const calibrationPoints = this.generateCalibrationPoints();
                this.points = calibrationPoints.map(pos => this.createPoint(pos.x, pos.y));
                this.showNextPoint();
            }, 500);
        }, { once: true });
    }

    /**
     * Creates a calibration point element and appends it to the calibration area.
     * @param {number} x - The x-coordinate of the point.
     * @param {number} y - The y-coordinate of the point.
     * @returns {HTMLElement} The created point element.
     */
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

    /**
     * Displays the next calibration point and sends its coordinates to the backend.
     */
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
            this.currentPointIndex++;
            setTimeout(() => this.showNextPoint(), 6000);
        } else {
            await eel.stop_recording_training_data()();
            eel.start_regressor()();
            this.finishCalibration();
        }
        eel.set_coordinates(Math.round(this.currentX), Math.round(this.currentY))();
    }

    /**
     * Finishes the calibration process and exits full-screen mode.
     */
    finishCalibration() {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        }
        if (remote) {
            const win = remote.getCurrentWindow();
            win.setFullScreen(false);
        }
        setTimeout(() => {
            this.reset();
        }, 1000);
    }

    /**
     * Resets the calibration process, clearing all points and resetting the start button.
     */
    reset() {
        this.points.forEach(point => point.remove());
        this.points = [];
        this.currentPointIndex = 0;
        this.startButton.style.display = 'block';
    }

    // Example function to be called from main.js
    exampleFunction() {
        console.log('Example function called from main.js');
    }

    // Listen for IPC messages to execute functions
    listenForIpcMessages() {
        ipcRenderer.on('execute-eyestracking-function', (event, functionName, ...args) => {
            if (typeof this[functionName] === 'function') {
                this[functionName](...args);
            } else {
                console.error(`Function ${functionName} not found in EyeTrackingCalibration`);
            }
        });
    }

}

/**
 * Initializes the EyeTrackingCalibration class when the DOM content is loaded.
 */
document.addEventListener('DOMContentLoaded', () => {
    new EyeTrackingCalibration();
    eyeTrackingCalibration.listenForIpcMessages();
});