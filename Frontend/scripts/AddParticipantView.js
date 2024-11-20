class AddParticipantView {
    constructor() {
        this.setupElements();
        this.setupEventListeners();
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
            name: this.participantName.value,
            age: parseInt(this.participantAge.value),
            gender: this.participantGender.value,
            birthday: this.participantBirthday.value,
            nationality: this.participantNationality.value
        };

        try {
            const response = await window.electronAPI.saveParticipant(participantData);
            
            if (response.status === 'success') {
                // Send the participant data to the main window to update the participant count
                await window.electronAPI.updateParticipantCount(participantData);
                // Close the window
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