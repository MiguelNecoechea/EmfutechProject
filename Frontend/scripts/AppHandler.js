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
    GENERATE_REPORT: 'generate_report',
    VIEW_CAMERA: 'view_camera',
    SELECT_PARTICIPANT: 'select_participant'
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
        this.isCameraActive = false;
        
        // Initial button state update
        this.checkSignalStates();

        // Add window close handler
        this.updateButtonStates(STATES.DISABLED);

        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });

        this.overlay = document.getElementById('overlay');
        this.isViewingCamera = false;

        // Add this line to load experiments when the app starts
        this.selectedExperimentId = null;
        this.loadExperiments();

        this.timer = null;
        this.experimentDuration = 0;
        this.timeRemaining = 0;
    }

    setupButtons() {
        this.startGaze = document.getElementById('start-gaze');
        this.start = document.getElementById('start');
        this.stop = document.getElementById('stop');
        this.reportArea = document.getElementById('report-area');
        this.viewCamera = document.getElementById('view-camera');
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
        let hasConfirmed = false;
        
        this.startGaze.addEventListener('click', async () => {
            const confirmed = confirm("By clicking OK, you agree to start recording data. This will collect interaction data. Do you wish to proceed?");
            if (confirmed) {
                hasConfirmed = true;
                this.viewCamera.disabled = this.ENABLED;
                await this.sendCommandToBackend(COMMANDS.START_GAZE);
            }
        });
        
        this.start.addEventListener('click', async () => {
            if (!hasConfirmed) {
                const confirmed = confirm("By clicking OK, you agree to start recording data. This will collect interaction data. Do you wish to proceed?");
                if (!confirmed) return;
            }
            
            // Get the experiment duration from the study length display
            const lengthText = document.getElementById('study-length').textContent;
            const duration = parseInt(lengthText.split(' ')[0]); // Extract number from "X minutes"
            
            await this.sendCommandToBackend(COMMANDS.START);
            this.startExperimentTimer(duration);
            window.electronAPI.minimize();
        });
        
        this.stop.addEventListener('click', async () => {
            hasConfirmed = false;
            await this.stopExperiment();
        });
        
        this.viewCamera.addEventListener('click', async () => {
            if (!this.isViewingCamera) {
                await this.handleViewCamera();
                this.isViewingCamera = true;
                this.viewCamera.textContent = 'Close Camera View';
            } else {
                await window.electronAPI.closeFrameStream();
                this.isViewingCamera = false;
                this.viewCamera.textContent = 'View Camera';
            }
        });

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

        // Add window close handler to reset camera view state
        window.addEventListener('beforeunload', () => {
            if (this.isViewingCamera) {
                window.electronAPI.closeFrameStream();
            }
        });

        document.getElementById('new-study').addEventListener('click', () => {
            window.electronAPI.openExperimentWindow();
        });

        // Modify add participant button handler
        const addParticipantBtn = document.getElementById('add-participant');
        if (addParticipantBtn) {
            addParticipantBtn.addEventListener('click', () => {
                if (!this.selectedExperimentId) {
                    alert('Please select an experiment first');
                    return;
                }
                window.electronAPI.openParticipantWindow(this.selectedExperimentId);
            });
        }

        // Add participant count update listener
        window.electronAPI.onParticipantUpdate((participantData) => {
            const participantCount = document.getElementById('participant-count');
            if (participantCount) {
                const currentCount = parseInt(participantCount.textContent) || 0;
                participantCount.textContent = (currentCount + 1).toString();
            }
        });
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

        // Add listener for study panel updates
        window.electronAPI.onStudyPanelUpdate((experimentData) => {
            // Update study panel elements
            document.getElementById('study-name').textContent = experimentData.name;
            document.getElementById('study-length').textContent = `${experimentData.length} minutes`;
            document.getElementById('participant-count').textContent = '0'; // Reset participant count for new study
        });

        // Update the participant update listener to refresh the list
        window.electronAPI.onParticipantUpdate(async (data) => {
            if (this.selectedExperimentId === data.experimentId) {
                // Reload participants list for the current experiment
                await this.loadParticipants(this.selectedExperimentId);
            }
        });

        // Add listener for experiment updates
        window.electronAPI.onExperimentUpdate(async () => {
            await this.loadExperiments();
        });

        // Update study panel listener
        window.electronAPI.onStudyPanelUpdate(async (experimentData) => {
            document.getElementById('study-name').textContent = experimentData.name;
            document.getElementById('study-length').textContent = `${experimentData.length} minutes`;
            document.getElementById('participant-count').textContent = '0';
            
            // Refresh the experiments list
            await this.loadExperiments();
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
                        this.viewCamera.disabled = this.DISABLED;
                        if (this.signalEye.checked && this.calibrationCount === 0) {
                            this.updateButtonStates(STATES.CALIBRATE);
                        } else {
                            this.updateButtonStates(STATES.READY);
                        }
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

    async cleanup() {
        this.stopExperimentTimer();
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
        const experimentsList = document.getElementById('experiments-list');
        const participantsList = document.getElementById('participants-list');
        switch (state) {
            case STATES.INITIAL:
                this.startGaze.disabled = this.DISABLED;
                this.start.disabled = this.DISABLED;
                this.stop.disabled = this.DISABLED;
                this.viewCamera.disabled = this.DISABLED;
                this.enableDisableCheckboxes(this.ENABLED);
                experimentsList.style.pointerEvents = 'auto';
                participantsList.style.pointerEvents = 'auto';
                break;
            case STATES.CALIBRATING:
                this.startGaze.disabled = this.DISABLED;
                this.start.disabled = this.DISABLED;
                this.stop.disabled = this.ENABLED;
                this.enableDisableCheckboxes(this.DISABLED);
                experimentsList.style.pointerEvents = 'none';
                participantsList.style.pointerEvents = 'none';
                break;
            case STATES.READY:
                this.startGaze.disabled = this.DISABLED;
                this.start.disabled = this.ENABLED;
                this.stop.disabled = this.DISABLED;
                this.enableDisableCheckboxes(this.ENABLED);
                experimentsList.style.pointerEvents = 'auto';
                participantsList.style.pointerEvents = 'auto';
                break;
            case STATES.RECORDING:
                this.startGaze.disabled = this.DISABLED;
                this.start.disabled = this.DISABLED;
                this.stop.disabled = this.ENABLED;
                this.enableDisableCheckboxes(this.DISABLED);
                experimentsList.style.pointerEvents = 'none';
                participantsList.style.pointerEvents = 'none';
                break;
            case STATES.CALIBRATE:
                this.startGaze.disabled = this.ENABLED;
                this.start.disabled = this.DISABLED;
                this.stop.disabled = this.DISABLED;
                this.enableDisableCheckboxes(this.ENABLED);
                experimentsList.style.pointerEvents = 'auto';
                participantsList.style.pointerEvents = 'auto';
                break;
            case STATES.DISABLED:
                this.startGaze.disabled = this.DISABLED;
                this.start.disabled = this.DISABLED;
                this.stop.disabled = this.DISABLED;
                this.enableDisableCheckboxes(this.DISABLED);
                experimentsList.style.pointerEvents = 'auto';
                participantsList.style.pointerEvents = 'auto';
                break;
            default:
                // Handle any other states
                experimentsList.style.pointerEvents = 'auto';
                participantsList.style.pointerEvents = 'auto';
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

    async handleViewCamera() {
        try {
            // Use the IPC bridge to open the frame stream window
            window.electronAPI.viewCamera();
        } catch (error) {
            console.error('Error opening camera view:', error);
        }
    }

    // Add this new method to load experiments
    async loadExperiments() {
        try {
            const response = await window.electronAPI.getExperiments();
            if (response.status === 'success') {
                const experimentsList = document.getElementById('experiments-list');
                experimentsList.innerHTML = '';

                response.data.forEach(experiment => {
                    const experimentElement = document.createElement('div');
                    experimentElement.className = 'experiment-item';
                    experimentElement.innerHTML = `
                        <h3>${experiment.name}</h3>
                        <p>${experiment.description}</p>
                        <div class="experiment-details">
                            <span>Length: ${experiment.length} minutes</span>
                            <span>Created: ${new Date(experiment.createdAt).toLocaleDateString()}</span>
                        </div>
                    `;
                    
                    // Add click handler to select the experiment
                    experimentElement.addEventListener('click', async () => {
                        this.selectedExperimentId = experiment.createdAt;
                        
                        // Update the study panel
                        document.getElementById('study-name').textContent = experiment.name;
                        document.getElementById('study-length').textContent = `${experiment.length} minutes`;
                        
                        // Clear participant details when switching experiments
                        this.clearParticipantDetails();
                        
                        // Highlight the selected experiment
                        document.querySelectorAll('.experiment-item').forEach(item => {
                            item.classList.remove('selected');
                        });
                        experimentElement.classList.add('selected');

                        // Load participants for this experiment
                        await this.loadParticipants(experiment.createdAt);
                    });

                    experimentsList.appendChild(experimentElement);
                });
            } else {
                console.error('Failed to load experiments:', response.message);
            }
        } catch (error) {
            console.error('Error loading experiments:', error);
        }
    }

    async loadParticipants(experimentId) {
        try {
            const response = await window.electronAPI.getParticipants(experimentId);
            const participantsList = document.getElementById('participants-list');
            participantsList.innerHTML = '';

            if (response.status === 'success') {
                response.data.forEach(participant => {
                    const participantElement = document.createElement('div');
                    participantElement.className = 'participant-item';
                    participantElement.innerHTML = `
                        <h4>${participant.name}</h4>
                        <div class="participant-details">
                            <span>Age: ${participant.age}</span>
                            <span>Gender: ${participant.gender}</span>
                            <span>Added: ${new Date(participant.createdAt).toLocaleDateString()}</span>
                        </div>
                        <div class="participant-folder">
                            <span title="${participant.folderPath}">📁 ${participant.name}</span>
                        </div>
                    `;

                    // Add click handler for participant selection
                    participantElement.addEventListener('click', () => this.handleParticipantClick(participant, participantElement));

                    participantsList.appendChild(participantElement);
                });

                // Update participant count
                document.getElementById('participant-count').textContent = response.data.length.toString();
            }
        } catch (error) {
            console.error('Error loading participants:', error);
        }
    }

    async handleParticipantClick(participant, participantElement) {
        // Update UI as before
        document.getElementById('current-participant-name').textContent = participant.name;
        document.getElementById('current-participant-age').textContent = participant.age;

        // Highlight selected participant
        document.querySelectorAll('.participant-item').forEach(item => {
            item.classList.remove('selected');
        });
        participantElement.classList.add('selected');

        // Send participant data to backend
        try {
            await window.electronAPI.sendPythonCommand(COMMANDS.UPDATE_NAME, {
                name: participant.name,
            });

            await window.electronAPI.sendPythonCommand(COMMANDS.UPDATE_PATH, {
                path: participant.folderPath
            });
            
            this.enableDisableCheckboxes(this.ENABLED);
            
        } catch (error) {
            console.error('Error sending participant data to backend:', error);
        }
    }

    // Add method to clear participant details
    clearParticipantDetails() {
        this.stopExperimentTimer();
        this.updateButtonStates(STATES.INITIAL);
        this.enableDisableCheckboxes(this.DISABLED);
        document.getElementById('current-participant-name').textContent = 'None';
        document.getElementById('current-participant-age').textContent = '-';
    }

    // Add this new method
    startExperimentTimer(duration) {
        this.experimentDuration = duration * 60; // Convert minutes to seconds
        this.timeRemaining = this.experimentDuration;
        this.updateTimerDisplay();

        this.timer = setInterval(() => {
            this.timeRemaining--;
            this.updateTimerDisplay();

            if (this.timeRemaining <= 0) {
                this.stopExperiment();
            }
        }, 1000);
    }

    // Add this new method
    updateTimerDisplay() {
        const minutes = Math.floor(this.timeRemaining / 60);
        const seconds = this.timeRemaining % 60;
        const display = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        document.getElementById('time-remaining').textContent = display;
    }

    // Add this new method
    stopExperimentTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        document.getElementById('time-remaining').textContent = '--:--';
    }

    // Add this new method
    async stopExperiment() {
        this.stopExperimentTimer();
        await this.sendCommandToBackend(COMMANDS.STOP);
        if (this.isViewingCamera) {
            await window.electronAPI.closeFrameStream();
            this.isViewingCamera = false;
            this.viewCamera.textContent = 'View Camera';
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

