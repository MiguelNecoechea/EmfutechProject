const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const zmq = require('zeromq');

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

        await this.mainWindow.loadFile('Frontend/index.html');
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

        this.calibrationWindow.loadFile('Frontend/calibration.html');

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
                    } else if (response.type === 'frame' && this.frameStreamWindow) {
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

        await this.frameStreamWindow.loadFile('Frontend/frameStream.html');

        this.frameStreamWindow.on('closed', async () => {
            await this.sendToPython('stop_camera_view');
            this.frameStreamWindow = null;
        });
    }
}

// Initialize the application
const appManager = new ApplicationManager();