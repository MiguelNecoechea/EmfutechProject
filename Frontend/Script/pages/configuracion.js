class ConfigurationManager {
    constructor() {
        this.initializeComponents();
        this.attachEventListeners();
    }

    initializeComponents() {
        this.deviceCheckboxes = document.querySelectorAll('.device-option input');
        this.filters = document.querySelectorAll('.filter-select');
        this.settingSelects = document.querySelectorAll('.setting-select');
        this.optionButtons = document.querySelectorAll('.option-btn');
    }

    attachEventListeners() {
        // Event listeners para dispositivos
        this.deviceCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', this.handleDeviceSelection.bind(this));
        });

        // Event listeners para filtros
        this.filters.forEach(filter => {
            filter.addEventListener('change', this.handleFilterChange.bind(this));
        });

        // Event listeners para configuraciones
        this.settingSelects.forEach(select => {
            select.addEventListener('change', this.handleSettingChange.bind(this));
        });

        // Event listeners para botones de opciones
        this.optionButtons.forEach(button => {
            button.addEventListener('click', this.handleOptionClick.bind(this));
        });
    }

    handleDeviceSelection(event) {
        const device = event.target.value;
        const isSelected = event.target.checked;
        console.log(`Device ${device} ${isSelected ? 'selected' : 'unselected'}`);
        this.updateDeviceSettings(device, isSelected);
    }

    handleFilterChange(event) {
        const filterType = event.target.options[0].text;
        const selectedValue = event.target.value;
        console.log(`Filter ${filterType} changed to: ${selectedValue}`);
        this.updateConfiguration();
    }

    handleSettingChange(event) {
        const settingType = event.target.previousElementSibling.textContent;
        const selectedValue = event.target.value;
        console.log(`Setting ${settingType} changed to: ${selectedValue}`);
        this.updateConfiguration();
    }

    handleOptionClick(event) {
        const option = event.target.textContent;
        switch(option) {
            case 'Assign Groups':
                this.handleGroupAssignment();
                break;
            case 'Segmentation':
                this.handleSegmentation();
                break;
            case 'Group Editing':
                this.handleGroupEditing();
                break;
        }
    }

    updateDeviceSettings(device, isEnabled) {
        // Actualizar configuraciones específicas del dispositivo
        console.log(`Updating settings for ${device}`);
    }

    updateConfiguration() {
        // Actualizar la configuración general
        this.updateDashboard();
        this.updateProgress();
        this.updateResults();
    }

    updateDashboard() {
        // Actualizar dashboard
        console.log('Updating dashboard');
    }

    updateProgress() {
        // Actualizar progreso
        console.log('Updating progress');
    }

    updateResults() {
        // Actualizar resultados
        console.log('Updating results');
    }

    handleGroupAssignment() {
        console.log('Opening group assignment interface');
    }

    handleSegmentation() {
        console.log('Opening segmentation interface');
    }

    handleGroupEditing() {
        console.log('Opening group editing interface');
    }
}

// Inicializar el gestor de configuración cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new ConfigurationManager();
});