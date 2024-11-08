const fs = require('fs');
// Frontend/Script/pages/experiment.js

class ExperimentManager {
    constructor() {
        this.initializeForm();
        this.attachEventListeners();
        this.setupValidation();
    }

    initializeForm() {
        this.form = document.querySelector('.experiment-form');
        this.experimentName = document.getElementById('experimentName');
        this.description = document.getElementById('description');
        this.duration = document.getElementById('duration');
        this.participants = document.getElementById('participants');
        this.activeSensors = document.getElementById('activeSensors');
        this.stimulusConfig = document.getElementById('stimulusConfig');

        // Botones
        this.saveButton = document.querySelector('button[type="submit"]');
        this.cancelButton = document.querySelector('button.btn-secondary');
        this.startButton = document.querySelector('button:last-child');
    }

    setupValidation() {
        this.requiredFields = ['experimentName', 'duration', 'participants'];
        this.validationMessages = {
            experimentName: 'El nombre del experimento es requerido',
            duration: 'Debe seleccionar una duración',
            participants: 'Debe seleccionar el tipo de participantes'
        };
    }

    async handleFormSubmit(event) {
        event.preventDefault();
        
        const { isValid, errors } = this.validateForm();
        if (!isValid) {
            this.showErrors(errors);
            return;
        }

        const formData = {
            experimentName: this.experimentName.value,
            description: this.description.value,
            duration: this.duration.value,
            participants: this.participants.value,
            activeSensors: this.activeSensors.value,
            stimulusConfig: this.stimulusConfig.value
        };

        try {
            this.showLoading();
            // Usar Eel para guardar el experimento
            const result = await eel.save_experiment(formData)();
            
            if (result.success) {
                this.showSuccess(result.message);
                this.resetForm();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            this.showError(`Error al guardar el experimento: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    attachEventListeners() {
        if (this.form) {
            this.form.addEventListener('submit', this.handleFormSubmit.bind(this));
        }

        this.cancelButton.addEventListener('click', () => {
            if (confirm('¿Está seguro de que desea cancelar? Los cambios no guardados se perderán.')) {
                this.resetForm();
            }
        });

        this.startButton.addEventListener('click', async () => {
            const { isValid, errors } = this.validateForm();
            if (!isValid) {
                this.showErrors(errors);
                return;
            }

            if (confirm('¿Desea iniciar el experimento ahora?')) {
                // Aquí iría la lógica para iniciar el experimento
                console.log('Iniciando experimento...');
            }
        });
    }

    validateForm() {
        let isValid = true;
        const errors = [];

        this.requiredFields.forEach(field => {
            const element = this[field];
            if (!element.value.trim()) {
                isValid = false;
                errors.push(this.validationMessages[field]);
                element.classList.add('invalid');
            } else {
                element.classList.remove('invalid');
            }
        });

        return { isValid, errors };
    }

    // Métodos de UI
    showLoading() {
        this.saveButton.disabled = true;
        this.saveButton.innerHTML = '<span class="spinner"></span> Guardando...';
    }

    hideLoading() {
        this.saveButton.disabled = false;
        this.saveButton.textContent = 'Guardar experimento';
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showErrors(errors) {
        errors.forEach(error => this.showNotification(error, 'error'));
    }

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    resetForm() {
        this.form.reset();
        this.requiredFields.forEach(field => {
            this[field].classList.remove('invalid');
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new ExperimentManager();
});



