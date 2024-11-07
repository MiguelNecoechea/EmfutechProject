const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const zmq = require('zeromq');

class ApplicationManager {
    constructor() {
        this.pythonProcess = null;
        this.mainWindow = null;
        this.socket = null;
        this.isShuttingDown = false;
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
            height: 800,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js')
            }
        });

        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
        });

        await this.mainWindow.loadFile('Frontend/Templates/EyesTracking/index.html');
        this.mainWindow.webContents.openDevTools();
        // if (process.env.NODE_ENV === 'development') {
        //     this.mainWindow.webContents.openDevTools();
        // }
    }

    async startPythonBackend() {
        const scriptPath = path.join(__dirname, 'Backend', 'BackendServer.py');
        console.log('Starting Python backend:', scriptPath);

        this.pythonProcess = spawn('python', [scriptPath], {
            stdio: 'inherit',
            detached: false // Ensure the process is terminated with the parent
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
                if (this.isShuttingDown) break;

                const response = JSON.parse(msg.toString());
                if (this.mainWindow) {
                    this.mainWindow.webContents.send('python-message', response);
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

        // Send stop command to Python backend
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

        // Terminate Python process
        if (this.pythonProcess) {
            try {
                this.pythonProcess.kill('SIGTERM');
                // Wait for process to terminate
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

        // Close main window
        if (this.mainWindow) {
            this.mainWindow.destroy();
            this.mainWindow = null;
        }

        console.log('Cleanup completed');
    }

    async onWindowAllClosed() {
        await this.cleanup();
        if (process.platform !== 'darwin') {
            app.quit();
        }
    }

    onActivate() {
        if (!this.mainWindow) {
            this.createWindow();
        }
    }
}

// Initialize the application
const appManager = new ApplicationManager();