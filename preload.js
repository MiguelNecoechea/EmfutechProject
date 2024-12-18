const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld(
    'electronAPI', {
        sendPythonCommand: (command, params) =>
            ipcRenderer.invoke('python-command', command, params),
        onPythonMessage: (callback) =>
            ipcRenderer.on('python-message', (event, data) => callback(data)),
        openCalibrationWindow: () => ipcRenderer.send('open-calibration-window'),
        openDirectory: () => ipcRenderer.invoke('open-directory'),
        generateReport: () => ipcRenderer.invoke('generate-report')
    }
);
