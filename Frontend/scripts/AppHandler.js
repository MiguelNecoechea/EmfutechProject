import { EyeTrackingCalibration } from './EyeTrackingCalibration.js';


// Button states
const STATES = {
    INITIAL: 'initial',
    CALIBRATE: 'calibrate',
    CALIBRATING: 'calibrating', 
    READY: 'ready',
    RECORDING: 'recording',
    COMPLETED: 'completed'
};

// Signal types
const SIGNALS = {
    AURA: 'aura',
    GAZE: 'gaze',
    EMOTION: 'emotion',
    POINTER: 'pointer',
    SCREEN: 'screen'
};

// Backend commands
const COMMANDS = {
    START_GAZE: 'start_eye_gaze',
    START: 'start',
    STOP: 'stop',
    UPDATE_SIGNAL: 'update_signal_status',
    UPDATE_NAME: 'update_participant_name',
    UPDATE_PATH: 'update_output_path'
};

// Response messages
const MESSAGES = {
    START_CALIBRATION: 'start-calibration',
    CALIBRATION_COMPLETE: 'calibration-complete'
};

class AppHandler {
    constructor() {
        this.setupButtons();
        this.setupCheckboxes();
        this.setupEventListeners();
        this.setupIPCListeners();
        this.currentState = STATES.INITIAL;
        this.calibrationCount = 0;
        
        // Initial button state update
        this.checkSignalStates();

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

        // Initialize button states
        this.updateButtonStates(STATES.INITIAL);
    }

    setupCheckboxes() {
        // Get all tracking signal checkboxes
        this.signalAura = document.querySelector('input[name="signal-aura"]');
        this.signalEye = document.querySelector('input[name="signal-eye"]');
        this.signalEmotion = document.querySelector('input[name="signal-emotion"]');
        this.signalPointer = document.querySelector('input[name="signal-pointer"]');
        this.signalScreen = document.querySelector('input[name="signal-screen"]');

        // Add checkbox state change handler
        const checkboxes = [this.signalAura, this.signalEye, this.signalEmotion, this.signalPointer, this.signalScreen];
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => this.checkSignalStates());
        });
    }

    setupEventListeners() {
        // Button event listeners
        this.startGaze.addEventListener('click', () => this.sendCommandToBackend(COMMANDS.START_GAZE));
        this.start.addEventListener('click', () => this.sendCommandToBackend(COMMANDS.START));
        this.stop.addEventListener('click', () => this.sendCommandToBackend(COMMANDS.STOP));
        this.selectFolder.addEventListener('click', () => this.selectOutputFolder());

        // Checkbox event listeners
        this.signalAura.addEventListener('change', () => this.updateSignalStatus(SIGNALS.AURA, this.signalAura.checked));
        this.signalEye.addEventListener('change', () => this.updateSignalStatus(SIGNALS.GAZE, this.signalEye.checked));
        this.signalEmotion.addEventListener('change', () => this.updateSignalStatus(SIGNALS.EMOTION, this.signalEmotion.checked));
        this.signalPointer.addEventListener('change', () => this.updateSignalStatus(SIGNALS.POINTER, this.signalPointer.checked));
        this.signalScreen.addEventListener('change', () => this.updateSignalStatus(SIGNALS.SCREEN, this.signalScreen.checked));
    }

    setupIPCListeners() {
        window.electronAPI.onPythonMessage((response) => {
            console.log('Received from Python:', response);
            if (response.status === 'success') {
                switch (response.message) {
                    case MESSAGES.START_CALIBRATION:
                        console.log("Starting calibration");
                        this.updateButtonStates(STATES.CALIBRATING);
                        window.electronAPI.openCalibrationWindow();
                        break;
                    case MESSAGES.CALIBRATION_COMPLETE:
                        this.calibrationCount++;
                        this.updateButtonStates(STATES.READY);
                        break;
                }
            }
        });
    }

    async sendCommandToBackend(command) {
        try {
            const response = await window.electronAPI.sendPythonCommand(command);
            if (response.status === 'success') {    
                switch (command) {
                    case COMMANDS.START:
                        this.updateButtonStates(STATES.RECORDING);
                        break;
                case COMMANDS.STOP:
                    this.updateButtonStates(STATES.READY); 
                    break;
            }
        }
        } catch (error) {
            console.error(`Error sending ${command} to backend:`, error);
        }
    }

    async updateSignalStatus(signalType, isEnabled) {
        try {
            await window.electronAPI.sendPythonCommand(COMMANDS.UPDATE_SIGNAL, {
                signal: signalType,
                status: isEnabled.toString()
            });
            this.checkSignalStates(); // Check signal states after update
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
            await this.sendCommandToBackend(COMMANDS.UPDATE_NAME, {
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
                await this.sendCommandToBackend(COMMANDS.UPDATE_PATH, {
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

    enableDisableCheckboxes(enable) {
        // Filter out any undefined checkboxes before trying to modify them
        [this.signalAura, this.signalEye, this.signalEmotion, 
         this.signalPointer, this.signalScreen]
         .filter(checkbox => checkbox !== undefined)
         .forEach(checkbox => {
            checkbox.disabled = enable;
        });
    }

    // Add this new method to manage button states
    updateButtonStates(state) {
        // Store current state for reference 
        this.currentState = state;
        let ENABLED = false;
        let DISABLED = true;

        switch (state) {
            case STATES.INITIAL:
                // Initial state at launching the app
                this.startGaze.disabled = DISABLED;
                this.start.disabled = DISABLED;
                this.stop.disabled = DISABLED;
                this.report.disabled = DISABLED;
                this.selectFolder.disabled = DISABLED;

                break;
            case STATES.CALIBRATING:
                // During eye gaze calibration
                this.startGaze.disabled = DISABLED;
                this.start.disabled = DISABLED;
                this.stop.disabled = DISABLED;
                this.report.disabled = DISABLED;
                this.selectFolder.disabled = DISABLED;
                // this.enableDisableCheckboxes(DISABLED);
                break;
            case STATES.READY:
                // Ready state after calibration or no calibration needed
                this.startGaze.disabled = DISABLED;
                this.start.disabled = ENABLED;
                this.stop.disabled = DISABLED;
                this.report.disabled = DISABLED;
                this.selectFolder.disabled = DISABLED;
                this.enableDisableCheckboxes(ENABLED);
                break;
            case STATES.RECORDING:
                // During recording
                this.startGaze.disabled = DISABLED;
                this.start.disabled = DISABLED;
                this.stop.disabled = ENABLED;
                this.report.disabled = DISABLED;
                this.selectFolder.disabled = DISABLED;
                this.enableDisableCheckboxes(DISABLED); // Ensure checkboxes are disabled during recording
                break;
            case STATES.COMPLETED:
                // After recording is stopped
                this.startGaze.disabled = DISABLED;
                this.start.disabled = ENABLED;
                this.stop.disabled = DISABLED;
                this.report.disabled = ENABLED;
                this.selectFolder.disabled = ENABLED;
                this.enableDisableCheckboxes(ENABLED);
                break;
            case STATES.CALIBRATE:
                // Calibration state
                this.startGaze.disabled = ENABLED;
                this.start.disabled = DISABLED;
                this.stop.disabled = DISABLED;
                this.report.disabled = DISABLED;
                this.selectFolder.disabled = DISABLED;
                break;
            default:
                // Handle any other states
                this.enableDisableCheckboxes(ENABLED);
                break;
        }
    }

    // Add new method to check if any signal is active
    checkSignalStates() {
        const anySignalActive = [
            this.signalAura.checked,
            this.signalEye.checked,
            this.signalEmotion.checked,
            this.signalPointer.checked,
            this.signalScreen.checked
        ].some(checked => checked);

        if (anySignalActive) {
            if (this.signalEye.checked && this.calibrationCount == 0) {
                this.updateButtonStates(STATES.CALIBRATE);
            } else {
                this.updateButtonStates(STATES.READY);
            }
        } else if (!anySignalActive) {
            this.updateButtonStates(STATES.INITIAL);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new AppHandler();
});