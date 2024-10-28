class Dashboard {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Control buttons
        const controlButtons = document.querySelectorAll('.control-buttons button');
        controlButtons.forEach(button => {
            button.addEventListener('click', this.handleControlButton.bind(this));
        });

        // Start button
        const startButton = document.querySelector('.start-btn');
        if (startButton) {
            startButton.addEventListener('click', this.handleStart.bind(this));
        }

        // Nav tabs
        const navTabs = document.querySelectorAll('.nav-tabs a');
        navTabs.forEach(tab => {
            tab.addEventListener('click', this.handleTabClick.bind(this));
        });
    }

    handleControlButton(event) {
        // Implementar lógica para los controles de reproducción
        console.log('Control button clicked:', event.target.textContent);
    }

    handleStart(event) {
        // Implementar lógica para el botón de inicio
        console.log('Start button clicked');
    }

    handleTabClick(event) {
        event.preventDefault();
        // Remover clase active de todos los tabs
        document.querySelectorAll('.nav-tabs a').forEach(tab => {
            tab.classList.remove('active');
        });
        // Agregar clase active al tab clickeado
        event.target.classList.add('active');
    }
}

// Inicializar dashboard cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});