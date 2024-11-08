const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs').promises;
const { spawn } = require('child_process');
const eel = require('eel-electron');
require('@electron/remote/main').initialize();

let pythonProcess = null;
let mainWindow = null;
let screenRecorderProcess = null;

function startPythonServer() {
    console.log('Starting Python server...');
    const pythonPath = process.platform === 'win32' ? '.\\venv\\Scripts\\python.exe' : './venv/bin/python';
    
    pythonProcess = spawn(pythonPath, ['Backend/EyesTracking/calibrateEyeGaze.py'], {
        stdio: 'pipe',
        env: { 
            ...process.env, 
            PYTHONPATH: path.join(__dirname),
            PYTHONUNBUFFERED: '1'
        }
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python stdout: ${data.toString()}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python stderr: ${data.toString()}`);
    });

    pythonProcess.on('error', (err) => {
        console.error('Error starting Python server:', err);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python server exited with code ${code}`);
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            enableRemoteModule: true,
            preload: path.join(__dirname, 'Frontend', 'Script', 'global', 'preload.js')
        }
    });

    require('@electron/remote/main').enable(mainWindow.webContents);

    mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
        callback({
            responseHeaders: {
                ...details.responseHeaders,
                'Content-Security-Policy': [
                    "default-src 'self' 'unsafe-inline' 'unsafe-eval'",
                    "connect-src 'self' http://localhost:8000",
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval'"
                ].join('; ')
            }
        });
    });

    // Iniciar con index.html en lugar de la página de calibración
    mainWindow.loadFile('index.html');

    // Monitorear errores de carga
    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
        console.error('Failed to load:', errorCode, errorDescription);
    });

    if (process.env.NODE_ENV === 'development') {
        mainWindow.webContents.openDevTools();
    }
}

// IPC handlers
ipcMain.handle('load-page', async (event, pagePath) => {
    try {
        const fullPath = path.join(__dirname, 'Frontend', 'Templates', pagePath);
        console.log('Loading page:', fullPath);
        
        // Verificar que el archivo existe antes de cargarlo
        await fs.access(fullPath);
        
        await mainWindow.loadFile(fullPath);
        return { success: true };
    } catch (error) {
        console.error('Error loading page:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('calibration-complete', async () => {
    try {
        if (mainWindow) {
            const dashboardPath = path.join(__dirname, 'Frontend', 'Templates', 'Dashboard', 'dashboard.html');
            await mainWindow.loadFile(dashboardPath);
        }
        return { success: true };
    } catch (error) {
        console.error('Error completing calibration:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('start-calibration', async () => {
    console.log('Starting calibration...');
    return { success: true };
});

ipcMain.handle('start-recording', async () => {
    console.log('Starting recording...');
    try {
        // Implementar lógica de inicio de grabación
        return { success: true };
    } catch (error) {
        console.error('Error starting recording:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('stop-recording', async () => {
    console.log('Stopping recording...');
    try {
        // Implementar lógica de detención de grabación
        return { success: true };
    } catch (error) {
        console.error('Error stopping recording:', error);
        return { success: false, error: error.message };
    }
});

// Manejador para abrir ventana de calibración
ipcMain.on('open-calibration-window', () => {
    console.log('Request to open calibration window received');
    if (mainWindow) {
        const calibrationPath = path.join(__dirname, 'Frontend', 'Templates', 'EyesTracking', 'index.html');
        mainWindow.loadFile(calibrationPath)
            .catch(error => console.error('Error loading calibration window:', error));
    }
});

function cleanupProcesses() {
    if (pythonProcess) {
        pythonProcess.kill();
        pythonProcess = null;
    }
    if (screenRecorderProcess) {
        screenRecorderProcess.kill();
        screenRecorderProcess = null;
    }
}

// Initialize the application
app.whenReady().then(() => {
    try {
        startPythonServer();
        createWindow();
    } catch (error) {
        console.error('Error initializing application:', error);
        app.quit();
    }
});

app.on('window-all-closed', () => {
    cleanupProcesses();
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

app.on('before-quit', () => {
    cleanupProcesses();
});

process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
    cleanupProcesses();
    app.quit();
});

process.on('unhandledRejection', (error) => {
    console.error('Unhandled Rejection:', error);
    cleanupProcesses();
    app.quit();
});