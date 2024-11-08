class MeasurementManager {
    constructor() {
        this.initializeComponents();
        this.attachEventListeners();
        this.monitoringActive = false;
        this.recordingTime = 0;
        this.statusLabel = document.querySelector('.status-label');
        this.recordingTimeLabel = document.querySelector('.status-value:nth-child(2)');
    }

    initializeComponents() {
        // Inicializar contenedores de los paneles de medición
        this.monitoringContainer = document.querySelector('.monitoring-content');
        this.eegContainer = document.querySelector('.eeg-content');
        this.eyeTrackingContainer = document.querySelector('.eye-tracking-content');
        this.emotionalContainer = document.querySelector('.emotional-content');
    }

    attachEventListeners() {
        // Event listeners para los tabs de navegación
        const navTabs = document.querySelectorAll('.nav-tabs a');
        navTabs.forEach(tab => {
            tab.addEventListener('click', this.handleTabClick.bind(this));
        });

        // Event listeners para los botones de la barra de herramientas
        const toolbarButtons = document.querySelectorAll('.toolbar-btn');
        toolbarButtons.forEach(button => {
            button.addEventListener('click', this.handleToolbarAction.bind(this));
        });
    }

    handleTabClick(event) {
        event.preventDefault();
        const tabs = document.querySelectorAll('.nav-tabs a');
        tabs.forEach(tab => tab.classList.remove('active'));
        event.target.classList.add('active');
        this.updateContent(event.target.textContent);
    }

    handleToolbarAction(event) {
        const action = event.target.textContent.trim().toLowerCase();
        switch (action) {
            case 'test':
                this.startTest();
                break;
            case 'record':
                this.toggleRecording();
                break;
            case 'data export':
                this.exportData();
                break;
            case 'report generation':
                this.generateReport();
                break;
            case 'configuration':
                this.showConfiguration();
                break;
        }
    }

    startTest() {
        console.log('Starting test...');
        // Implementar lógica de prueba
        alert("Test iniciado");
    }

    toggleRecording() {
        this.monitoringActive = !this.monitoringActive;
        if (this.monitoringActive) {
            this.statusLabel.textContent = 'Recording...';
            this.startMonitoring();
        } else {
            this.statusLabel.textContent = 'Stopped';
            this.stopMonitoring();
        }
    }

    startMonitoring() {
        console.log('Starting monitoring...');
        this.recordingTime = 0;
        this.updateRecordingTime();
        this.monitoringInterval = setInterval(() => {
            this.recordingTime++;
            this.updateRecordingTime();
            this.updateMonitoringDisplay();
        }, 1000);
    }

    stopMonitoring() {
        console.log('Stopping monitoring...');
        clearInterval(this.monitoringInterval);
        this.statusLabel.textContent = 'Ready';
    }

    updateRecordingTime() {
        const hours = String(Math.floor(this.recordingTime / 3600)).padStart(2, '0');
        const minutes = String(Math.floor((this.recordingTime % 3600) / 60)).padStart(2, '0');
        const seconds = String(this.recordingTime % 60).padStart(2, '0');
        this.recordingTimeLabel.textContent = `${hours}:${minutes}:${seconds}`;
    }

    exportData() {
        console.log('Exporting data...');
        alert("Data exportada correctamente");
        // Implementar exportación de datos
    }

    generateReport() {
        console.log('Generating report...');
        alert("Reporte generado");
        // Implementar generación de reportes
    }

    showConfiguration() {
        console.log('Showing configuration...');
        // Implementar visualización de configuración
        alert("Configuración mostrada");
    }

    updateContent(tabName) {
        console.log(`Switched to ${tabName} tab`);
        // Implementar lógica para actualizar contenido basado en el tab seleccionado
    }

    updateMonitoringDisplay() {
        // Actualizar visualizaciones en tiempo real en los paneles de medición
        this.monitoringContainer.innerHTML = `<div class="data-placeholder">Real-Time Data: ${new Date().toLocaleTimeString()}</div>`;
        this.eegContainer.innerHTML = `<div class="data-placeholder">EEG Data: ${Math.random().toFixed(2)}</div>`;
        this.eyeTrackingContainer.innerHTML = `<div class="data-placeholder">Eye Tracking: ${Math.random().toFixed(2)}</div>`;
        this.emotionalContainer.innerHTML = `<div class="data-placeholder">Emotional Response: ${Math.random().toFixed(2)}</div>`;
    }
}

// Inicializar el gestor de mediciones cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new MeasurementManager();
});
