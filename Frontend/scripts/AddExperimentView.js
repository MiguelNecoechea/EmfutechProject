class AddExperimentView {
    constructor() {
        this.setupElements();
        this.setupEventListeners();
    }

    setupElements() {
        // Form elements
        this.experimentForm = document.getElementById('experimentForm');
        this.experimentName = document.getElementById('experimentName');
        this.experimentDescription = document.getElementById('experimentDescription');
        this.experimentFolder = document.getElementById('experimentFolder');
        this.experimentMinutes = document.getElementById('experimentMinutes');
        this.experimentSeconds = document.getElementById('experimentSeconds');
        this.selectFolderBtn = document.getElementById('selectFolder');
        this.cancelBtn = document.getElementById('cancelBtn');
        this.confirmBtn = document.getElementById('confirmBtn');

        // Add signal checkboxes
        this.signalAura = document.querySelector('input[name="signal-aura"]');
        this.signalEye = document.querySelector('input[name="signal-eye"]');
        this.signalEmotion = document.querySelector('input[name="signal-emotion"]');
        this.signalPointer = document.querySelector('input[name="signal-pointer"]');
        this.signalKeyboard = document.querySelector('input[name="signal-keyboard"]');
    }

    setupEventListeners() {
        // Folder selection
        this.selectFolderBtn.addEventListener('click', () => this.handleFolderSelection());

        // Form submission
        this.experimentForm.addEventListener('submit', (e) => this.handleSubmit(e));

        // Cancel button - using direct function call
        this.cancelBtn.addEventListener('click', () => {
            console.log('Cancel button clicked'); // Debug log
            window.electronAPI.closeWindow();
        });
    }

    async handleFolderSelection() {
        try {
            const folderPath = await window.electronAPI.openDirectory();
            if (folderPath) {
                this.experimentFolder.value = folderPath;
                this.selectFolderBtn.textContent = 'Change Folder';
            }
        } catch (error) {
            console.error('Error selecting folder:', error);
        }
    }

    async handleSubmit(event) {
        event.preventDefault();

        // Validate form
        if (!this.validateForm()) {
            return;
        }

        const experimentData = {
            name: this.experimentName.value,
            description: this.experimentDescription.value,
            folder: this.experimentFolder.value,
            length: {
                minutes: parseInt(this.experimentMinutes.value),
                seconds: parseInt(this.experimentSeconds.value)
            },
            // Update signals configuration
            signals: {
                aura: this.signalAura.checked,
                eye: this.signalEye.checked,
                emotion: this.signalEmotion.checked,
                pointer: this.signalPointer.checked,
                keyboard: this.signalKeyboard.checked,
                screen: true, // Always true
                face_landmarks: true
            }
        };

        try { 
            const response = await window.electronAPI.saveExperiment(experimentData);
            
            if (response.status === 'success') {
                // Send the experiment data to the main window to update the study panel
                await window.electronAPI.updateStudyPanel(experimentData);
                // Close the window
                window.electronAPI.closeWindow();
            } else {
                alert('Failed to save experiment: ' + response.message);
            }
        } catch (error) {
            console.error('Error saving experiment:', error);
            alert('Error saving experiment: ' + error.message);
        }
    }

    handleCancel() {
        // Use the window.electronAPI to close the window
        window.electronAPI.closeWindow(); 
    }

    validateForm() {
        // Name validation
        if (!this.experimentName.value.trim()) {
            alert('Please enter an experiment name');
            return false;
        }

        // Folder validation
        if (!this.experimentFolder.value) {
            alert('Please select a folder for the experiment');
            return false;
        }

        // Length validation
        const minutes = parseInt(this.experimentMinutes.value);
        const seconds = parseInt(this.experimentSeconds.value);
        
        if (isNaN(minutes) || minutes < 0) {
            alert('Please enter a valid number of minutes (must be 0 or greater)');
            return false;
        }

        if (isNaN(seconds) || seconds < 0 || seconds > 59) {
            alert('Please enter a valid number of seconds (must be between 0 and 59)');
            return false;
        }

        if (minutes === 0 && seconds === 0) {
            alert('Total experiment duration must be greater than 0');
            return false;
        }

        // Add signal validation
        const hasSignalSelected = 
            this.signalAura.checked ||
            this.signalEye.checked ||
            this.signalEmotion.checked ||
            this.signalPointer.checked ||
            this.signalKeyboard.checked;

        if (!hasSignalSelected) {
            alert('Please select at least one tracking signal');
            return false;
        }

        return true;
    }
}

// Initialize the view when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AddExperimentView();
});
