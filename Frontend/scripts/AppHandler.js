import { EyeTrackingCalibration } from './EyeTrackingCalibration.js';

class AppHandler {
    constructor() {
        this.setupButtons();
        this.setupCheckboxes();
        this.setupEventListeners();
        this.setupIPCListeners();

        // Add window close handler
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }

    setupButtons() {
        this.startGaze = document.getElementById('start-gaze');
        this.start = document.getElementById('start');
        this.stop = document.getElementById('stop');
        this.report = document.getElementById('report');
        this.selectFolder = document.getElementById('selectFolder');

    }

    setupCheckboxes() {
        // Get all tracking signal checkboxes
        this.signalAura = document.querySelector('input[name="signal-aura"]');
        this.signalEye = document.querySelector('input[name="signal-eye"]');
        this.signalEmotion = document.querySelector('input[name="signal-emotion"]');
        this.signalPointer = document.querySelector('input[name="signal-pointer"]');
        this.signalScreen = document.querySelector('input[name="signal-screen"]');
    }

    setupEventListeners() {
        // Button event listeners
        this.startGaze.addEventListener('click', () => this.sendCommandToBackend('start_eye_gaze'));
        this.start.addEventListener('click', () => this.sendCommandToBackend('start'));
        this.stop.addEventListener('click', () => this.sendCommandToBackend('stop'));
        this.selectFolder.addEventListener('click', () => this.selectOutputFolder());

        // Checkbox event listeners
        this.signalAura.addEventListener('change', () => this.updateSignalStatus('aura', this.signalAura.checked));
        this.signalEye.addEventListener('change', () => this.updateSignalStatus('gaze', this.signalEye.checked));
        this.signalEmotion.addEventListener('change', () => this.updateSignalStatus('emotion', this.signalEmotion.checked));
        this.signalPointer.addEventListener('change', () => this.updateSignalStatus('pointer', this.signalPointer.checked));
        this.signalScreen.addEventListener('change', () => this.updateSignalStatus('screen', this.signalScreen.checked));
    }

    setupIPCListeners() {
        window.electronAPI.onPythonMessage((response) => {
            console.log('Received from Python:', response);
            if (response.status === 'success' && response.message === 'start-calibration') {
                console.log("Starting calibration");
                window.electronAPI.openCalibrationWindow();
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

    async updateSignalStatus(signalType, isEnabled) {
        try {
            await window.electronAPI.sendPythonCommand('update_signal_status', {
                signal: signalType,
                status: isEnabled.toString()
            });
        } catch (error) {
            console.error(`Error updating ${signalType} status:`, error);
        }
    }

    openCalibrationWindow() {
        // Send IPC message to main process to open calibration window
        window.electronAPI.openCalibrationWindow();
    }

    async updateParticipantName(name) {
        try {
            await this.sendCommandToBackend('update_participant_name', {
                name: name
            });
        } catch (error) {
            console.error('Error updating participant name:', error);
        }
    }

    async selectOutputFolder() {
        try {
            const result = await window.electronAPI.selectDirectory();
            if (result) {
                await this.sendCommandToBackend('update_output_path', {
                    path: result
                });
            }
        } catch (error) {
            console.error('Error selecting output folder:', error);
        }
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