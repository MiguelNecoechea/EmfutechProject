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
    SCREEN: 'screen',
    KEYBOARD: 'keyboard'
};

// Backend commands
const COMMANDS = {
    START_GAZE: 'start_eye_gaze',
    START: 'start',
    STOP: 'stop',
    UPDATE_SIGNAL: 'update_signal',
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
        // this.updateButtonStates(STATES.INITIAL);

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

        this.isStreamSelectorOpen = false;  // Add this flag

        // Initialize signal states
        this.signalStates = {
            aura: 'inactive',
            gaze: 'inactive',
            emotion: 'inactive',
            pointer: 'inactive',
            screen: 'inactive',
            keyboard: 'inactive'
        };

        // Initialize all status elements with 'Inactive'
        const statusElements = [
            'status-aura',
            'status-eye',
            'status-emotion',
            'status-pointer',
            'status-screen',
            'status-keyboard'
        ];

        statusElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = 'Inactive';
                element.className = 'signal-status';
            }
        });

        window.electronAPI.onCalibrationStatus((status) => {
            console.log('Received calibration status:', status);
            if (status === 'complete') {
                this.handleCalibrationComplete();
            }
        });

    }

    handleCalibrationComplete() {
        console.log('Handling calibration completion');
        // Update state
        this.currentState = STATES.READY;
        
        // Unlock UI
        this.lockUIForCalibration(false);
        
        // Enable start button if it exists
        const startButton = document.getElementById('start-button');
        if (startButton) {
            startButton.disabled = false;
            startButton.classList.remove('disabled');
            startButton.classList.add('ready');
        }
        
        // Update any other UI elements that depend on calibration state
        this.updateButtonStates(STATES.READY);
    }

    setupButtons() {
        this.viewCamera = document.getElementById('view-camera');
    }

    setupEventListeners() {
        // Button event listeners
        this.hasConfirmed = false;
        
        this.viewCamera.addEventListener('click', async () => {
            // Check if a participant is selected
            const selectedParticipant = document.querySelector('.participant-item.selected');
            if (!selectedParticipant) {
                alert('Please select a participant first');
                return;
            }

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
                case 'delete-study':
                    this.handleDeleteStudy(args[0]);
                    break;
            }
        });

        // Add AURA settings button handler
        document.getElementById('aura-settings').addEventListener('click', () => {
            this.isStreamSelectorOpen = true;  // Set flag when opening window
            window.electronAPI.openStreamSelector();
            window.electronAPI.sendPythonCommand('get_aura_streams');
        });
    }
    
    setupIPCListeners() {
        window.electronAPI.onPythonMessage((response) => {
            console.log('Received from Python:', response);
            
            // Handle signal status updates
            if (response.type === 'signal_update') {
                const { signal, status } = response;
                console.log(`Received signal update: ${signal} -> ${status}`);
                this.handleSignalStatusUpdate(response);
                return;
            }

            // Handle calibration complete message
            if (response.message === 'calibration-complete') {
                console.log('Calibration completed, updating state to READY');
                this.currentState = STATES.READY;
                this.calibrationCount++;
                this.updateButtonStates(STATES.READY);
                // Unlock UI after calibration
                this.lockUIForCalibration(false);
                return;
            }

            window.electronAPI.onSignalStatusUpdate((data) => {
                console.log('Received signal status update:', data);
                this.handleSignalStatusUpdate(data);
                
                // Special handling for gaze signal becoming ready
                if (data.signal === 'gaze' && data.status === 'ready') {
                    console.log('Eye tracking calibration completed');
                    this.handleCalibrationComplete();
                }
            });

            // Handle other message types...
        });

        // Add specific signal status update listener
        window.electronAPI.onSignalStatusUpdate((data) => {
            console.log('Signal status update received:', data); // Debug log
            this.handleSignalStatusUpdate(data);
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
                
                // Preserve the experiment selection state
                const experimentElements = document.querySelectorAll('.experiment-item');
                experimentElements.forEach(element => {
                    const experimentName = element.querySelector('h3').textContent;
                    if (experimentName === document.getElementById('study-name').textContent) {
                        element.classList.add('selected');
                    }
                });
                
                // Re-enable the add participant button
                const addParticipantBtn = document.getElementById('add-participant');
                if (addParticipantBtn) {
                    addParticipantBtn.disabled = false;
                }
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

        // Add listener for when stream selector window closes
        window.electronAPI.onWindowClosed(() => {
            this.isStreamSelectorOpen = false;  // Reset flag when window closes
        });
    }

    async sendCommandToBackend(command) {
        try {
            const response = await window.electronAPI.sendPythonCommand(command);
            if (response.status === 'success') {    
                switch (command) {
                    case COMMANDS.START:
                        // Lock UI immediately after successful start
                        const selectedParticipant = document.querySelector('.participant-item.selected');
                        if (selectedParticipant) {
                            this.updateButtonStates(STATES.RECORDING);
                        }
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
                        break;
                }
                return response;
            } else {
                console.error(`Command ${command} failed:`, response.message);
                throw new Error(response.message);
            }
        } catch (error) {
            console.error(`Error sending ${command} to backend:`, error);
            throw error;
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
        this.currentState = state;
        const experimentsList = document.getElementById('experiments-list');
        const participantsList = document.getElementById('participants-list');
        const addParticipantBtn = document.getElementById('add-participant');
        const newStudyBtn = document.getElementById('new-study');

        switch (state) {
            case STATES.CALIBRATE:
                addParticipantBtn.disabled = !this.selectedExperimentId;
                newStudyBtn.disabled = this.ENABLED;
                experimentsList.style.pointerEvents = 'auto';
                participantsList.style.pointerEvents = 'auto';
                this.updateCameraButtonState(this.selectedExperimentId, this.DISABLED);
                this.updateParticipantButtonStates('stop', this.DISABLED);
                this.updateParticipantButtonStates('start', this.DISABLED);
                this.updateParticipantButtonStates('eye-tracking', this.ENABLED);
                this.lockUIForCalibration(false);
                break;
            case STATES.RECORDING:
                this.viewCamera.disabled = this.DISABLED;
                addParticipantBtn.disabled = true;
                newStudyBtn.disabled = true;
                experimentsList.style.pointerEvents = 'none';
                participantsList.style.pointerEvents = 'none';
                this.updateParticipantButtonStates('stop', this.ENABLED);
                this.updateParticipantButtonStates('start', this.DISABLED);
                this.lockUIForCalibration(true);
                break;
            case STATES.INITIAL:
                this.viewCamera.disabled = this.DISABLED;
                addParticipantBtn.disabled = !this.selectedExperimentId;
                newStudyBtn.disabled = this.ENABLED;
                experimentsList.style.pointerEvents = 'auto';
                participantsList.style.pointerEvents = 'auto';
                this.updateCameraButtonState(this.selectedExperimentId, this.DISABLED);
                this.lockUIForCalibration(false);
                break;

            case STATES.CALIBRATING:
                addParticipantBtn.disabled = this.DISABLED;
                newStudyBtn.disabled = this.DISABLED;
                this.updateCameraButtonState(this.selectedExperimentId, this.ENABLED);
                this.lockUIForCalibration(true);
                this.updateParticipantButtonStates('stop', this.DISABLED);
                this.updateParticipantButtonStates('start', this.DISABLED);
                this.updateParticipantButtonStates('eye-tracking', this.DISABLED);
                break;
            case STATES.READY:
                addParticipantBtn.disabled = !this.selectedExperimentId;
                newStudyBtn.disabled = this.ENABLED;
                experimentsList.style.pointerEvents = 'auto';
                participantsList.style.pointerEvents = 'auto';
                this.updateCameraButtonState(this.selectedExperimentId, this.ENABLED);
                this.updateParticipantButtonStates('stop', this.DISABLED);
                this.updateParticipantButtonStates('start', this.ENABLED);
                this.updateParticipantButtonStates('eye-tracking', this.DISABLED);
                this.lockUIForCalibration(false);
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

    updateParticipantButtonStates(buttonType = 'all', state = this.DISABLED) {
        document.querySelectorAll('.participant-item').forEach(item => {
            const isSelected = item.classList.contains('selected');
            const eyeTrackingBtn = item.querySelector('.eye-tracking-button');
            const startBtn = item.querySelector('.start-button');
            const stopBtn = item.querySelector('.stop-button');
            
            // Always disable buttons for non-selected participants
            if (!isSelected) {
                if (eyeTrackingBtn) eyeTrackingBtn.disabled = true;
                if (startBtn) startBtn.disabled = true;
                if (stopBtn) stopBtn.disabled = true;
                return;
            }
            
            // Update buttons only for selected participant
            if (buttonType === 'all' || buttonType === 'eye-tracking') {
                if (eyeTrackingBtn) eyeTrackingBtn.disabled = state;
            }
            if (buttonType === 'all' || buttonType === 'start') {
                if (startBtn) startBtn.disabled = state;
            }
            if (buttonType === 'all' || buttonType === 'stop') {
                if (stopBtn) stopBtn.disabled = state;
            }
        });
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
            if (!this.isViewingCamera) {
                // Use the IPC bridge to open the frame stream window
                await window.electronAPI.viewCamera();
                this.isViewingCamera = true;
                this.viewCamera.textContent = 'Close Camera';
            } else {
                await window.electronAPI.closeFrameStream();
                this.isViewingCamera = false;
                this.viewCamera.textContent = 'View Camera';
            }
        } catch (error) {
            console.error('Error handling camera view:', error);
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

                        // Get the experiment data to check signals
                        const experimentResponse = await window.electronAPI.getExperiment(experiment.createdAt);
                        if (experimentResponse.status === 'success' && experimentResponse.data && experimentResponse.data.signals) {
                            const signals = experimentResponse.data.signals;
                            
                            // Update UI status labels
                            this.updateSignalStatusLabels(signals);
                            
                            // Update backend signal statuses
                            const signalMappings = {
                                aura: 'aura',
                                eye: 'gaze',
                                emotion: 'emotion',
                                pointer: 'pointer',
                                screen: 'screen'
                            };

                            // Send each signal status to the backend
                            for (const [signal, status] of Object.entries(signals)) {
                                const backendSignal = signalMappings[signal] || signal;
                                await this.updateSignalStatus(backendSignal, status);
                            }
                        }

                        // Load participants for this experiment
                        await this.loadParticipants(experiment.createdAt);
                        
                        // Enable add participant button when an experiment is selected
                        addParticipantBtn.disabled = false;
                    });

                    // Add context menu to experiment elements
                    experimentElement.addEventListener('contextmenu', async (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        await window.electronAPI.showContextMenu('study', experiment.createdAt);
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

            // Preserve the current state
            const currentState = this.currentState;

            if (response.status === 'success') {
                response.data.forEach(participant => {
                    const participantElement = document.createElement('div');
                    participantElement.className = 'participant-item';
                    
                    // Check if eye tracking is enabled for this experiment
                    const hasEyeTracking = experimentResponse.data.signals.eye;
                    const needsCalibration = hasEyeTracking && this.calibrationCount === 0;
                    
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
                                    `<button class="control-button eye-tracking-button" disabled title="Start eye tracking calibration">Eye Track</button>` : 
                                    ''
                                }
                                <button class="control-button start-button" disabled title="Start recording">Start</button>
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
                            // Check if this participant is selected
                            const isSelected = participantElement.classList.contains('selected');
                            if (!isSelected) {
                                alert('Please select this participant first');
                                return;
                            }

                            const confirmed = confirm("By clicking OK, you agree to start recording data. This will collect interaction data. Do you wish to proceed?");
                            if (confirmed) {
                                this.hasConfirmed = true;
                                this.updateButtonStates(STATES.CALIBRATING);
                                await this.sendCommandToBackend(COMMANDS.START_GAZE);
                            }
                        });
                    }

                    startButton.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        // Check if this participant is selected
                        const isSelected = participantElement.classList.contains('selected');
                        if (!isSelected) {
                            alert('Please select this participant first');
                            return;
                        }

                        if (!this.hasConfirmed) {
                            const confirmed = confirm("By clicking OK, you agree to start recording data. This will collect interaction data. Do you wish to proceed?");
                            if (!confirmed) return;
                            this.hasConfirmed = true;
                        }
                        
                        await this.handleParticipantClick(participant, participantElement);
                        await this.sendCommandToBackend(COMMANDS.START);
                        this.updateSignalStatesForRecording(true); 
                        this.lockExperimentSelection(true);
                        this.updateButtonStates(STATES.RECORDING);
                        
                        const lengthText = document.getElementById('study-length').textContent;
                        const duration = parseInt(lengthText.split(' ')[0]);
                        
                        this.startExperimentTimer(duration);
                        window.electronAPI.minimize();
                    });

                    stopButton.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        this.hasConfirmed = false;
                        await this.stopExperiment();
                    });

                    participantElement.addEventListener('click', () => {
                        this.handleParticipantClick(participant, participantElement);
                    });

                    // Add context menu to participant elements
                    participantElement.addEventListener('contextmenu', async (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        await window.electronAPI.showContextMenu('participant', participant.createdAt);
                    });

                    participantsList.appendChild(participantElement);
                });
            }

            // Restore the state after loading participants
            this.updateButtonStates(currentState);
            
            // Update participant count
            const participantCount = document.getElementById('participant-count');
            if (participantCount) {
                participantCount.textContent = response.data.length.toString();
            }
        } catch (error) {
            console.error('Error loading participants:', error);
        }
    }

    // Add this new method
    async updateSignalStatus(signal, status) {
        try {
            await window.electronAPI.sendPythonCommand('update_signal', {
                signal: signal,
                status: status
            });
        } catch (error) {
            console.error(`Error updating signal status for ${signal}:`, error);
        }
    }

    // Update the existing updateSignalStatusLabels method
    async updateSignalStatusLabels(signals) {
        const statusElements = {
            aura: document.getElementById('status-aura'),
            gaze: document.getElementById('status-eye'),
            emotion: document.getElementById('status-emotion'),
            pointer: document.getElementById('status-pointer'),
            screen: document.getElementById('status-screen')
        };

        // Update each status label based on the signals configuration
        for (const [signal, isEnabled] of Object.entries(signals)) {
            const mappedSignal = signal === 'eye' ? 'gaze' : signal;
            const statusElement = statusElements[mappedSignal];
            
            if (statusElement) {
                if (!this.isRecording && isEnabled) {
                    // Special handling for eye tracking
                    if (signal === 'eye' && this.calibrationCount === 0) {
                        statusElement.textContent = 'Needs calibration';
                        statusElement.className = 'signal-status need-calibration';
                    } else {
                        statusElement.textContent = 'Ready';
                        statusElement.className = 'signal-status ready';
                    }
                } else {
                    // If recording or signal is disabled
                    statusElement.textContent = isEnabled ? 'Active' : 'Inactive';
                    statusElement.className = `signal-status ${isEnabled ? 'active' : 'inactive'}`;
                }
            }
        }
        
    }

    // Add this method to update signal statuses when recording starts/stops
    updateSignalStatesForRecording(isRecording) {
        Object.entries(this.signalStates).forEach(([signal, state]) => {
            if (state === 'active' || state === 'ready') {
                const signalMappings = {
                    'aura': 'status-aura',
                    'gaze': 'status-eye',
                    'emotion': 'status-emotion',
                    'pointer': 'status-pointer',
                    'screen': 'status-screen',
                    'keyboard': 'status-keyboard'
                };

                const statusElement = document.getElementById(signalMappings[signal]);
                if (statusElement) {
                    if (isRecording) {
                        statusElement.textContent = 'Recording';
                        statusElement.className = 'signal-status recording';
                        this.signalStates[signal] = 'recording';
                    } else {
                        statusElement.textContent = 'Active';
                        statusElement.className = 'signal-status active';
                        this.signalStates[signal] = 'active';
                    }
                }
            }
        });
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
            
            // Check if eye tracking is enabled and needs calibration
            if (this.selectedExperimentId) {
                const response = await window.electronAPI.getExperiment(this.selectedExperimentId);
                if (response.status === 'success' && response.data && response.data.signals) {
                    const signals = response.data.signals;
                    if (signals.eye && this.calibrationCount === 0) {
                        this.updateButtonStates(STATES.CALIBRATE);
                    } else {
                        this.updateButtonStates(STATES.READY);
                    }
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
        // this.updateButtonStates(STATES.INITIAL);
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
        // Clear any existing timer
        this.stopExperimentTimer();

        this.timer = setInterval(async () => {
            this.timeRemaining--;
            this.updateTimerDisplay(timerDisplay);

            if (this.timeRemaining <= 0) {
                clearInterval(this.timer);
                this.timer = null;
                await this.stopExperiment();
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
        this.updateSignalStatesForRecording(false);
        
        // Get the current experiment to check if it has eye tracking
        const experimentResponse = await window.electronAPI.getExperiment(this.selectedExperimentId);
        if (experimentResponse && experimentResponse.data && experimentResponse.data.signals) {
            const hasEyeTracking = experimentResponse.data.signals.eye;
            
            // Re-enable buttons based on eye tracking status
            const selectedParticipant = document.querySelector('.participant-item.selected');
            if (selectedParticipant) {
                if (hasEyeTracking) {
                    // Reset calibration and enable eye tracking button
                    this.calibrationCount = 0;
                    this.updateButtonStates(STATES.CALIBRATE);
                } else {
                    this.updateButtonStates(STATES.READY);
                }
            }
        }
        
        // Focus the window when experiment stops
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
        
        // Remove any existing listeners
        const newExperimentsList = experimentsList.cloneNode(true);
        experimentsList.parentNode.replaceChild(newExperimentsList, experimentsList);
        
        // Add context menu for the entire experiments section
        experimentsSection.addEventListener('contextmenu', async (e) => {
            // Prevent context menu if calibrating
            if (this.currentState === STATES.CALIBRATING) {
                e.preventDefault();
                return;
            }
            
            e.preventDefault();
            e.stopPropagation();
            await window.electronAPI.showContextMenu('study-area');
        });

        // For participants section
        const participantsList = document.getElementById('participants-list');
        const participantsSection = document.querySelector('.participants-section');
        
        // Remove any existing listeners
        const newParticipantsList = participantsList.cloneNode(true);
        participantsList.parentNode.replaceChild(newParticipantsList, participantsList);
        
        // Add context menu for the entire participants section
        participantsSection.addEventListener('contextmenu', async (e) => {
            // Prevent context menu if calibrating
            if (this.currentState === STATES.CALIBRATING) {
                e.preventDefault();
                return;
            }
            
            e.preventDefault();
            e.stopPropagation();
            if (this.selectedExperimentId) {
                await window.electronAPI.showContextMenu('participant-area', this.selectedExperimentId);
            }
        });

        // Add context menu prevention for individual items during calibration
        document.addEventListener('contextmenu', (e) => {
            if (this.currentState === STATES.CALIBRATING) {
                const target = e.target;
                if (target.closest('.experiment-item') || target.closest('.participant-item')) {
                    e.preventDefault();
                    return;
                }
            }
        }, true);
    }

    // Add this new method to handle study deletion
    async handleDeleteStudy(experimentId) {
        try {
            const response = await window.electronAPI.deleteExperiment(experimentId);
            if (response.status === 'success') {
                // Clear participant details if the deleted study was selected
                if (this.selectedExperimentId === experimentId) {
                    this.clearParticipantDetails();
                    this.selectedExperimentId = null;
                }
                // Reload the experiments list
                await this.loadExperiments();
            } else {
                console.error('Error deleting study:', response.message);
            }
        } catch (error) {
            console.error('Error handling study deletion:', error);
        }
    }

    // Add method to handle participant deletion
    async handleDeleteParticipant(participantId) {
        try {
            const response = await window.electronAPI.deleteParticipant(participantId);
            if (response.status === 'success') {
                // Reload the participants list
                if (this.selectedExperimentId) {
                    await this.loadParticipants(this.selectedExperimentId);
                }
            } else {
                console.error('Error deleting participant:', response.message);
            }
        } catch (error) {
            console.error('Error handling participant deletion:', error);
        }
    }

    // Add this method to handle UI locking
    lockUIForCalibration(lock) {
        const experimentsList = document.getElementById('experiments-list');
        const participantsList = document.getElementById('participants-list');
        const addParticipantBtn = document.getElementById('add-participant');
        const newStudyBtn = document.getElementById('new-study');
        const studyPanel = document.querySelector('.study-panel');
        const studyDetails = document.querySelector('.study-details');

        // Lock/unlock UI elements
        experimentsList.style.pointerEvents = lock ? 'none' : 'auto';
        participantsList.style.pointerEvents = lock ? 'none' : 'auto';
        studyPanel.style.pointerEvents = lock ? 'none' : 'auto';
        addParticipantBtn.disabled = lock;
        newStudyBtn.disabled = lock;

        // Add visual feedback for locked state
        if (lock) {
            experimentsList.style.opacity = '0.6';
            participantsList.style.opacity = '0.6';
            studyDetails.style.opacity = '0.6';
        } else {
            experimentsList.style.opacity = '1';
            participantsList.style.opacity = '1';
            studyDetails.style.opacity = '1';
        }
    }

    handleSignalStatusUpdate(response) {
        const { signal, status, message } = response;
        // Map backend signal names to frontend element IDs
        console.log(`Handling signal update: signal=${signal}, status=${status}, message=${message}`);
        const signalMappings = {
            'aura': 'status-aura',
            'gaze': 'status-eye',
            'emotion': 'status-emotion',
            'pointer': 'status-pointer',
            'screen': 'status-screen',
            'keyboard': 'status-keyboard'
        };

        const elementId = signalMappings[signal.toLowerCase()];        
        const statusElement = document.getElementById(elementId);

        if (!statusElement) {
            console.error(`Status element not found for signal: ${signal} (elementId: ${elementId})`);
            return;
        }

        // Update the status text and class
        let statusText = 'Inactive';
        let statusClass = '';

        switch (status.toLowerCase()) {
            case 'active':
                statusText = 'Active';
                statusClass = 'active';
                break;
            case 'need_calibration':
                statusText = 'Needs Calibration';
                statusClass = 'need-calibration';
                break;
            case 'calibrating':
                statusText = 'Calibrating';
                statusClass = 'calibrating';
                break;
            case 'recording':
                statusText = 'Recording';
                statusClass = 'recording';
                break;
            case 'error':
                statusText = 'Error';
                statusClass = 'error';
                break;
            case 'ready':
                statusText = 'Ready';
                statusClass = 'ready';
                break;
            case 'connecting':
                statusText = 'Connecting';
                statusClass = 'connecting';
                break;
            case 'inactive':
                statusText = 'Inactive';
                statusClass = '';
                break;
            default:
                statusText = 'Inactive';
                statusClass = '';
                break;
        }
        
        // Update the element
        statusElement.textContent = statusText;
        statusElement.className = 'signal-status' + (statusClass ? ` ${statusClass}` : '');

        if (message) {
            statusElement.title = message;
        }

        // Update internal state
        this.signalStates[signal.toLowerCase()] = status.toLowerCase();
        console.log(`Updated signal states:`, this.signalStates);
    }

}

document.addEventListener('DOMContentLoaded', () => {
    new AppHandler();
});


