// Configuración global de la aplicación
const App = {
    init() {
        this.setupTheme();
        this.setupGlobalEventListeners();
    },

    setupTheme() {
        // Implementar lógica para temas claros/oscuros si es necesario
    },

    setupGlobalEventListeners() {
        // Escuchadores de eventos globales
        document.addEventListener('click', (e) => {
            // Manejar clics globales si es necesario
        });
    }
};

// Inicializar la aplicación
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});