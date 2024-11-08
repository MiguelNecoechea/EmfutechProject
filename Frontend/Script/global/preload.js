const { contextBridge, ipcRenderer } = require('electron');

// Exponer APIs seguras para el proceso de renderizado
contextBridge.exposeInMainWorld('electronAPI', {
    // Funciones para navegación
    loadPage: (pagePath) => ipcRenderer.invoke('load-page', pagePath),
    
    // Funciones para calibración
    startCalibration: () => ipcRenderer.invoke('start-calibration'),
    calibrationComplete: () => ipcRenderer.invoke('calibration-complete'),
    openCalibrationWindow: () => ipcRenderer.send('open-calibration-window'),
    finishCalibration: () => ipcRenderer.invoke('calibration-complete'), // Añadida esta línea
    
    // Funciones para grabación
    startRecording: () => ipcRenderer.invoke('start-recording'),
    stopRecording: () => ipcRenderer.invoke('stop-recording'),
    
    // Funciones para experimentos
    saveExperiment: (data) => ipcRenderer.invoke('save-experiment', data),
    loadExperiments: () => ipcRenderer.invoke('load-experiments'),
    deleteExperiment: (fileName) => ipcRenderer.invoke('delete-experiment', fileName),
    startExperiment: () => ipcRenderer.invoke('start-experiment'),
    stopExperiment: () => ipcRenderer.invoke('stop-experiment'),
    
    // Funcionalidad general de IPC
    send: (channel, data) => {
        const validSendChannels = [
            'open-calibration-window',
            'calibration-complete', // Añadido este canal
            // Agrega aquí otros canales válidos para send
        ];
        if (validSendChannels.includes(channel)) {
            ipcRenderer.send(channel, data);
        }
    },
    
    invoke: (channel, data) => {
        const validChannels = [
            // Navegación
            'load-page',
            // Calibración
            'start-calibration',
            'calibration-complete',
            // Grabación
            'start-recording',
            'stop-recording',
            // Experimentos
            'save-experiment',
            'load-experiments',
            'delete-experiment',
            'start-experiment',
            'stop-experiment'
        ];
        
        if (validChannels.includes(channel)) {
            return ipcRenderer.invoke(channel, data);
        }
        
        return Promise.reject(new Error(`Canal IPC no permitido: ${channel}`));
    },

    // Manejadores de eventos
    on: (channel, callback) => {
        const validChannels = [
            'experiment-saved',
            'experiment-started',
            'experiment-stopped',
            'recording-started',
            'recording-stopped',
            'calibration-status',
            'calibration-complete' // Añadido este canal
        ];
        if (validChannels.includes(channel)) {
            ipcRenderer.on(channel, (event, ...args) => callback(...args));
        }
    },

    once: (channel, callback) => {
        const validChannels = [
            'experiment-saved',
            'experiment-started',
            'experiment-stopped',
            'calibration-complete' // Añadido este canal
        ];
        if (validChannels.includes(channel)) {
            ipcRenderer.once(channel, (event, ...args) => callback(...args));
        }
    }
});

// Opcional: Logging para desarrollo
if (process.env.NODE_ENV === 'development') {
    console.log('Preload script loaded');
    
    // Monitorear eventos IPC
    ipcRenderer.on('ipc-message', (event, ...args) => {
        console.log('IPC Message:', ...args);
    });
}