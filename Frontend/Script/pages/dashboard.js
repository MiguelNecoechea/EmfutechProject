class Dashboard {
    constructor() {
        this.isRecording = false; // Variable para alternar entre iniciar y detener grabación
        this.initializeEventListeners();
        this.initializeCharts(); // Inicializa los gráficos de señales
        this.initializeCameraFeed(); // Inicializa el feed de la cámara
    }

    initializeEventListeners() {
        // Configurar los eventos de navegación para la barra lateral
        const navLinks = document.querySelectorAll('.sidebar-nav a');

        navLinks.forEach(link => {
            link.addEventListener('click', event => {
                event.preventDefault();
                const pagePath = link.getAttribute('data-path');
                if (pagePath) {
                    this.loadPage(pagePath);
                }
            });
        });

        // Botones de control
        const controlButtons = document.querySelectorAll('.control-buttons button');
        controlButtons.forEach(button => {
            button.addEventListener('click', this.handleControlButton.bind(this));
        });

        // Botón de inicio (Start)
        const startButton = document.querySelector('.start-btn');
        if (startButton) {
            startButton.addEventListener('click', this.toggleScreenRecording.bind(this));
        }
    }

    loadPage(pagePath) {
        // Llama a Electron para cargar la página en la misma ventana
        window.electronAPI.loadPage(pagePath);
    }

    initializeCharts() {
        // Configura los gráficos de las señales (e.g., EEG, Eye Tracking, Emotions)
        const eegCanvas = document.getElementById('eegChart');
        const eyeTrackingCanvas = document.getElementById('eyeTrackingChart');
        const emotionCanvas = document.getElementById('emotionChart');

        if (eegCanvas) {
            this.eegChart = new Chart(eegCanvas, {
                type: 'line',
                data: {
                    labels: [], // Etiquetas de tiempo
                    datasets: [{
                        label: 'EEG Signals',
                        data: [], // Datos de señal EEG
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        x: { display: true },
                        y: { display: true }
                    }
                }
            });
        }

        if (eyeTrackingCanvas) {
            this.eyeTrackingChart = new Chart(eyeTrackingCanvas, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Eye Tracking',
                        data: [],
                        borderColor: 'rgba(153, 102, 255, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        x: { display: true },
                        y: { display: true }
                    }
                }
            });
        }

        if (emotionCanvas) {
            this.emotionChart = new Chart(emotionCanvas, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Emotion Signals',
                        data: [],
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        x: { display: true },
                        y: { display: true }
                    }
                }
            });
        }
    }
/*
    initializeCameraFeed() {
        const cameraStream = document.getElementById('cameraStream');

        // Verifica si el navegador soporta la API de getUserMedia
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(stream => {
                    cameraStream.srcObject = stream;
                })
                .catch(error => {
                    console.error("Error al acceder a la cámara: ", error);
                });
        } else {
            console.error("getUserMedia no es compatible con este navegador.");
        }
    }
*/
    handleControlButton(event) {
        console.log('Botón de control presionado:', event.target.textContent);
    }

    async toggleScreenRecording() {
        if (!this.isRecording) {
            console.log('Iniciando grabación de pantalla...');
            try {
                await window.electronAPI.startRecording();
                this.isRecording = true;
            } catch (error) {
                console.error('Error al iniciar la grabación de pantalla:', error);
            }
        } else {
            console.log('Deteniendo grabación de pantalla...');
            try {
                await window.electronAPI.stopRecording();
                this.isRecording = false;
            } catch (error) {
                console.error('Error al detener la grabación de pantalla:', error);
            }
        }
    }

    updateCharts(data) {
        // Actualizar gráficos con nuevos datos
        if (this.eegChart) {
            this.eegChart.data.labels.push(data.time);
            this.eegChart.data.datasets[0].data.push(data.eegSignal);
            this.eegChart.update();
        }

        if (this.eyeTrackingChart) {
            this.eyeTrackingChart.data.labels.push(data.time);
            this.eyeTrackingChart.data.datasets[0].data.push(data.eyeTrackingSignal);
            this.eyeTrackingChart.update();
        }

        if (this.emotionChart) {
            this.emotionChart.data.labels.push(data.time);
            this.emotionChart.data.datasets[0].data.push(data.emotionSignal);
            this.emotionChart.update();
        }
    }
}

// Inicializar dashboard cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});
