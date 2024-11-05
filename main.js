const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
require('@electron/remote/main').initialize();

let pythonProcess = null;
let mainWindow = null;
let screenRecorderProcess = null; // Variable para manejar el proceso de grabación de pantalla

function startPythonServer() {
    console.log('Iniciando servidor Python...');
    pythonProcess = spawn('python', ['Backend/EyesTracking/calibrateEyeGaze.py'], {
        stdio: 'inherit',
        env: { ...process.env, PYTHONPATH: path.join(__dirname) } // Agregar PYTHONPATH al entorno
    });

    pythonProcess.on('error', (err) => {
        console.error('Error al iniciar Python:', err);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Servidor Python cerrado con código ${code}`);
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: true,
            enableRemoteModule: true,
            preload: path.join(__dirname, 'Frontend', 'Script', 'global', 'preload.js') // Ruta correcta para preload.js
        }
    });

    require('@electron/remote/main').enable(mainWindow.webContents);

    mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
        callback({
            responseHeaders: {
                ...details.responseHeaders,
                'Content-Security-Policy': ['default-src \'self\' \'unsafe-inline\' \'unsafe-eval\'']
            }
        });
    });

    mainWindow.loadFile(path.join(__dirname, 'Frontend', 'Templates', 'Dashboard', 'dashboard.html'));
    mainWindow.webContents.openDevTools();
}

// Handlers para controlar la grabación de pantalla
ipcMain.handle('start-recording', async () => {
    if (!screenRecorderProcess) {
        screenRecorderProcess = spawn('python', ['./IO/ScreenRecording/WindowsScreenRecorder.py'], {
            env: { ...process.env, PYTHONIOENCODING: 'utf-8' } // Configuración de entorno UTF-8
        });
        console.log('Grabacion de pantalla iniciada');

        screenRecorderProcess.stdout.on('data', (data) => {
            console.log(`Salida de grabacion: ${data}`);
        }); 

        screenRecorderProcess.stderr.on('data', (data) => {
            console.error(`Error de grabacion: ${data}`);
        });

        screenRecorderProcess.on('close', (code) => {
            console.log(`Grabacion de pantalla detenida con codigo ${code}`);
            screenRecorderProcess = null; // Resetear el proceso cuando se detiene
        });
    }
});


ipcMain.handle('stop-recording', async () => {
    if (screenRecorderProcess) {
        screenRecorderProcess.kill(); // Detener el proceso de grabación
        console.log('Grabación de pantalla detenida');
        screenRecorderProcess = null;
    }
});

app.whenReady().then(() => {
    startPythonServer();
    createWindow();
});

app.on('window-all-closed', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    if (screenRecorderProcess) {
        screenRecorderProcess.kill();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
