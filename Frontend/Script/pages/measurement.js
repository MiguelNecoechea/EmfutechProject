document.addEventListener('DOMContentLoaded', function() {
    // Variables
    const tabButtons = document.querySelectorAll('.tab-btn');
    const actionButtons = document.querySelectorAll('.action-btn');
    const monitorPanels = document.querySelectorAll('.monitor-panel');
    let isRecording = false;

    // Tab Navigation
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            updateContent(button.textContent);
        });
    });

    // Action Button Handlers
    actionButtons.forEach(button => {
        if (button.textContent === 'Record') {
            button.addEventListener('click', toggleRecording);
        } else if (button.classList.contains('dropdown')) {
            button.addEventListener('click', handleDropdown);
        }
    });

    // Toggle Recording
    function toggleRecording() {
        isRecording = !isRecording;
        const recordButton = document.querySelector('.action-btn');
        recordButton.textContent = isRecording ? 'Stop' : 'Record';
        recordButton.style.color = isRecording ? '#ff0000' : '';
        
        if (isRecording) {
            startMonitoring();
        } else {
            stopMonitoring();
        }
    }

    // Handle Dropdowns
    function handleDropdown(e) {
        const button = e.target;
        // Aquí se implementaría la lógica del menú desplegable
        console.log(`Clicked: ${button.textContent.trim()}`);
    }

    // Update Content based on Tab
    function updateContent(tabName) {
        console.log(`Switched to ${tabName} tab`);
        // Aquí se implementaría la lógica para actualizar el contenido
    }

    // Monitoring Functions
    function startMonitoring() {
        monitorPanels.forEach(panel => {
            const type = panel.querySelector('h3').textContent;
            initializeMonitor(panel, type);
        });
    }

    function stopMonitoring() {
        monitorPanels.forEach(panel => {
            const content = panel.querySelector('.monitor-content');
            content.innerHTML = '';
        });
    }

    function initializeMonitor(panel, type) {
        const content = panel.querySelector('.monitor-content');
        
        // Simulación de datos en tiempo real
        if (isRecording) {
            setInterval(() => {
                if (!isRecording) return;
                
                // Aquí se implementaría la lógica real de monitoreo
                const timestamp = new Date().toLocaleTimeString();
                content.innerHTML += `<div>${timestamp}: ${type} data point</div>`;
                content.scrollTop = content.scrollHeight;
            }, 1000);
        }
    }

    // Inicialización
    function initialize() {
        // Configuración inicial de los paneles
        monitorPanels.forEach(panel => {
            const content = panel.querySelector('.monitor-content');
            content.innerHTML = 'Waiting to start...';
        });
    }

    initialize();


});

class MeasurementManager {
    constructor() {
        this.initializeComponents();
        this.attachEventListeners();
        this.monitoringActive = false;
    }

    initializeComponents() {
        // Inicializar componentes de medición
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
    }

    handleToolbarAction(event) {
        const action = event.target.textContent.toLowerCase();
        switch(action) {
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
    }

    toggleRecording() {
        this.monitoringActive = !this.monitoringActive;
        if (this.monitoringActive) {
            this.startMonitoring();
        } else {
            this.stopMonitoring();
        }
    }

    startMonitoring() {
        console.log('Starting monitoring...');
        // Implementar inicio de monitoreo
    }

    stopMonitoring() {
        console.log('Stopping monitoring...');
        // Implementar detención de monitoreo
    }

    exportData() {
        console.log('Exporting data...');
        // Implementar exportación de datos
    }

    generateReport() {
        console.log('Generating report...');
        // Implementar generación de reportes
    }

    showConfiguration() {
        console.log('Showing configuration...');
        // Implementar visualización de configuración
    }

    updateMonitoringDisplay() {
        // Actualizar visualizaciones en tiempo real
    }
}

// Inicializar el gestor de mediciones cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new MeasurementManager();
});