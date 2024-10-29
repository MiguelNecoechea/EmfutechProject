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
        this.currentPointIndex = 0;
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.startButton.addEventListener('click', () => {
            this.startButton.style.display = 'none';
            if (remote) {
                const win = remote.getCurrentWindow();
                win.setFullScreen(true)
                    .then(() => this.initializeCalibration())
                    .catch(() => {
                        document.documentElement.requestFullscreen()
                            .then(() => this.initializeCalibration())
                            .catch(err => console.error(err));
                    });
            } else {
                document.documentElement.requestFullscreen()
                    .then(() => this.initializeCalibration())
                    .catch(err => console.error(err));
            }
        });
    }

    generateCalibrationPoints() {
        const padding = 50;
        const width = window.innerWidth;
        const height = window.innerHeight;

        return [
            { x: padding, y: padding },                    // Esquina superior izquierda
            { x: width - padding, y: padding },            // Esquina superior derecha
            { x: width/2, y: height/2 },                   // Centro
            { x: padding, y: height - padding },           // Esquina inferior izquierda
            { x: width - padding, y: height - padding }    // Esquina inferior derecha
        ];
    }

    initializeCalibration() {
        const calibrationPoints = this.generateCalibrationPoints();
        this.points = calibrationPoints.map(pos => this.createPoint(pos.x, pos.y));
        this.showNextPoint();
    }

    createPoint(x, y) {
        const point = document.createElement('div');
        point.className = 'calibration-point';
        point.style.left = `${x}px`;
        point.style.top = `${y}px`;
        point.style.display = 'none';
        this.calibrationArea.appendChild(point);
        
        // Enviar coordenadas a Python
        eel.get_coordinates(Math.round(x), Math.round(y))();
        return point;
    }

    showNextPoint() {
        if (this.currentPointIndex > 0) {
            this.points[this.currentPointIndex - 1].style.display = 'none';
        }

        if (this.currentPointIndex < this.points.length) {
            this.points[this.currentPointIndex].style.display = 'block';
            this.currentPointIndex++;
            setTimeout(() => this.showNextPoint(), 2000);
        } else {
            this.finishCalibration();
        }
    }

    finishCalibration() {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        }
        if (remote) {
            const win = remote.getCurrentWindow();
            win.setFullScreen(false);
        }
        setTimeout(() => {
            this.reset();
        }, 1000);
    }

    reset() {
        this.points.forEach(point => point.remove());
        this.points = [];
        this.currentPointIndex = 0;
        this.startButton.style.display = 'block';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new EyeTrackingCalibration();
});