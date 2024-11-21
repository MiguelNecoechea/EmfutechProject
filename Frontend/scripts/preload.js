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
        ipcRenderer.invoke('get-experiments'),
    saveParticipant: (data) =>
        ipcRenderer.invoke('save-participant', data),
    updateParticipantCount: (data) =>
        ipcRenderer.send('update-participant-count', data),
    onParticipantUpdate: (callback) =>
        ipcRenderer.on('participant-update', (_event, data) => callback(data)),
    openParticipantWindow: (experimentId) =>
        ipcRenderer.send('open-participant-window', experimentId),
    getParticipants: (experimentId) =>
        ipcRenderer.invoke('get-participants', experimentId),
    onExperimentUpdate: (callback) =>
        ipcRenderer.on('experiment-update', (_event, data) => callback(data)),
    focusWindow: () => 
        ipcRenderer.send('focus-window'),
    getExperiment: (experimentId) =>
        ipcRenderer.invoke('get-experiment', experimentId),
    showContextMenu: (menuType, experimentId) =>
        ipcRenderer.invoke('show-context-menu', menuType, experimentId),
    onMenuAction: (callback) =>
        ipcRenderer.on('menu-action', (_event, action, ...args) => callback(action, ...args)),
    onCloseFrameStream: (callback) =>
        ipcRenderer.on('close-frame-stream', (_event) => callback()),
    onCameraClosed: (callback) =>
        ipcRenderer.on('camera-closed', (_event) => callback()),
    deleteExperiment: (experimentId) =>
        ipcRenderer.invoke('delete-experiment', experimentId),
    deleteParticipant: (participantId) =>
        ipcRenderer.invoke('delete-participant', participantId),
});
