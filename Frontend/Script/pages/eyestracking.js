class EyeTrackingCalibration {
    constructor() {
        this.calibrationArea = document.getElementById('calibrationArea');
        this.startButton = document.getElementById('startButton');
        this.points = [];
        this.currentPointIndex = 0;
        this.coordinateLog = [];
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.startButton.addEventListener('click', () => {
            document.documentElement.requestFullscreen();
            this.startButton.style.display = 'none';
            this.initializeCalibration();
        });
    }

    generateCalibrationPoints() {
        const padding = 50;
        const width = window.innerWidth;
        const height = window.innerHeight;

        const keyPoints = [
            { x: padding, y: padding },                    // Esquina superior izquierda
            { x: width - padding, y: padding },            // Esquina superior derecha
            { x: width/2, y: height/2 },                   // Centro
            { x: padding, y: height - padding },           // Esquina inferior izquierda
            { x: width - padding, y: height - padding },   // Esquina inferior derecha
        ];

        const randomPoints = [];
        for (let i = 0; i < 4; i++) {
            randomPoints.push({
                x: Math.floor(Math.random() * (width - 2 * padding)) + padding,
                y: Math.floor(Math.random() * (height - 2 * padding)) + padding
            });
        }

        const allPoints = [...keyPoints, ...randomPoints];
        const firstPoint = keyPoints[Math.floor(Math.random() * 4)];
        const centerPoint = keyPoints[2];
        const remainingPoints = allPoints.filter(p => 
            p !== firstPoint && p !== centerPoint
        );

        for (let i = remainingPoints.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [remainingPoints[i], remainingPoints[j]] = [remainingPoints[j], remainingPoints[i]];
        }

        return [firstPoint, ...remainingPoints, centerPoint];
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
        
        this.logCoordinates(x, y, this.currentPointIndex + 1);
        return point;
    }

    logCoordinates(x, y, pointNumber) {
        const coordinates = {
            pointNumber: pointNumber,
            x: Math.round(x),
            y: Math.round(y),
            timestamp: new Date().toISOString()
        };
        this.coordinateLog.push(coordinates);

        // Enviar al servidor en tiempo real
        fetch('http://localhost:5000/log-point', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(coordinates)
        });

        // Mostrar en consola del navegador
        console.log(`Punto ${pointNumber}: X=${Math.round(x)}px, Y=${Math.round(y)}px`);
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
        // Enviar datos completos al servidor
        fetch('http://localhost:5000/save-calibration', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(this.coordinateLog)
        })
        .then(response => response.json())
        .then(data => {
            console.log('=== Calibración Completada ===');
            console.log(`Datos guardados en: ${data.filename}`);
            console.table(this.coordinateLog);
            
            setTimeout(() => {
                document.exitFullscreen();
                this.reset();
            }, 1000);
        })
        .catch(error => {
            console.error('Error al guardar los datos:', error);
            setTimeout(() => {
                document.exitFullscreen();
                this.reset();
            }, 1000);
        });
    }

    reset() {
        this.points.forEach(point => point.remove());
        this.points = [];
        this.currentPointIndex = 0;
        this.coordinateLog = [];
        this.startButton.style.display = 'block';
    }
}

window.addEventListener('load', () => new EyeTrackingCalibration());