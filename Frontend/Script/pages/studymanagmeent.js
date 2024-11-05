class StudyManager {
    constructor() {
        this.initializeComponents();
        this.attachEventListeners();
    }

    initializeComponents() {
        // Inicializar filtros y búsqueda
        this.filters = document.querySelectorAll('.filter-select');
        this.searchInput = document.querySelector('.search-input');
        this.searchButton = document.querySelector('.search-btn');
        
        // Inicializar botones de opciones y contenedores de contenido
        this.optionButtons = document.querySelectorAll('.toolbar-btn');
        this.newStudyButton = document.querySelector('.new-study-btn');
        this.studyContainers = {
            status: document.querySelector('.status-content'),
            dashboard: document.querySelector('.dashboard-content'),
            progress: document.querySelector('.progress-content'),
            results: document.querySelector('.results-content')
        };
    }

    attachEventListeners() {
        // Event listeners para los filtros
        this.filters.forEach(filter => {
            filter.addEventListener('change', this.handleFilterChange.bind(this));
        });

        // Event listener para el botón de búsqueda
        this.searchButton.addEventListener('click', this.handleSearch.bind(this));
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });

        // Event listeners para los botones de opciones en la barra de herramientas
        this.optionButtons.forEach(button => {
            button.addEventListener('click', this.handleOptionClick.bind(this));
        });

        // Event listener para el botón de "Nuevo Estudio"
        if (this.newStudyButton) {
            this.newStudyButton.addEventListener('click', this.createNewStudy.bind(this));
        }
    }

    handleFilterChange(event) {
        const filterType = event.target.options[0].textContent.trim();
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
        const option = event.target.textContent.trim();
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
        this.updateStudyView();
    }

    handleGroupAssignment() {
        console.log('Opening group assignment interface');
        alert('Assigning groups...');
    }

    handleSegmentation() {
        console.log('Opening segmentation interface');
        alert('Performing segmentation...');
    }

    handleGroupEditing() {
        console.log('Opening group editing interface');
        alert('Editing groups...');
    }

    createNewStudy() {
        console.log('Creating new study...');
        alert('New study form opened.');
    }

    updateStudyView() {
        console.log('Updating study view...');
        this.updateStudyStatus();
        this.updateDashboard();
        this.updateProgress();
        this.updateResults();
    }

    updateStudyStatus() {
        console.log('Updating study status...');
        this.studyContainers.status.innerHTML = `<p>Updated status of studies</p>`;
    }

    updateDashboard() {
        console.log('Updating dashboard...');
        this.studyContainers.dashboard.innerHTML = `<p>Updated dashboard content</p>`;
    }

    updateProgress() {
        console.log('Updating participant progress...');
        this.studyContainers.progress.innerHTML = `<p>Updated progress of participants</p>`;
    }

    updateResults() {
        console.log('Updating results management...');
        this.studyContainers.results.innerHTML = `<p>Updated study results</p>`;
    }
}

// Inicializar el gestor de estudios cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new StudyManager();
});
