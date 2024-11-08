/*
let remote;
try {
    remote = require('@electron/remote');
} catch (e) {
    console.warn('Error loading remote:', e);
}

class EyeTrackingCalibration {
    constructor() {
        this.calibrationArea = document.getElementById('calibrationArea');
        this.startButton = document.getElementById('startButton');
        this.points = [];
        this.currentX = 0;
        this.currentY = 0;
        this.currentPointIndex = 0;
        this.calibrationPoints = [];
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.startButton.addEventListener('click', async () => {
            this.startButton.style.display = 'none';
            try {
                if (remote) {
                    const win = remote.getCurrentWindow();
                    await win.setFullScreen(true);
                } else {
                    await document.documentElement.requestFullscreen();
                }
                // Iniciar la calibración después de entrar en pantalla completa
                setTimeout(() => this.initializeCalibration(), 500);
            } catch (err) {
                console.error('Error starting calibration:', err);
            }
        });
    }

    generateCalibrationPoints() {
        const padding = 10;
        const width = window.innerWidth;
        const height = window.innerHeight;
        return [
            { x: padding, y: padding },
            { x: width / 2, y: padding },
            { x: width - padding, y: padding },
            { x: padding, y: height / 2 },
            { x: width / 2, y: height / 2 },
            { x: width - padding, y: height / 2 },
            { x: padding, y: height - padding },
            { x: width / 2, y: height - padding },
            { x: width - padding, y: height - padding }
        ];
    }

    initializeCalibration() {
        this.calibrationPoints = this.generateCalibrationPoints();
        this.points = this.calibrationPoints.map(pos => this.createPoint(pos.x, pos.y));
        this.showNextPoint();
    }

    createPoint(x, y) {
        const point = document.createElement('div');
        point.className = 'calibration-point';
        point.style.left = `${x}px`;
        point.style.top = `${y}px`;
        point.style.display = 'none';
        point.dataset.x = x;
        point.dataset.y = y;
        this.calibrationArea.appendChild(point);
        return point;
    }

    async showNextPoint() {
        if (this.currentPointIndex > 0) {
            this.points[this.currentPointIndex - 1].style.display = 'none';
        }

        if (this.currentPointIndex < this.points.length) {
            const currentPoint = this.points[this.currentPointIndex];
            currentPoint.style.display = 'block';
            this.currentX = parseInt(currentPoint.dataset.x);
            this.currentY = parseInt(currentPoint.dataset.y);
            
            try {
                await eel.set_coordinates(this.currentX, this.currentY)();
            } catch (error) {
                console.warn('Error setting coordinates:', error);
            }
            
            this.currentPointIndex++;
            setTimeout(() => this.showNextPoint(), 6000);
        } else {
            await this.finishCalibration();
        }
    }

    // En tu función finishCalibration o donde estés enviando el evento
async finishCalibration() {
    try {
        if (document.fullscreenElement) {
            await document.exitFullscreen();
        }

        // Si estás usando send
        if (window.electron) {
            window.electron.send('calibration-complete', {
                status: 'success',
                timestamp: new Date().toISOString()
            });
        }
        
        // O si estás usando invoke
        if (window.electron && window.electron.invoke) {
            await window.electron.invoke('calibration-complete', {
                status: 'success',
                timestamp: new Date().toISOString()
            });
        }

        // Como fallback, usar navegación directa
        else {
            window.location.href = '../Dashboard/dashboard.html';
        }
    } catch (error) {
        console.error('Error en finishCalibration:', error);
    }
}

    reset() {
        this.points.forEach(point => point.remove());
        this.points = [];
        this.currentPointIndex = 0;
        this.startButton.style.display = 'block';
    }
}

// Iniciar el eye tracking cuando se carga el DOM
document.addEventListener('DOMContentLoaded', async () => {
    const calibration = new EyeTrackingCalibration();
    
    try {
        await eel.start_eye_gaze()();
        await eel.start_recording()();
    } catch (error) {
        console.warn('Error starting eye tracking:', error);
    }
});
*/

let remote;
try {
    remote = require('@electron/remote');
} catch (e) {
    console.warn('Error loading remote:', e);
}

class EyeTrackingCalibration {
    constructor() {
        this.calibrationArea = document.getElementById('calibrationArea');
        this.startButton = document.getElementById('startButton');
        this.points = [];
        this.currentX = 0;
        this.currentY = 0;
        this.currentPointIndex = 0;
        this.calibrationPoints = [];
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.startButton.addEventListener('click', async () => {
            this.startButton.style.display = 'none';
            try {
                if (remote) {
                    const win = remote.getCurrentWindow();
                    await win.setFullScreen(true);
                } else {
                    await document.documentElement.requestFullscreen();
                }
                // Iniciar la calibración después de entrar en pantalla completa
                setTimeout(() => this.initializeCalibration(), 500);
            } catch (err) {
                console.error('Error starting calibration:', err);
            }
        });
    }

    generateCalibrationPoints() {
        const padding = 10;
        const width = window.innerWidth;
        const height = window.innerHeight;
        return [
            { x: padding, y: padding },
            { x: width / 2, y: padding },
            { x: width - padding, y: padding },
            { x: padding, y: height / 2 },
            { x: width / 2, y: height / 2 },
            { x: width - padding, y: height / 2 },
            { x: padding, y: height - padding },
            { x: width / 2, y: height - padding },
            { x: width - padding, y: height - padding }
        ];
    }

    initializeCalibration() {
        this.calibrationPoints = this.generateCalibrationPoints();
        this.points = this.calibrationPoints.map(pos => this.createPoint(pos.x, pos.y));
        this.showNextPoint();
    }

    createPoint(x, y) {
        const point = document.createElement('div');
        point.className = 'calibration-point';
        point.style.left = `${x}px`;
        point.style.top = `${y}px`;
        point.style.display = 'none';
        point.dataset.x = x;
        point.dataset.y = y;
        this.calibrationArea.appendChild(point);
        return point;
    }

    async showNextPoint() {
        if (this.currentPointIndex > 0) {
            this.points[this.currentPointIndex - 1].style.display = 'none';
        }

        if (this.currentPointIndex < this.points.length) {
            const currentPoint = this.points[this.currentPointIndex];
            currentPoint.style.display = 'block';
            this.currentX = parseInt(currentPoint.dataset.x);
            this.currentY = parseInt(currentPoint.dataset.y);
            
            try {
                await eel.set_coordinates(this.currentX, this.currentY)();
            } catch (error) {
                console.warn('Error setting coordinates:', error);
            }
            
            this.currentPointIndex++;
            setTimeout(() => this.showNextPoint(), 6000);
        } else {
            await this.finishCalibration();
        }
    }

    async finishCalibration() {
        try {
            if (document.fullscreenElement) {
                await document.exitFullscreen();
            }
            if (remote) {
                const win = remote.getCurrentWindow();
                win.setFullScreen(false);
            }

            // Solo detener la grabación, mantener el eye tracking activo
            try {
                await eel.stop_recording()();
                // Removido stop_eye_gaze para mantener el tracking activo
            } catch (error) {
                console.warn('Error stopping recording:', error);
            }

            // Notificar que la calibración ha terminado para cargar el dashboard
            await window.electronAPI.finishCalibration();
        } catch (error) {
            console.error('Error finishing calibration:', error);
        }
    }

    reset() {
        this.points.forEach(point => point.remove());
        this.points = [];
        this.currentPointIndex = 0;
        this.startButton.style.display = 'block';
    }
}

// Iniciar el eye tracking cuando se carga el DOM
document.addEventListener('DOMContentLoaded', async () => {
    const calibration = new EyeTrackingCalibration();
    
    try {
        await eel.start_eye_gaze()();
        await eel.start_recording()();
    } catch (error) {
        console.warn('Error starting eye tracking:', error);
    }
});