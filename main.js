const { app, BrowserWindow } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
require('@electron/remote/main').initialize()

let pythonProcess = null

function startPythonServer() {
    console.log('Iniciando servidor Python...');
    pythonProcess = spawn('python', ['Backend/EyesTracking/calibrateEyeGaze.py'], {
        stdio: 'inherit'
    });

    pythonProcess.on('error', (err) => {
        console.error('Error al iniciar Python:', err);
    });

    pythonProcess.on('close', (code) => {
        eel.stop_eye_gaze()();
        console.log(`Servidor Python cerrado con código ${code}`);
    });
}

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true,
            webSecurity: false // Solo para desarrollo
        }
    })

    require('@electron/remote/main').enable(win.webContents)
    
    // Para desarrollo
    win.webContents.session.webRequest.onHeadersReceived((details, callback) => {
        callback({
            responseHeaders: {
                ...details.responseHeaders,
                'Content-Security-Policy': ['default-src \'self\' \'unsafe-inline\' \'unsafe-eval\'']
            }
        })
    });

    // Esperar un momento para que el servidor Eel esté listo
    setTimeout(() => {
        win.loadURL('http://localhost:8000/Templates/EyesTracking/index.html')
        win.webContents.openDevTools()
    }, 4000)
}

app.whenReady().then(() => {
    startPythonServer()
    createWindow()
})

app.on('window-all-closed', () => {
    if (pythonProcess) {
        pythonProcess.kill()
    }
    if (process.platform !== 'darwin') {
        app.quit()
    }
})