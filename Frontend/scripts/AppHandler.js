import { EyeTrackingCalibration } from './EyeTrackingCalibration.js';

// Button states
const STATES = {
    INITIAL: 'initial',
    CALIBRATE: 'calibrate',
    CALIBRATING: 'calibrating', 
    READY: 'ready',
    RECORDING: 'recording',
    COMPLETED: 'completed',
    SELECTING_FOLDER: 'selecting_folder',
    DISABLED: 'disabled'
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
    UPDATE_PATH: 'update_output_path',
    NEW_PARTICIPANT: 'new_participant',
    GENERATE_REPORT: 'generate_report'
};

// Response messages
const MESSAGES = {
    START_CALIBRATION: 'start-calibration',
    CALIBRATION_COMPLETE: 'calibration-complete'
};

class AppHandler {
    constructor() {
        this.ENABLED = false;
        this.DISABLED = true;
        
        this.setupButtons();
        this.setupCheckboxes();
        this.setupEventListeners();
        this.setupIPCListeners();
        this.currentState = STATES.INITIAL;
        this.calibrationCount = 0;
        
        // Initial button state update
        this.checkSignalStates();

        // Add window close handler
        this.updateButtonStates(STATES.DISABLED);

        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });

        this.overlay = document.getElementById('overlay');
    }

    setupButtons() {
        this.startGaze = document.getElementById('start-gaze');
        this.start = document.getElementById('start');
        this.stop = document.getElementById('stop');
        this.selectFolder = document.getElementById('selectFolder');
        this.participantNameInput = document.getElementById('participant-name');
        this.newParticipant = document.getElementById('new-participant');
        this.generateReport = document.getElementById('generate-report'); 
        this.reportArea = document.getElementById('report-area');
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
        this.newParticipant.addEventListener('click', () => this.handleNewParticipant());
        this.generateReport.addEventListener('click', () => this.handleGenerateReport());  // Add this line

        // Checkbox event listeners
        this.signalAura.addEventListener('change', () => this.updateSignalStatus(SIGNALS.AURA, this.signalAura.checked));
        this.signalEye.addEventListener('change', () => this.updateSignalStatus(SIGNALS.GAZE, this.signalEye.checked));
        this.signalEmotion.addEventListener('change', () => this.updateSignalStatus(SIGNALS.EMOTION, this.signalEmotion.checked));
        this.signalPointer.addEventListener('change', () => this.updateSignalStatus(SIGNALS.POINTER, this.signalPointer.checked));
        this.signalScreen.addEventListener('change', () => this.updateSignalStatus(SIGNALS.SCREEN, this.signalScreen.checked));

        // Add debounced participant name update
        const participantNameInput = document.getElementById('participant-name');
        if (participantNameInput) {
            participantNameInput.addEventListener('input', this.debounce(async (event) => {
                await this.updateParticipantName(event.target.value);
            }, 500)); // Wait 500ms after typing stops before sending update
        }
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
            const response = await window.electronAPI.sendPythonCommand(COMMANDS.UPDATE_NAME, {
                name: name
            });
        } catch (error) {
            console.error('Error updating participant name:', error);
        }
    }

    async selectOutputFolder() {
        try {
            this.showOverlay();
            this.updateButtonStates(STATES.DISABLED);
            const result = await window.electronAPI.openDirectory();
            if (result) {
                await window.electronAPI.sendPythonCommand(COMMANDS.UPDATE_PATH, {
                    path: result
                });
                this.updateButtonStates(STATES.INITIAL);
                this.selectFolder.textContent = result;
                this.selectFolder.disabled = true;
            }
        } catch (error) {
            console.error('Error selecting output folder:', error);
        } finally {
            this.hideOverlay();
            this.checkSignalStates();
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
        switch (state) {
            case STATES.INITIAL:
                this.startGaze.disabled = this.DISABLED;
                this.start.disabled = this.DISABLED;
                this.stop.disabled = this.DISABLED;
                this.generateReport.disabled = this.DISABLED;
                this.participantNameInput.disabled = this.ENABLED;
                this.enableDisableCheckboxes(this.ENABLED);
                break;
            case STATES.CALIBRATING:
                this.startGaze.disabled = this.DISABLED;
                this.start.disabled = this.DISABLED;
                this.stop.disabled = this.DISABLED;
                this.generateReport.disabled = this.DISABLED;
                this.participantNameInput.disabled = this.DISABLED;
                this.newParticipant.disabled = this.DISABLED;
                this.enableDisableCheckboxes(this.DISABLED);
                break;
            case STATES.READY:
                this.startGaze.disabled = this.DISABLED;
                this.start.disabled = this.ENABLED;
                this.stop.disabled = this.DISABLED;
                this.generateReport.disabled = this.ENABLED;
                this.participantNameInput.disabled = this.DISABLED;
                this.newParticipant.disabled = this.ENABLED;
                this.enableDisableCheckboxes(this.ENABLED);
                break;
            case STATES.RECORDING:
                this.startGaze.disabled = this.DISABLED;
                this.start.disabled = this.DISABLED;
                this.stop.disabled = this.ENABLED;
                this.generateReport.disabled = this.DISABLED;
                this.participantNameInput.disabled = this.DISABLED;
                this.newParticipant.disabled = this.DISABLED;
                this.enableDisableCheckboxes(this.DISABLED); // Ensure checkboxes are disabled during recording
                break;
            case STATES.CALIBRATE:
                this.startGaze.disabled = this.ENABLED;
                this.start.disabled = this.DISABLED;
                this.stop.disabled = this.DISABLED;
                this.generateReport.disabled = this.DISABLED;
                this.participantNameInput.disabled = this.ENABLED;
                this.enableDisableCheckboxes(this.ENABLED);
                break;
            case STATES.DISABLED:
                this.startGaze.disabled = this.DISABLED;
                this.start.disabled = this.DISABLED;
                this.stop.disabled = this.DISABLED;
                this.generateReport.disabled = this.DISABLED;
                this.enableDisableCheckboxes(this.DISABLED);
                break;
            default:
                // Handle any other states
                this.enableDisableCheckboxes(this.ENABLED);
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

    showOverlay() {
        this.overlay.classList.add('active');
    }

    hideOverlay() {
        this.overlay.classList.remove('active');
    }

    // Add debounce utility method
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    async handleNewParticipant() {
        try {
            this.selectFolder.disabled = this.ENABLED;
            this.selectFolder.textContent = 'Select Folder';
            this.participantNameInput.value = '';
            this.participantNameInput.disabled = this.ENABLED;
            this.calibrationCount = 0;

            // Update button states
            this.updateButtonStates(STATES.DISABLED);
            this.generateReport.disabled = this.DISABLED;

            await window.electronAPI.sendPythonCommand(COMMANDS.NEW_PARTICIPANT);
        } catch (error) {
            console.error('Error handling new participant:', error);
        }
    }

    async handleGenerateReport() {
        try {
            this.showOverlay();
            const response = await window.electronAPI.generateReport();
            console.log("Report Response:", response);
            
            if (response && response.status === 'success') {
                if (this.reportArea) {
                    this.reportArea.innerHTML = window.marked.parse(response.message || "No report data received");
                } else {
                    console.error('Report area not found');
                }
            } else {
                console.error('Error generating report:', response);
                if (this.reportArea) {
                    this.reportArea.innerHTML = window.marked.parse('**Error generating report:** ' + 
                        (response ? response.message : 'Unknown error'));
                }
            }
        } catch (error) {
            console.error('Error generating report:', error);
            if (this.reportArea) {
                this.reportArea.innerHTML = window.marked.parse('**Error generating report:** ' + error.message);
            }
        } finally {
            this.hideOverlay();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new AppHandler();
});

