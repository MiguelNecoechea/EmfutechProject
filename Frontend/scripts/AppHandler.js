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
        this.setupEventListeners();
        this.setupIPCListeners();
        this.currentState = STATES.INITIAL;
        this.calibrationCount = 0;
        this.isCameraActive = false;
        
        // Initial button state update
        this.updateButtonStates(STATES.INITIAL);

        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });

        this.overlay = document.getElementById('overlay');
        this.isViewingCamera = false;

        this.selectedExperimentId = null;
        this.loadExperiments();

        this.timer = null;
        this.experimentDuration = 0;
        this.timeRemaining = 0;
        this.timers = new Map(); // Add this to track multiple timers
        this.isRecording = false; // Add this flag to track recording state

        // Setup context menus
        this.setupContextMenus();
    }

    setupButtons() {
        this.viewCamera = document.getElementById('view-camera');
    }

    setupEventListeners() {
        // Button event listeners
        this.hasConfirmed = false;
        
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

        document.getElementById('new-study').addEventListener('click', () => {
            window.electronAPI.openExperimentWindow();
        });

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

        // Add menu action listener
        window.electronAPI.onMenuAction((action, ...args) => {
            switch (action) {
                case 'new-study':
                    window.electronAPI.openExperimentWindow();
                    break;
                case 'add-participant':
                    const experimentId = args[0];
                    window.electronAPI.openParticipantWindow(experimentId);
                    break;
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

        // Add listener for camera closed events
        window.electronAPI.onCameraClosed(() => {
            this.isViewingCamera = false;
            this.viewCamera.textContent = 'View Camera';
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
                        // Close camera view if it's open
                        if (this.isViewingCamera) {
                            await window.electronAPI.closeFrameStream();
                            this.isViewingCamera = false;
                        }
                        
                        // Disable the view camera button
                        this.viewCamera.disabled = true;
                        this.viewCamera.textContent = 'View Camera';
                        
                        // Get the experiment data to check if eye tracking is enabled
                        const experiment = await window.electronAPI.getExperiment(this.selectedExperimentId);
                        if (experiment && experiment.data && experiment.data.signals) {
                            if (experiment.data.signals.eye && this.calibrationCount === 0) {
                                this.updateButtonStates(STATES.CALIBRATE);
                            } else {
                                this.updateButtonStates(STATES.READY);
                            }
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

    // Add method to handle camera button state
    updateCameraButtonState(experimentId, state) {
        // Check if camera is enabled in study before enabling view camera button
        window.electronAPI.getExperiment(experimentId).then(experiment => {
            if (experiment && experiment.data && experiment.data.signals &&
                (experiment.data.signals.eye || experiment.data.signals.emotion)) {
                this.viewCamera.disabled = state;
            }
        });
    }

    // Add this new method to manage button states
    updateButtonStates(state) {
        // Store current state for reference 
        this.currentState = state;
        const experimentsList = document.getElementById('experiments-list');
        const participantsList = document.getElementById('participants-list');
        const addParticipantBtn = document.getElementById('add-participant');
        const newStudyBtn = document.getElementById('new-study');

        // First, reset all buttons to default state
        this.viewCamera.disabled = this.DISABLED;
        addParticipantBtn.disabled = this.DISABLED;
        newStudyBtn.disabled = this.DISABLED;

        switch (state) {
            case STATES.INITIAL:
                // Initial state - everything enabled except camera
                this.viewCamera.disabled = this.DISABLED;
                addParticipantBtn.disabled = !this.selectedExperimentId;
                newStudyBtn.disabled = this.ENABLED;
                experimentsList.style.pointerEvents = 'auto';
                participantsList.style.pointerEvents = 'auto';
                this.updateCameraButtonState(this.selectedExperimentId, this.DISABLED);
                break;
            case STATES.CALIBRATING:
                // During calibration - disable most interactions
                addParticipantBtn.disabled = this.DISABLED;
                newStudyBtn.disabled = this.DISABLED;
                experimentsList.style.pointerEvents = 'none';
                participantsList.style.pointerEvents = 'none';
                this.updateCameraButtonState(this.selectedExperimentId, this.ENABLED);
                break;

            case STATES.READY:
                // Ready to record - enable necessary controls
                addParticipantBtn.disabled = !this.selectedExperimentId;
                newStudyBtn.disabled = this.ENABLED;
                experimentsList.style.pointerEvents = 'auto';
                participantsList.style.pointerEvents = 'auto';
                this.updateCameraButtonState(this.selectedExperimentId, this.DISABLED);
                break;

            case STATES.RECORDING:
                // During recording - lock most interactions
                this.viewCamera.disabled = this.DISABLED;
                addParticipantBtn.disabled = this.DISABLED;
                newStudyBtn.disabled = this.DISABLED;
                experimentsList.style.pointerEvents = 'none';
                participantsList.style.pointerEvents = 'none';
                this.updateCameraButtonState(this.selectedExperimentId, this.ENABLED);
                break;

            case STATES.DISABLED:
                this.viewCamera.disabled = this.DISABLED;
                addParticipantBtn.disabled = this.DISABLED;
                newStudyBtn.disabled = this.DISABLED;
                experimentsList.style.pointerEvents = 'none';
                participantsList.style.pointerEvents = 'none';
                this.updateCameraButtonState(this.selectedExperimentId, this.DISABLED);
                break;

            default:
                // Default state - enable basic interactions
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
            const experimentsList = document.getElementById('experiments-list');
            const addParticipantBtn = document.getElementById('add-participant');
            experimentsList.innerHTML = '';
            
            // Disable add participant button when no experiment is selected
            addParticipantBtn.disabled = true;

            if (response.status === 'success') {
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

                        // Enable add participant button when an experiment is selected
                        addParticipantBtn.disabled = false;
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
            const experimentResponse = await window.electronAPI.getExperiment(experimentId);
            const participantsList = document.getElementById('participants-list');
            participantsList.innerHTML = '';

            if (response.status === 'success') {
                response.data.forEach(participant => {
                    const participantElement = document.createElement('div');
                    participantElement.className = 'participant-item';
                    
                    // Check if eye tracking is enabled for this experiment
                    const hasEyeTracking = experimentResponse.data.signals.eye;
                    
                    participantElement.innerHTML = `
                        <div class="participant-content">
                            <div class="participant-info">
                                <h4 class="participant-name">${participant.name}</h4>
                                <div class="participant-details">
                                    <span>Age: ${participant.age}</span>
                                    <span>Gender: ${participant.gender}</span>
                                    <span>Added: ${new Date(participant.createdAt).toLocaleDateString()}</span>
                                </div>
                                <div class="participant-folder">
                                    <span title="${participant.folderPath}">📁 ${participant.name}</span>
                                </div>
                            </div>
                            <div class="participant-controls">
                                ${hasEyeTracking ? 
                                    `<button class="control-button eye-tracking-button" title="Start eye tracking calibration">Eye Track</button>` : 
                                    ''
                                }
                                <button class="control-button start-button" title="Start recording">Start</button>
                                <button class="control-button stop-button" disabled title="Stop recording">Stop</button>
                            </div>
                        </div>
                    `;

                    // Add event listeners for the buttons
                    const startButton = participantElement.querySelector('.start-button');
                    const stopButton = participantElement.querySelector('.stop-button');
                    const eyeTrackingButton = participantElement.querySelector('.eye-tracking-button');

                    if (eyeTrackingButton) {
                        eyeTrackingButton.addEventListener('click', async (e) => {
                            e.stopPropagation();
                            const confirmed = confirm("By clicking OK, you agree to start recording data. This will collect interaction data. Do you wish to proceed?");
                            if (confirmed) {
                                this.hasConfirmed = true;
                                await this.sendCommandToBackend(COMMANDS.START_GAZE);
                                eyeTrackingButton.disabled = true;
                                startButton.disabled = false;
                            }
                        });
                    }

                    // Add method to update button states
                    const updateButtonStates = (isRecording) => {
                        startButton.disabled = isRecording;
                        stopButton.disabled = !isRecording;
                        
                        // Update the inactive class on the participant item
                        document.querySelectorAll('.participant-item').forEach(item => {
                            if (item !== participantElement) {
                                item.classList.add('inactive');
                                const itemStartBtn = item.querySelector('.start-button');
                                const itemStopBtn = item.querySelector('.stop-button');
                                if (itemStartBtn && itemStopBtn) {
                                    itemStartBtn.disabled = true;
                                    itemStopBtn.disabled = true;
                                }
                            } else {
                                item.classList.remove('inactive');
                            }
                        });
                    };

                    startButton.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        if (!this.hasConfirmed) {
                            const confirmed = confirm("By clicking OK, you agree to start recording data. This will collect interaction data. Do you wish to proceed?");
                            if (!confirmed) return;
                            this.hasConfirmed = true;
                        }
                        
                        await this.handleParticipantClick(participant, participantElement);
                        await this.sendCommandToBackend(COMMANDS.START);
                        
                        const lengthText = document.getElementById('study-length').textContent;
                        const duration = parseInt(lengthText.split(' ')[0]);
                        
                        this.startExperimentTimer(duration);
                        updateButtonStates(true);
                        window.electronAPI.minimize();
                    });

                    stopButton.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        this.hasConfirmed = false;
                        await this.stopExperiment();
                        updateButtonStates(false);
                        document.querySelectorAll('.participant-item').forEach(item => {
                            item.classList.remove('inactive');
                            const itemStartBtn = item.querySelector('.start-button');
                            const itemStopBtn = item.querySelector('.stop-button');
                            if (itemStartBtn && itemStopBtn) {
                                itemStartBtn.disabled = false;
                                itemStopBtn.disabled = true;
                            }
                        });
                    });

                    participantElement.addEventListener('click', () => {
                        this.handleParticipantClick(participant, participantElement);
                    });

                    participantsList.appendChild(participantElement);
                });
            }
        } catch (error) {
            console.error('Error loading participants:', error);
        }
    }

    // Update method to handle signal status updates
    updateSignalStatusLabels(signals) {
        const statusElements = {
            aura: document.getElementById('status-aura'),
            gaze: document.getElementById('status-eye'),
            emotion: document.getElementById('status-emotion'),
            pointer: document.getElementById('status-pointer'),
            screen: document.getElementById('status-screen')
        };

        // Update each status label based on the signals configuration
        Object.entries(signals).forEach(([signal, isEnabled]) => {
            const statusElement = statusElements[signal === 'eye' ? 'gaze' : signal];
            if (statusElement) {
                statusElement.textContent = isEnabled ? 'Active' : 'Inactive';
                statusElement.className = `signal-status ${isEnabled ? 'active' : 'inactive'}`;
            }
        });

        // Update button states based on active signals
        const anySignalActive = Object.values(signals).some(signal => signal);
        if (anySignalActive) {
            if (signals.eye && this.calibrationCount === 0) {
                this.updateButtonStates(STATES.CALIBRATE);
            } else {
                this.updateButtonStates(STATES.READY);
            }
        } else {
            this.updateButtonStates(STATES.INITIAL);
        }
    }

    // Add this new method to handle signal status updates to backend
    async updateSignalStatus(signal, status) {
        try {
            await window.electronAPI.sendPythonCommand(COMMANDS.UPDATE_SIGNAL, {
                signal: signal,
                status: status
            });
        } catch (error) {
            console.error(`Error updating ${signal} status:`, error);
        }
    }

    async handleParticipantClick(participant, element) {
        // Remove selected class from all participants
        document.querySelectorAll('.participant-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // Add selected class to clicked participant
        element.classList.add('selected');
        
        try {
            // Update participant name and folder path in backend
            await window.electronAPI.sendPythonCommand(COMMANDS.UPDATE_NAME, {
                name: participant.name,
            });

            await window.electronAPI.sendPythonCommand(COMMANDS.UPDATE_PATH, {
                path: participant.folderPath
            });
            
            // Update participant info panel
            document.getElementById('current-participant-name').textContent = participant.name;
            document.getElementById('current-participant-age').textContent = participant.age;
            
            // Get the experiment data
            const response = await window.electronAPI.getExperiment(this.selectedExperimentId);
            if (response.status === 'success' && response.data && response.data.signals) {
                const signals = response.data.signals;
                
                // Update UI status labels
                this.updateSignalStatusLabels(signals);
                
                // Update backend signal statuses
                const signalMappings = {
                    aura: 'aura',
                    eye: 'gaze',  // Map 'eye' to 'gaze' for backend
                    emotion: 'emotion',
                    pointer: 'pointer',
                    screen: 'screen'
                };

                // Send each signal status to the backend
                for (const [signal, status] of Object.entries(signals)) {
                    const backendSignal = signalMappings[signal] || signal;
                    await this.updateSignalStatus(backendSignal, status);
                }

                // Update button states based on signals
                if (signals.eye && this.calibrationCount === 0) {
                    this.updateButtonStates(STATES.CALIBRATE);
                } else if (Object.values(signals).some(status => status)) {
                    this.updateButtonStates(STATES.READY);
                } else {
                    this.updateButtonStates(STATES.INITIAL);
                }
            }
        } catch (error) {
            console.error('Error handling participant selection:', error);
        }
    }

    // Add method to clear participant details
    clearParticipantDetails() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        this.updateButtonStates(STATES.INITIAL);
        document.getElementById('current-participant-name').textContent = 'None';
        document.getElementById('current-participant-age').textContent = '-';
    }

    // Add this method to handle stopping experiment timer
    stopExperimentTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        const timerDisplay = document.getElementById('time-remaining');
        if (timerDisplay) {
            timerDisplay.textContent = '--:--';
        }
    }

    // Update the timer methods to work with individual displays
    startExperimentTimer(duration) {
        this.experimentDuration = duration * 60;
        this.timeRemaining = this.experimentDuration;
        const timerDisplay = document.getElementById('time-remaining');
        this.updateTimerDisplay(timerDisplay);

        // Lock experiment selection
        this.lockExperimentSelection(true);

        // Clear any existing timer
        this.stopExperimentTimer();

        this.timer = setInterval(async () => {
            this.timeRemaining--;
            this.updateTimerDisplay(timerDisplay);

            if (this.timeRemaining <= 0) {
                clearInterval(this.timer);
                this.timer = null;
                await this.stopExperiment();
                
                // Reset all participant buttons and unlock selection
                document.querySelectorAll('.participant-item').forEach(item => {
                    const startBtn = item.querySelector('.start-button');
                    const stopBtn = item.querySelector('.stop-button');
                    if (startBtn && stopBtn) {
                        startBtn.disabled = false;
                        stopBtn.disabled = true;
                    }
                });
                
                this.lockExperimentSelection(false);
                await window.electronAPI.focusWindow();
                timerDisplay.textContent = '--:--';
            }
        }, 1000);
    }

    updateTimerDisplay(timerDisplay) {
        const minutes = Math.floor(this.timeRemaining / 60);
        const seconds = this.timeRemaining % 60;
        const display = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        timerDisplay.textContent = display;
    }

    async stopExperiment() {
        this.stopExperimentTimer();
        await this.sendCommandToBackend(COMMANDS.STOP);
        this.hasConfirmed = false;
        this.lockExperimentSelection(false);
        await window.electronAPI.focusWindow();
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

    // Add this method to handle experiment selection locking
    lockExperimentSelection(lock) {
        this.isRecording = lock;
        const experimentsList = document.getElementById('experiments-list');
        const participantsList = document.getElementById('participants-list');
        
        // Add or remove the inactive class based on lock state
        experimentsList.style.pointerEvents = lock ? 'none' : 'auto';
        experimentsList.style.opacity = lock ? '0.6' : '1';
        
        // For participants, we need to keep the stop button functional
        const participants = participantsList.querySelectorAll('.participant-item');
        participants.forEach(participant => {
            const stopButton = participant.querySelector('.stop-button');
            const content = participant.querySelector('.participant-details');
            const header = participant.querySelector('h4');
            const folder = participant.querySelector('.participant-folder');
            
            if (lock) {
                participant.style.pointerEvents = 'none';
                if (stopButton && !stopButton.disabled) {
                    stopButton.style.pointerEvents = 'auto';
                    participant.style.pointerEvents = 'auto';
                }
                content.style.opacity = '0.6';
                header.style.opacity = '0.6';
                folder.style.opacity = '0.6';
            } else {
                participant.style.pointerEvents = 'auto';
                content.style.opacity = '1';
                header.style.opacity = '1';
                folder.style.opacity = '1';
            }
        });
    }

    // Setup context menus
    setupContextMenus() {
        // For experiments section
        const experimentsList = document.getElementById('experiments-list');
        const experimentsSection = document.querySelector('.experiments-section');
        
        experimentsSection.addEventListener('contextmenu', async (e) => {
            e.preventDefault();
            await window.electronAPI.showContextMenu('new-study');
        });

        // For participants section
        const participantsSection = document.querySelector('.participants-section');
        
        participantsSection.addEventListener('contextmenu', async (e) => {
            e.preventDefault();
            if (this.selectedExperimentId) {
                await window.electronAPI.showContextMenu('add-participant', this.selectedExperimentId);
            }
        });
    }

}

document.addEventListener('DOMContentLoaded', () => {
    new AppHandler();
});


