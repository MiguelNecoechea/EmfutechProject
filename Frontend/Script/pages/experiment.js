class ExperimentManager {
    constructor() {
        this.initializeForm();
        this.attachEventListeners();
    }

    initializeForm() {
        this.form = document.querySelector('.experiment-form');
        
        // Referencias a los campos del formulario
        this.experimentName = document.getElementById('experimentName');
        this.description = document.getElementById('description');
        this.objective = document.getElementById('objective');
        this.duration = document.getElementById('duration');
        this.participants = document.getElementById('participants');
        this.activeSensors = document.getElementById('activeSensors');
        this.stimulusConfig = document.getElementById('stimulusConfig');
        this.frequency = document.getElementById('frequency');
    }

    attachEventListeners() {
        const navTabs = document.querySelectorAll('.nav-tabs a');
        navTabs.forEach(tab => {
            tab.addEventListener('click', this.handleTabClick.bind(this));
        });

        if (this.form) {
            this.form.addEventListener('submit', this.handleFormSubmit.bind(this));
        }

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
        const formData = {
            experimentName: this.experimentName.value,
            description: this.description.value,
            objective: this.objective.value,
            duration: this.duration.value,
            participants: this.participants.value,
            activeSensors: this.activeSensors.value,
            stimulusConfig: this.stimulusConfig.value,
            frequency: this.frequency.value
        };

        // Guardar datos en LocalStorage o enviar a backend
        localStorage.setItem('experimentFormData', JSON.stringify(formData));
        
        alert('Experiment data saved successfully!');
        console.log('Form Data:', formData);
    }

    handleSelectChange(event) {
        const selectId = event.target.id;
        const selectedValue = event.target.value;
        console.log(`${selectId} changed to: ${selectedValue}`);
    }
}

// Inicializar el gestor de experimentos cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new ExperimentManager();
});
