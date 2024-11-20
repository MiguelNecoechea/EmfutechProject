const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    sendPythonCommand: (command, params) =>
        ipcRenderer.invoke('python-command', command, params),
    onPythonMessage: (callback) =>
        ipcRenderer.on('python-message', (_event, data) => callback(data)),
    onFrameData: (callback) =>
        ipcRenderer.on('frame-data', (_event, data) => callback(data)),
    openCalibrationWindow: () => 
        ipcRenderer.send('open-calibration-window'),
    openDirectory: () => 
        ipcRenderer.invoke('open-directory'),
    generateReport: () => 
        ipcRenderer.invoke('generate-report'),
    minimize: () => 
        ipcRenderer.send('minimize-window'),
    viewCamera: () => 
        ipcRenderer.send('view-camera'),
    closeFrameStream: () => 
        ipcRenderer.send('close-frame-stream'),
    openExperimentWindow: () => 
        ipcRenderer.send('open-experiment-window'),
    closeWindow: () => 
        ipcRenderer.send('close-window'),
    updateStudyPanel: (data) => 
        ipcRenderer.send('update-study-panel', data),
    onStudyPanelUpdate: (callback) =>
        ipcRenderer.on('study-panel-update', (_event, data) => callback(data)),
    saveExperiment: (data) =>
        ipcRenderer.invoke('save-experiment', data),
    getExperiments: () =>
        ipcRenderer.invoke('get-experiments')
});
