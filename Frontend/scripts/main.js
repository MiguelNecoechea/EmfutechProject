const { app, BrowserWindow, ipcMain, dialog } = require('electron');
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

                // Ensure data directory exists
                if (!fs.existsSync(dataDir)) {
                    fs.mkdirSync(dataDir, { recursive: true });
                }

                // Create experiment folder
                const experimentFolder = path.join(
                    experimentData.folder,
                    experimentData.name
                );

                // Create the experiment folder
                fs.mkdirSync(experimentFolder, { recursive: true });

                // Update the folder path in experimentData to include the experiment name
                const experimentWithUpdatedPath = {
                    ...experimentData,
                    folder: experimentFolder,
                    createdAt: new Date().toISOString()
                };

                // Read existing data
                let experiments = [];
                if (fs.existsSync(filePath)) {
                    const fileContent = fs.readFileSync(filePath, 'utf8');
                    experiments = JSON.parse(fileContent);
                }

                // Add new experiment
                experiments.push(experimentWithUpdatedPath);

                // Write back to file
                fs.writeFileSync(filePath, JSON.stringify(experiments, null, 2));
                
                // After successful save, broadcast update to all windows
                this.mainWindow.webContents.send('experiment-update');
                
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
                // Get experiment data to access its folder
                const experiments = JSON.parse(
                    fs.readFileSync(path.join(__dirname, '..', 'data', 'experiments.json'), 'utf8')
                );
                const experiment = experiments.find(e => e.createdAt === participantData.experimentId);
                
                if (!experiment) {
                    throw new Error('Experiment not found');
                }

                // Create participant folder inside experiment folder
                const participantFolder = path.join(
                    experiment.folder,
                    participantData.name
                );

                // Create folders recursively
                fs.mkdirSync(participantFolder, { recursive: true });

                // Save participant data to participants.json
                const dataDir = path.join(__dirname, '..', 'data');
                const filePath = path.join(dataDir, 'participants.json');

                // Ensure data directory exists
                if (!fs.existsSync(dataDir)) {
                    fs.mkdirSync(dataDir, { recursive: true });
                }

                // Read existing participants
                let participants = [];
                if (fs.existsSync(filePath)) {
                    const fileContent = fs.readFileSync(filePath, 'utf8');
                    participants = JSON.parse(fileContent);
                }

                // Add folder path to participant data
                const participantWithFolder = {
                    ...participantData,
                    folderPath: participantFolder
                };

                // Add new participant
                participants.push(participantWithFolder);

                // Write back to file
                fs.writeFileSync(filePath, JSON.stringify(participants, null, 2));
                
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
            height: 900,
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
        try {
            for await (const [msg] of this.socket) {
                if (this.isShuttingDown || !this.socket) break;

                try {
                    const response = JSON.parse(msg.toString());
                    
                    if (this.reportResponseResolver) {
                        this.reportResponseResolver(response);
                        this.reportResponseResolver = null;
                    } else if ((response.type === 'frame' || response.type === 'gaze_frame') && this.frameStreamWindow) {
                        try {
                            if (!this.frameStreamWindow.isDestroyed()) {
                                this.frameStreamWindow.webContents.send('frame-data', response);
                            }
                        } catch (windowError) {
                            console.error('Error sending frame data:', windowError);
                            this.frameStreamWindow = null;
                        }
                    } else if (this.mainWindow) {
                        try {
                            if (!this.mainWindow.isDestroyed()) {
                                this.mainWindow.webContents.send('python-message', response);
                            }
                        } catch (windowError) {
                            console.error('Error sending message to main window:', windowError);
                            this.mainWindow = null;
                        }
                    }
                } catch (error) {
                    if (!this.isShuttingDown) {
                        console.error('Error processing message:', error);
                    }
                }
            }
        } catch (error) {
            if (!this.isShuttingDown) {
                console.error('ZMQ message loop error:', error);
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

        // Close frame stream window first
        if (this.frameStreamWindow) {
            try {
                // Send stop camera view before closing socket
                if (this.socket) {
                    await this.sendToPython('stop_camera_view');
                }
                this.frameStreamWindow.destroy();
                this.frameStreamWindow = null;
            } catch (error) {
                console.error('Error closing frame stream window:', error);
            }
        }

        // Send final stop command and close socket
        if (this.socket) {
            try {
                await this.sendToPython('stop');
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

        this.frameStreamWindow.on('closed', async () => {
            await this.sendToPython('stop_camera_view');
            this.frameStreamWindow = null;
        });
    }

    async createExperimentWindow() {
        const experimentWindow = new BrowserWindow({
            width: 600,
            height: 500,
            modal: true,
            parent: this.mainWindow,
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
            height: 300,
            modal: true,
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
}

// Initialize the application
const appManager = new ApplicationManager();