class ExperimentManager {
    constructor() {
        this.initializeForm();
        this.attachEventListeners();
        this.loadFormData();
    }

    initializeForm() {
        this.form = document.querySelector('.experiment-form');
        this.signalTypes = document.querySelectorAll('.signal-types input[type="checkbox"]');

        // Campos del formulario
        this.experimentName = document.getElementById('experimentName');
        this.description = document.getElementById('description');
        this.objective = document.getElementById('objective');
        this.duration = document.getElementById('duration');
        this.participants = document.getElementById('participants');
        this.activeSensors = document.getElementById('activeSensors');
        this.stimulusConfig = document.getElementById('stimulusConfig');
        this.frequency = document.getElementById('frequency');
        this.conectAura = document.getElementById('connectAura');
        this.disconectAura = document.getElementById('disconnectAura');

        // Nuevos botones
        this.refreshChannels = document.getElementById('refreshChannels');
        this.removeSelectedChannels = document.getElementById('removeSelectedChannels');
        this.selectChannels = document.getElementById('selectChannels');
    }

    attachEventListeners() {
        const navTabs = document.querySelectorAll('.nav-tabs a');
        navTabs.forEach(tab => {
            tab.addEventListener('click', this.handleTabClick.bind(this));
        });

        if (this.form) {
            this.form.addEventListener('submit', this.handleFormSubmit.bind(this));
        }

        if (this.conectAura) {
            this.conectAura.addEventListener('click', () => {
                console.log('Aura conectado');
                alert('¡Aura conectado exitosamente!');
            });
        }

        if (this.disconectAura) {
            this.disconectAura.addEventListener('click', () => {
                console.log('Aura desconectado');
                alert('¡Aura desconectado exitosamente!');
            });
        }

        // Nuevos eventos para los botones añadidos
        if (this.refreshChannels) {
            this.refreshChannels.addEventListener('click', this.handleRefreshChannels.bind(this));
        }

        if (this.removeSelectedChannels) {
            this.removeSelectedChannels.addEventListener('click', this.handleRemoveSelectedChannels.bind(this));
        }

        if (this.selectChannels) {
            this.selectChannels.addEventListener('click', this.handleSelectChannels.bind(this));
        }

        this.signalTypes.forEach(checkbox => {
            checkbox.addEventListener('change', this.handleSignalTypeChange.bind(this));
        });

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
        this.saveFormData();
        alert('Experiment data saved successfully!');
    }

    saveFormData() {
        const formData = {
            experimentName: this.experimentName.value,
            description: this.description.value,
            objective: this.objective.value,
            duration: this.duration.value,
            participants: this.participants.value,
            activeSensors: this.activeSensors.value,
            stimulusConfig: this.stimulusConfig.value,
            frequency: this.frequency.value,
            signalTypes: Array.from(this.signalTypes).map(checkbox => ({
                type: checkbox.nextSibling.textContent.trim(),
                checked: checkbox.checked
            }))
        };

        localStorage.setItem('experimentFormData', JSON.stringify(formData));
    }

    loadFormData() {
        const savedData = localStorage.getItem('experimentFormData');

        if (savedData) {
            const formData = JSON.parse(savedData);

            this.experimentName.value = formData.experimentName || '';
            this.description.value = formData.description || '';
            this.objective.value = formData.objective || '';
            this.duration.value = formData.duration || '';
            this.participants.value = formData.participants || '';
            this.activeSensors.value = formData.activeSensors || '';
            this.stimulusConfig.value = formData.stimulusConfig || '';
            this.frequency.value = formData.frequency || '';

            this.signalTypes.forEach(checkbox => {
                const signalType = formData.signalTypes.find(
                    signal => signal.type === checkbox.nextSibling.textContent.trim()
                );
                if (signalType) {
                    checkbox.checked = signalType.checked;
                }
            });
        }
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

    handleRefreshChannels() {
        console.log('Refrescando canales de Aura...');
        // Aquí añadiríamos el código específico para refrescar los canales desde el backend o API
        alert('Canales de Aura actualizados.');
    }

    handleRemoveSelectedChannels() {
        console.log('Eliminando canales seleccionados...');
        // Aquí se implementaría la lógica para identificar y eliminar los canales seleccionados
        alert('Canales seleccionados eliminados.');
    }

    handleSelectChannels() {
        console.log('Seleccionando canales...');
        // Aquí se implementaría la lógica para seleccionar canales
        alert('Canales seleccionados con éxito.');
    }
}

// Inicializar el gestor de experimentos cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new ExperimentManager();
});
