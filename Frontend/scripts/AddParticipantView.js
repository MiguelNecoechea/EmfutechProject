class AddParticipantView {
    constructor() {
        this.setupElements();
        this.setupEventListeners();
        // Get the experiment ID from the URL or window parameters
        const urlParams = new URLSearchParams(window.location.search);
        this.experimentId = urlParams.get('experimentId');
        if (!this.experimentId) {
            alert('No experiment selected');
            window.electronAPI.closeWindow();
        }
    }

    setupElements() {
        // Form elements
        this.participantForm = document.getElementById('participantForm');
        this.participantName = document.getElementById('participantName');
        this.participantAge = document.getElementById('participantAge');
        this.participantGender = document.getElementById('participantGender');
        this.participantBirthday = document.getElementById('participantBirthday');
        this.cancelBtn = document.getElementById('cancelBtn');
        this.confirmBtn = document.getElementById('confirmBtn');
    }

    setupEventListeners() {
        // Form submission
        this.participantForm.addEventListener('submit', (e) => this.handleSubmit(e));

        // Cancel button
        this.cancelBtn.addEventListener('click', () => {
            window.electronAPI.closeWindow();
        });
    }

    async handleSubmit(event) {
        event.preventDefault();

        // Validate form
        if (!this.validateForm()) {
            return;
        }

        const participantData = {
            experimentId: this.experimentId,
            name: this.participantName.value,
            age: parseInt(this.participantAge.value),
            gender: this.participantGender.value,
            birthday: this.participantBirthday.value,
            createdAt: new Date().toISOString()
        };

        try {
            const response = await window.electronAPI.saveParticipant(participantData);
            
            if (response.status === 'success') {
                // Include the folder path in the participant data
                const participantWithFolder = {
                    ...participantData,
                    folderPath: response.folderPath
                };

                // Send the participant data with experimentId for proper updating
                await window.electronAPI.updateParticipantCount({
                    experimentId: this.experimentId,
                    participant: participantWithFolder
                });
                
                window.electronAPI.closeWindow();
            } else {
                alert('Failed to save participant: ' + response.message);
            }
        } catch (error) {
            console.error('Error saving participant:', error);
            alert('Error saving participant: ' + error.message);
        }
    }

    validateForm() {
        // Name validation
        if (!this.participantName.value.trim()) {
            alert('Please enter participant name');
            return false;
        }

        // Age validation
        const age = parseInt(this.participantAge.value);
        if (isNaN(age) || age < 0) {
            alert('Please enter a valid age');
            return false;
        }

        // Gender validation
        if (!this.participantGender.value) {
            alert('Please select a gender');
            return false;
        }

        // Birthday validation
        if (!this.participantBirthday.value) {
            alert('Please enter a birthday');
            return false;
        }

        return true;
    }
}

// Initialize the view when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AddParticipantView();
}); 