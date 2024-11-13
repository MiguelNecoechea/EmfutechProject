import EyeTrackingCalibration from './EyeTrackingCalibration.js';

class AppHandler {
    constructor() {
        this.setupButtons();
        this.calibration = new EyeTrackingCalibration();
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
        this.calibrateTracking.addEventListener('click', () => this.sendCommandToBackend('calibrate_eye_tracking'));
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
                this.calibration.initializeCalibration();
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

    async cleanup() {
        if (this.calibration.isCalibrating) {
            try {
                await window.electronAPI.sendPythonCommand('stop_recording_training_data');
                await window.electronAPI.sendPythonCommand('stop');
            } catch (error) {
                console.error('Error during cleanup:', error);
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new AppHandler();
});