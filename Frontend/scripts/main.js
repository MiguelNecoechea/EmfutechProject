const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const zmq = require('zeromq');
const fs = require('fs');

class ApplicationManager {
    constructor() {
        this.pythonProcess = null;
        this.mainWindow = null;
        this.calibrationWindow = null;
        this.socket = null;
        this.isShuttingDown = false;
        this.pendingReportResponse = null;
        this.reportResponseResolver = null;
        this.frameStreamWindow = null;
        this.streamSelectorWindow = null;
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        app.whenReady().then(() => this.onAppReady());
        app.on('window-all-closed', () => this.onWindowAllClosed());
        app.on('before-quit', async (event) => {
            event.preventDefault();
            await this.cleanup();
            app.exit(0);
        });
        app.on('activate', () => this.onActivate());

        // Handle uncaught exceptions
        process.on('uncaughtException', async (error) => {
            console.error('Uncaught Exception:', error);
            await this.cleanup();
            app.exit(1);
        });

        // Listen for calibration window requests
        ipcMain.on('open-calibration-window', () => {
            this.createCalibrationWindow();
        });

        ipcMain.handle('open-directory', async () => {
            const result = await dialog.showOpenDialog({
                properties: ['openDirectory']
            });
            
            if (!result.canceled) {
                return result.filePaths[0];
            }
            return null;
        });

        // New special handler for report generation
        ipcMain.handle('generate-report', async () => {
            try {
                // Create a promise that will be resolved when we get the response
                const responsePromise = new Promise((resolve) => {
                    this.reportResponseResolver = resolve;
                });

                // Send the command
                await this.sendToPython('generate_report');

                // Wait for the response (will be resolved in startMessageLoop)
                const response = await responsePromise;
                this.reportResponseResolver = null;
                return response;
            } catch (error) {
                console.error('Error generating report:', error);
                return { status: 'error', message: error.toString() };
            }
        });

        ipcMain.on('minimize-window', () => {
            if (this.mainWindow) {
                this.mainWindow.minimize();
            }
        });

        ipcMain.on('open-experiment-window', () => {
            this.createExperimentWindow();
        });

        // Listen for frame stream window requests
        ipcMain.on('view-camera', async () => {
            try {
                await this.createFrameStreamWindow();
                await this.sendToPython('view_camera');
            } catch (error) {
                console.error('Error handling view-camera:', error);
            }
        });

        // Add handler for closing frame stream window
        ipcMain.on('close-frame-stream', () => {
            if (this.frameStreamWindow && !this.frameStreamWindow.isDestroyed()) {
                this.frameStreamWindow.close();
            }
        });

        ipcMain.on('create-experiment-window', async () => {
            await this.createExperimentWindow();
        });

        ipcMain.on('close-window', (event) => {
            console.log('Received close-window event');
            const win = BrowserWindow.fromWebContents(event.sender);
            if (win) {
                console.log('Window found, closing...');
                win.close();
            } else {
                console.log('Window not found');
            }
        });

        ipcMain.on('update-study-panel', (event, experimentData) => {
            // Send the data to the main window
            if (this.mainWindow) {
                this.mainWindow.webContents.send('study-panel-update', experimentData);
            }
        });

        ipcMain.handle('save-experiment', async (event, experimentData) => {
            try {
                const dataDir = path.join(__dirname, '..', 'data');
                const filePath = path.join(dataDir, 'experiments.json');

                // Create experiment folder
                const experimentFolder = path.join(
                    experimentData.folder,
                    experimentData.name
                );
                fs.mkdirSync(experimentFolder, { recursive: true });

                // Update the folder path in experimentData
                const experimentWithUpdatedPath = {
                    ...experimentData,
                    folder: experimentFolder,
                    createdAt: new Date().toISOString()
                };

                // Read existing experiments
                const experiments = await this.readJSONSafely(filePath);
                experiments.push(experimentWithUpdatedPath);

                // Write updated experiments
                await this.writeJSONSafely(filePath, experiments);
                
                // Broadcast update
                if (this.mainWindow) {
                    this.mainWindow.webContents.send('experiment-update');
                }
                
                return { 
                    status: 'success',
                    folderPath: experimentFolder 
                };
            } catch (error) {
                return { 
                    status: 'error', 
                    message: error.message 
                };
            }
        });

        ipcMain.handle('get-experiments', async () => {
            try {
                const dataDir = path.join(__dirname, '..', 'data');
                const filePath = path.join(dataDir, 'experiments.json');

                if (!fs.existsSync(filePath)) {
                    return { status: 'success', data: [] };
                }

                const fileContent = fs.readFileSync(filePath, 'utf8');
                const experiments = JSON.parse(fileContent);
                
                return { status: 'success', data: experiments };
            } catch (error) {
                return { status: 'error', message: error.message };
            }
        });

        ipcMain.handle('save-participant', async (event, participantData) => {
            try {
                const experimentsPath = path.join(__dirname, '..', 'data', 'experiments.json');
                const experiments = await this.readJSONSafely(experimentsPath);
                
                const experiment = experiments.find(e => e.createdAt === participantData.experimentId);
                if (!experiment) {
                    throw new Error('Experiment not found');
                }

                // Create participant folder
                const participantFolder = path.join(
                    experiment.folder,
                    participantData.name
                );
                fs.mkdirSync(participantFolder, { recursive: true });

                // Add folder path to participant data
                const participantWithFolder = {
                    ...participantData,
                    folderPath: participantFolder,
                    createdAt: new Date().toISOString()
                };

                // Save participant data
                const participantsPath = path.join(__dirname, '..', 'data', 'participants.json');
                const participants = await this.readJSONSafely(participantsPath);
                participants.push(participantWithFolder);
                
                await this.writeJSONSafely(participantsPath, participants);
                
                return { 
                    status: 'success',
                    folderPath: participantFolder
                };
            } catch (error) {
                return { 
                    status: 'error', 
                    message: error.message 
                };
            }
        });

        ipcMain.handle('get-participants', async (event, experimentId) => {
            try {
                const dataDir = path.join(__dirname, '..', 'data');
                const filePath = path.join(dataDir, 'participants.json');

                if (!fs.existsSync(filePath)) {
                    return { status: 'success', data: [] };
                }

                const fileContent = fs.readFileSync(filePath, 'utf8');
                const allParticipants = JSON.parse(fileContent);
                
                // Filter participants by experiment ID
                const experimentParticipants = allParticipants.filter(
                    p => p.experimentId === experimentId
                );
                
                return { status: 'success', data: experimentParticipants };
            } catch (error) {
                return { status: 'error', message: error.message };
            }
        });

        ipcMain.on('update-participant-count', (event, data) => {
            // Broadcast participant update to all windows
            this.mainWindow.webContents.send('participant-update', data);
            // Also trigger an experiment update to refresh the list
            this.mainWindow.webContents.send('experiment-update');
        });

        // Add handler for opening participant window
        ipcMain.on('open-participant-window', (event, experimentId) => {
            this.createParticipantWindow(experimentId);
        });

        ipcMain.on('focus-window', () => {
            if (this.mainWindow) {
                this.mainWindow.show();  // Make sure window is visible
                this.mainWindow.focus(); // Focus the window
                if (this.mainWindow.isMinimized()) {
                    this.mainWindow.restore(); // Restore if minimized
                }
            }
        });

        ipcMain.handle('get-experiment', async (event, experimentId) => {
            try {
                const dataDir = path.join(__dirname, '..', 'data');
                const filePath = path.join(dataDir, 'experiments.json');

                if (!fs.existsSync(filePath)) {
                    return { status: 'error', message: 'Experiments file not found' };
                }

                const fileContent = fs.readFileSync(filePath, 'utf8');
                const experiments = JSON.parse(fileContent);
                const experiment = experiments.find(e => e.createdAt === experimentId);

                if (!experiment) {
                    return { status: 'error', message: 'Experiment not found' };
                }

                return { status: 'success', data: experiment };
            } catch (error) {
                return { status: 'error', message: error.message };
            }
        });

            // Start of Selection
            ipcMain.handle('show-context-menu', (event, menuType, id) => {
                const window = BrowserWindow.fromWebContents(event.sender);
                
                let menuTemplate = [];

                switch (menuType) {
                    case 'study':
                        menuTemplate = [
                            {
                                label: 'New Study',
                                click: () => {
                                    window.webContents.send('menu-action', 'new-study');
                                }
                            },
                            {
                                label: 'Add Participant',
                                click: () => {
                                    window.webContents.send('menu-action', 'add-participant', id);
                                }
                            },
                            { type: 'separator' },
                            {
                                label: 'Delete Study',
                                click: async () => {
                                    const choice = await dialog.showMessageBox(window, {
                                        type: 'warning',
                                        buttons: ['Cancel', 'Delete'],
                                        defaultId: 0,
                                        title: 'Confirm Study Deletion',
                                        message: 'Are you sure you want to delete this study?',
                                        detail: 'This will permanently delete the study and all associated participant data.'
                                    });

                                    if (choice.response === 1) {
                                        window.webContents.send('menu-action', 'delete-study', id);
                                    }
                                }
                            }
                        ];
                        break;

                    case 'participant':
                    case 'participant-area':
                        // Only show menu if we have a selected study ID
                        if (id) {  // id here is the selectedExperimentId
                            menuTemplate = [
                                {
                                    label: 'Add Participant',
                                    click: () => {
                                        window.webContents.send('menu-action', 'add-participant', id);
                                    }
                                }
                            ];
                            
                            // Only add delete option for individual participants
                            if (menuType === 'participant') {
                                menuTemplate.push(
                                    { type: 'separator' },
                                    {
                                        label: 'Delete Participant',
                                        click: async () => {
                                            const choice = await dialog.showMessageBox(window, {
                                                type: 'warning',
                                                buttons: ['Cancel', 'Delete'],
                                                defaultId: 0,
                                                title: 'Confirm Participant Deletion',
                                                message: 'Are you sure you want to delete this participant?',
                                                detail: 'This will permanently delete all participant data.'
                                            });

                                            if (choice.response === 1) {
                                                window.webContents.send('menu-action', 'delete-participant', id);
                                            }
                                        }
                                    }
                                );
                            }
                        } else {
                            // Show message if no study is selected
                            dialog.showMessageBox(window, {
                                type: 'info',
                                title: 'No Study Selected',
                                message: 'Please select a study first before adding participants.',
                            });
                            return; // Don't show context menu
                        }
                        break;

                    case 'study-area':
                        menuTemplate = [
                            {
                                label: 'New Study',
                                click: () => {
                                    window.webContents.send('menu-action', 'new-study');
                                }
                            }
                        ];
                        break;
                }

                if (menuTemplate.length > 0) {
                    const menu = Menu.buildFromTemplate(menuTemplate);
                    menu.popup({ window });
                }
            });

        // Add new handler for deleting experiments
        ipcMain.handle('delete-experiment', async (event, experimentId) => {
            try {
                const dataDir = path.join(__dirname, '..', 'data');
                const experimentsPath = path.join(dataDir, 'experiments.json');
                const participantsPath = path.join(dataDir, 'participants.json');

                // Read experiments file
                const experiments = JSON.parse(fs.readFileSync(experimentsPath, 'utf8'));
                const experimentToDelete = experiments.find(e => e.createdAt === experimentId);

                if (!experimentToDelete) {
                    return { status: 'error', message: 'Experiment not found' };
                }

                // Delete experiment folder if it exists
                if (experimentToDelete.folder && fs.existsSync(experimentToDelete.folder)) {
                    fs.rmSync(experimentToDelete.folder, { recursive: true, force: true });
                }

                // Remove experiment from experiments.json
                const updatedExperiments = experiments.filter(e => e.createdAt !== experimentId);
                fs.writeFileSync(experimentsPath, JSON.stringify(updatedExperiments, null, 2));

                // Remove associated participants
                if (fs.existsSync(participantsPath)) {
                    const participants = JSON.parse(fs.readFileSync(participantsPath, 'utf8'));
                    const updatedParticipants = participants.filter(p => p.experimentId !== experimentId);
                    fs.writeFileSync(participantsPath, JSON.stringify(updatedParticipants, null, 2));
                }

                return { status: 'success' };
            } catch (error) {
                return { status: 'error', message: error.message };
            }
        });

        // Add handler for deleting participants
        ipcMain.handle('delete-participant', async (event, participantId) => {
            try {
                const dataDir = path.join(__dirname, '..', 'data');
                const participantsPath = path.join(dataDir, 'participants.json');

                // Read participants file
                const participants = JSON.parse(fs.readFileSync(participantsPath, 'utf8'));
                const participantToDelete = participants.find(p => p.createdAt === participantId);

                if (!participantToDelete) {
                    return { status: 'error', message: 'Participant not found' };
                }

                // Delete participant folder if it exists
                if (participantToDelete.folderPath && fs.existsSync(participantToDelete.folderPath)) {
                    fs.rmSync(participantToDelete.folderPath, { recursive: true, force: true });
                }

                // Remove participant from participants.json
                const updatedParticipants = participants.filter(p => p.createdAt !== participantId);
                fs.writeFileSync(participantsPath, JSON.stringify(updatedParticipants, null, 2));

                return { status: 'success' };
            } catch (error) {
                return { status: 'error', message: error.message };
            }
        });

        ipcMain.on('open-stream-selector', () => {
            if (!this.streamSelectorWindow) {
                this.createStreamSelectorWindow();
            }
        });
    }

    async onAppReady() {
        try {
            await this.startPythonBackend();
            await this.createWindow();
            await this.setupZMQSocket();
            this.setupIPCHandlers();
        } catch (error) {
            console.error('Error during app initialization:', error);
            await this.cleanup();
            app.exit(1);
        }
    }

    async createWindow() {
        this.mainWindow = new BrowserWindow({
            width: 1200,
            height: 1000,
            minWidth: 1200,
            minHeight: 900,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js')
            }
        });

        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
        });

        await this.mainWindow.loadFile('Frontend/UI/index.html');
        this.mainWindow.webContents.openDevTools();
    }

    async createCalibrationWindow() {
        if (this.calibrationWindow) {
            this.calibrationWindow.focus();
            return;
        }

        this.calibrationWindow = new BrowserWindow({
            fullscreen: true,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js')
            }
        });

        this.calibrationWindow.loadFile('Frontend/UI/calibration.html');

        this.calibrationWindow.once('ready-to-show', () => {
            this.calibrationWindow.show();
        });

        this.calibrationWindow.on('closed', () => {
            this.calibrationWindow = null;
        });
    }

    async startPythonBackend() {
        const scriptPath = path.join('main.py');
        console.log('Starting Python backend:', scriptPath);

        if (!require('fs').existsSync(scriptPath)) {
            throw new Error(`Python script not found at: ${scriptPath}`);
        }

        this.pythonProcess = spawn('python', [scriptPath], {
            stdio: 'inherit',
            detached: false,
            env: { ...process.env, PYTHONUNBUFFERED: '1' }
        });

        return new Promise((resolve, reject) => {
            this.pythonProcess.on('error', (err) => {
                console.error('Failed to start Python backend:', err);
                reject(err);
            });

            this.pythonProcess.on('spawn', () => {
                // Wait for the process to fully start
                setTimeout(resolve, 2000);
            });

            // Handle Python process exit
            this.pythonProcess.on('exit', (code, signal) => {
                console.log(`Python backend exited with code ${code} and signal ${signal}`);
                this.pythonProcess = null;
            });
        });
    }

    async setupZMQSocket() {
        if (this.socket) {
            await this.socket.close();
        }

        this.socket = new zmq.Pair();
        await this.socket.connect("tcp://localhost:5556");

        // Handle incoming messages
        this.startMessageLoop();
    }

    async startMessageLoop() {
        while (!this.isShuttingDown) {
            try {
                const message = await this.socket.receive();

                // Convert the message to a string and parse it
                let messageString;
                if (message instanceof Uint8Array) {
                    messageString = new TextDecoder().decode(message);
                } else {
                    messageString = message.toString();
                }

                const response = this.handleMessage(messageString);
                if (response) {
                    this.mainWindow.webContents.send('python-message', response);
                }
            } catch (error) {
                if (error.code === 'EAGAIN') {
                    if (!this.isShuttingDown) {
                        console.error('EAGAIN Error: No message received.');
                    }
                    // If shutting down, silently ignore the EAGAIN error
                } else {
                    console.error('Error in message loop:', error);
                }
                // Optional: Add a short delay to prevent a tight loop in case of continuous errors
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }
    }

    setupIPCHandlers() {
        ipcMain.handle('python-command', async (event, command, params) => {
            try {
                await this.sendToPython(command, params);
                return { status: 'success' };
            } catch (error) {
                console.error('Error sending command to Python:', error);
                return { status: 'error', message: error.toString() };
            }
        });
    }

    async sendToPython(command, params = {}) {
        if (!this.socket || this.isShuttingDown) return;

        const message = { command, params };
        await this.socket.send(JSON.stringify(message));
    }

    async cleanup() {
        if (this.isShuttingDown) return;

        this.isShuttingDown = true;
        console.log('Starting cleanup...');
    
        try {
            // Optional: Send a shutdown message to the backend if needed
            await this.sendToPython('shutdown'); // Define a 'shutdown' command in your backend
    
            // Wait briefly to allow any final messages to be processed
            await new Promise(resolve => setTimeout(resolve, 500));
        } catch (error) {
            console.error('Error sending shutdown command:', error);
        }
    
        // Proceed to close the socket after signaling shutdown
        if (this.socket) {
            try {
                await this.socket.close();
                console.log('ZMQ socket closed');
            } catch (error) {
                console.error('Error closing ZMQ socket:', error);
            }
            this.socket = null;
        }    

        // Close other windows
        if (this.calibrationWindow) {
            this.calibrationWindow.destroy();
            this.calibrationWindow = null;
        }

        if (this.mainWindow) {
            this.mainWindow.destroy();
            this.mainWindow = null;
        }

        // Terminate Python process last
        if (this.pythonProcess) {
            try {
                this.pythonProcess.kill('SIGTERM');
                await new Promise((resolve) => {
                    const timeout = setTimeout(() => {
                        if (this.pythonProcess) {
                            this.pythonProcess.kill('SIGKILL');
                        }
                        resolve();
                    }, 5000);

                    this.pythonProcess.on('exit', () => {
                        clearTimeout(timeout);
                        resolve();
                    });
                });
                console.log('Python process terminated');
            } catch (error) {
                console.error('Error terminating Python process:', error);
            }
            this.pythonProcess = null;
        }

        console.log('Cleanup completed');
    }

    async onWindowAllClosed() {
        if (this.isShuttingDown) {
            // If the app is shutting down, do not restart the Python backend
            return;
        }

        if (process.platform === 'darwin') {
            console.log('All windows closed on macOS. Restarting Python backend...');
            await this.restartPythonBackend();
        } else {
            await this.cleanup();
            app.quit();
        }
    }

    async restartPythonBackend() {
        if (this.pythonProcess) {
            try {
                console.log('Stopping existing Python backend...');
                this.pythonProcess.kill('SIGTERM');
                await new Promise((resolve) => {
                    this.pythonProcess.on('exit', () => {
                        console.log('Python backend stopped.');
                        resolve();
                    });
                });
            } catch (error) {
                console.error('Error terminating Python process:', error);
            }
            this.pythonProcess = null;
        }

        try {
            console.log('Starting Python backend...');
            await this.startPythonBackend();
            console.log('Python backend restarted successfully.');
        } catch (error) {
            console.error('Failed to restart Python backend:', error);
        }
    }

    async onActivate() {
        if (!this.mainWindow) {
            await this.createWindow();
            // Optionally, restart the Python backend if needed
            if (!this.pythonProcess) {
                await this.restartPythonBackend();
            }
        }
    }

    async createFrameStreamWindow() {
        if (this.frameStreamWindow) {
            this.frameStreamWindow.focus();
            return;
        }

        this.frameStreamWindow = new BrowserWindow({
            width: 800,
            height: 600,
            minWidth: 600,
            minHeight: 400,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js')
            }
        });

        await this.frameStreamWindow.loadFile('Frontend/UI/frameStream.html');

        // Handle any type of window close
        const handleClose = async () => {
            try {
                // Stop the camera view in the backend
                await this.sendToPython('stop_camera_view');
                
                // Notify both windows about the camera being closed
                if (this.frameStreamWindow && !this.frameStreamWindow.isDestroyed()) {
                    this.frameStreamWindow.webContents.send('close-frame-stream');
                }
                if (this.mainWindow && !this.mainWindow.isDestroyed()) {
                    this.mainWindow.webContents.send('camera-closed');
                }
            } catch (error) {
                console.error('Error handling frame stream window close:', error);
            }
        };

        // Listen for the window close event
        this.frameStreamWindow.on('close', handleClose);

        this.frameStreamWindow.on('closed', () => {
            this.frameStreamWindow = null;
        });
    }

    async createExperimentWindow() {
        const experimentWindow = new BrowserWindow({
            width: 600,
            height: 950,
            modal: true,
            parent: this.mainWindow,
            resizable: false,
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js'),
                sandbox: false
            }
        });

        await experimentWindow.loadFile('Frontend/UI/AddExperimentView.html');
    }

    async createParticipantWindow(experimentId) {
        const participantWindow = new BrowserWindow({
            width: 400,
            height: 325,
            modal: true,
            resizable: false,
            parent: this.mainWindow,
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js'),
                sandbox: false
            }
        });

        await participantWindow.loadFile(
            'Frontend/UI/AddParticipantView.html',
            { query: { experimentId } }
        );
    }

    async createStreamSelectorWindow() {
        this.streamSelectorWindow = new BrowserWindow({
            width: 400,
            height: 300,
            modal: true,
            parent: this.mainWindow,
            resizable: false,
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js'),
                sandbox: false
            }
        });

        await this.streamSelectorWindow.loadFile('Frontend/UI/StreamSelector.html');

        // Handle window closed event
        this.streamSelectorWindow.on('closed', () => {
            this.streamSelectorWindow = null;
        });
    }

    async readJSONSafely(filePath) {
        try {
            // Ensure the directory exists
            const dir = path.dirname(filePath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            
            // If file doesn't exist, return empty array
            if (!fs.existsSync(filePath)) {
                return [];
            }

            // Read and parse file
            const data = await fs.promises.readFile(filePath, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            console.error(`Error reading JSON file ${filePath}:`, error);
            throw error;
        }
    }

    async writeJSONSafely(filePath, data) {
        try {
            // Ensure the directory exists
            const dir = path.dirname(filePath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }

            // Write to temporary file first
            const tempPath = `${filePath}.tmp`;
            await fs.promises.writeFile(tempPath, JSON.stringify(data, null, 2));
            
            // Rename temp file to actual file (atomic operation)
            await fs.promises.rename(tempPath, filePath);
        } catch (error) {
            console.error(`Error writing JSON file ${filePath}:`, error);
            throw error;
        }
    }

    handleMessage(message) {
        try {
            const data = JSON.parse(message);

            // Handle different message types
            if (data.type === 'frame' || data.type === 'gaze_frame') {
                // Forward camera/gaze frames to the frame stream window
                if (this.frameStreamWindow && !this.frameStreamWindow.isDestroyed()) {
                    this.frameStreamWindow.webContents.send('frame', data);
                }
                return null;
            }

            if (data.type === 'signal_update') {
                // Add debug logging
                console.log('Main process received signal update:', data);
                // Forward signal updates to main window
                if (this.mainWindow && !this.mainWindow.isDestroyed()) {
                    this.mainWindow.webContents.send('signal-status-update', {
                        signal: data.signal,
                        status: data.status,
                        message: data.message
                    });
                }
                return null;
            }

            // Add specific handling for calibration messages
            if (data.message === 'start-calibration') {
                // Create calibration window when backend signals it's ready
                this.createCalibrationWindow();
                return null;
            }

            if (data.message === 'calibration-complete') {
                // Close calibration window when calibration is complete
                if (this.calibrationWindow) {
                    this.calibrationWindow.close();
                }
                // Notify main window of completion
                if (this.mainWindow) {
                    this.mainWindow.webContents.send('calibration-status', 'complete');
                }
                return null;
            }

            // Handle report response
            if (this.reportResponseResolver) {
                this.reportResponseResolver(data);
                return null;
            }

            // For any other messages, forward them to the main window
            if (this.mainWindow && !this.mainWindow.isDestroyed()) {
                this.mainWindow.webContents.send('python-message', data);
            }

            return null;
        } catch (error) {
            console.error('Error handling message:', error);
            return null;
        }
    }
}

// Initialize the application
const appManager = new ApplicationManager();