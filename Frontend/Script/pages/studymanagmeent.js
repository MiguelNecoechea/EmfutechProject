// Init: Javier Reyes
// Date: 2021-09-15
// Update: 2021-09-15
// Description: Script para la página de gestión de estudios
class StudyManager {
    constructor() {
        this.initializeComponents();
        this.attachEventListeners();
    }

    initializeComponents() {
        this.filters = document.querySelectorAll('.filter-select');
        this.searchInput = document.querySelector('.search-input');
        this.searchButton = document.querySelector('.search-btn');
        this.optionButtons = document.querySelectorAll('.option-btn');
        this.studyContainers = {
            status: document.querySelector('.status-content'),
            dashboard: document.querySelector('.dashboard-content'),
            progress: document.querySelector('.progress-content'),
            results: document.querySelector('.results-content')
        };
    }

    attachEventListeners() {
        // Event listeners para filtros
        this.filters.forEach(filter => {
            filter.addEventListener('change', this.handleFilterChange.bind(this));
        });

        // Event listener para búsqueda
        this.searchButton.addEventListener('click', this.handleSearch.bind(this));
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });

        // Event listeners para botones de opciones
        this.optionButtons.forEach(button => {
            button.addEventListener('click', this.handleOptionClick.bind(this));
        });
    }

    handleFilterChange(event) {
        const filterType = event.target.options[0].text;
        const selectedValue = event.target.value;
        console.log(`Filter ${filterType} changed to: ${selectedValue}`);
        this.updateStudyView();
    }

    handleSearch() {
        const searchTerm = this.searchInput.value.trim();
        console.log(`Searching for: ${searchTerm}`);
        this.performSearch(searchTerm);
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

    performSearch(term) {
        // Implementar lógica de búsqueda
        console.log('Performing search with term:', term);
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

    updateStudyView() {
        // Actualizar las diferentes secciones de estudio
        this.updateStudyStatus();
        this.updateDashboard();
        this.updateProgress();
        this.updateResults();
    }

    updateStudyStatus() {
        // Actualizar estado del estudio
    }

    updateDashboard() {
        // Actualizar dashboard
    }

    updateProgress() {
        // Actualizar progreso de participantes
    }

    updateResults() {
        // Actualizar gestión de resultados
    }
}

// Inicializar el gestor de estudios cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new StudyManager();
});