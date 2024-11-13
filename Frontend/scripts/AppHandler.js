import { EyeTrackingCalibration } from './EyeTrackingCalibration.js';

class AppHandler {
    constructor() {
        this.setupButtons();
        this.setupEventListeners();
        this.setupIPCListeners();

        // Add window close handler
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }

    setupButtons() {
        this.buttons = document.getElementById('button-container');
        this.startGaze = document.getElementById('startGaze');
        this.calibrateTracking = document.getElementById('calibrateTracking');
        this.startTesting = document.getElementById('startTesting');
        this.endTesting = document.getElementById('endTesting');
        this.startRegressor = document.getElementById('startRegressor');
        this.connectAura = document.getElementById('connectAura');
        this.startEmotions = document.getElementById('startEmotions');
        this.startPointerTracking = document.getElementById('startPointerTracking');

        if (!this.startGaze || !this.calibrateTracking || !this.startTesting || !this.endTesting) {
            throw new Error('One or more button elements not found.');
        }
    }

    setupEventListeners() {
        this.startGaze.addEventListener('click', () => this.sendCommandToBackend('start_eye_gaze'));
        this.calibrateTracking.addEventListener('click', () => this.openCalibrationWindow());
        this.startTesting.addEventListener('click', () => this.sendCommandToBackend('start_testing'));
        this.endTesting.addEventListener('click', () => this.sendCommandToBackend('stop_testing'));
        this.startRegressor.addEventListener('click', () => this.sendCommandToBackend('start_regressor'));
        this.connectAura.addEventListener('click', () => this.sendCommandToBackend('connect_aura'));
        this.startEmotions.addEventListener('click', () => this.sendCommandToBackend('start_emotions'));
        this.startPointerTracking.addEventListener('click', () => this.sendCommandToBackend('start_pointer_tracking'));
    }

    setupIPCListeners() {
        window.electronAPI.onPythonMessage((response) => {
            console.log('Received from Python:', response);
            if (response.status === 'start-calibration') {
                console.log("Starting calibration");
                this.openCalibrationWindow();
            }
        });
    }

    async sendCommandToBackend(command) {
        try {
            const response = await window.electronAPI.sendPythonCommand(command);
            // Handle response if needed
        } catch (error) {
            console.error(`Error sending ${command} to backend:`, error);
        }
    }

    openCalibrationWindow() {
        // Send IPC message to main process to open calibration window
        window.electronAPI.openCalibrationWindow();
    }

    async cleanup() {
        // Depending on your application logic,
        // ensure that calibration is only handled within the calibration window.
        // If necessary, implement additional cleanup here.
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new AppHandler();
});