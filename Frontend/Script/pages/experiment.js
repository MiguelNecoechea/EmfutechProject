class ExperimentManager {
    constructor() {
        this.initializeForm();
        this.attachEventListeners();
    }

    initializeForm() {
        // Inicializar selectores y campos del formulario
        this.form = document.querySelector('.experiment-form');
        this.signalTypes = document.querySelectorAll('.signal-types input[type="checkbox"]');
    }

    attachEventListeners() {
        // Event listeners para los tabs de navegación
        const navTabs = document.querySelectorAll('.nav-tabs a');
        navTabs.forEach(tab => {
            tab.addEventListener('click', this.handleTabClick.bind(this));
        });

        // Event listener para el formulario
        if (this.form) {
            this.form.addEventListener('submit', this.handleFormSubmit.bind(this));
        }

        // Event listeners para los checkboxes de tipos de señales
        this.signalTypes.forEach(checkbox => {
            checkbox.addEventListener('change', this.handleSignalTypeChange.bind(this));
        });

        // Event listeners para los selectores
        document.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', this.handleSelectChange.bind(this));
        });
    }

    handleTabClick(event) {
        event.preventDefault();
        const tabs = document.querySelectorAll('.nav-tabs a');
        tabs.forEach(tab => tab.classList.remove('active'));
        event.target.classList.add('active');
    }

    handleFormSubmit(event) {
        event.preventDefault();
        // Recopilar datos del formulario
        const formData = new FormData(this.form);
        console.log('Form submitted:', Object.fromEntries(formData));
    }

    handleSignalTypeChange(event) {
        const signalType = event.target.nextSibling.textContent.trim();
        console.log(`Signal type ${signalType} ${event.target.checked ? 'selected' : 'unselected'}`);
        this.updateSignalPreview();
    }

    handleSelectChange(event) {
        const selectId = event.target.id;
        const selectedValue = event.target.value;
        console.log(`${selectId} changed to: ${selectedValue}`);
    }

    updateSignalPreview() {
        // Actualizar la vista previa de señales basado en las selecciones
        const preview = document.querySelector('.signal-preview');
        const selectedSignals = Array.from(this.signalTypes)
            .filter(checkbox => checkbox.checked)
            .map(checkbox => checkbox.nextSibling.textContent.trim());
        
        if (preview) {
            preview.innerHTML = `
                <h3>Sign:</h3>
                <div class="selected-signals">
                    ${selectedSignals.join(', ') || 'No signals selected'}
                </div>
            `;
        }
    }
}

// Inicializar el gestor de experimentos cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new ExperimentManager();
});