import { EyeTrackingCalibration } from './EyeTrackingCalibration.js';

class CalibrationHandler {
    constructor() {
        this.calibration = new EyeTrackingCalibration();
        this.initialize();
    }

    async initialize() {
        try {
            await this.calibration.initializeCalibration();
            // Additional UI-related logic if needed
        } catch (error) {
            console.error('Calibration Initialization Error:', error);
            alert('Calibration failed. Please try again.');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new CalibrationHandler();
});
