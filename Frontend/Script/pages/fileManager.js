class FileManager {
    constructor() {
        this.initializeComponents();
        this.attachEventListeners();
    }

    initializeComponents() {
        this.filters = document.querySelectorAll('.filter-select');
        this.searchButton = document.querySelector('.search-btn');
        this.actionButtons = document.querySelectorAll('.action-btn');
        this.fileContainer = document.querySelector('.file-container');
    }

    attachEventListeners() {
        // Event listeners para filtros
        this.filters.forEach(filter => {
            filter.addEventListener('change', this.handleFilterChange.bind(this));
        });

        // Event listener para búsqueda
        this.searchButton.addEventListener('click', this.handleSearch.bind(this));

        // Event listeners para botones de acción
        this.actionButtons.forEach(button => {
            button.addEventListener('click', this.handleActionClick.bind(this));
        });
    }

    handleFilterChange(event) {
        const filterType = event.target.options[0].text;
        const selectedValue = event.target.value;
        console.log(`Filter ${filterType} changed to: ${selectedValue}`);
        this.updateFileList();
    }

    handleSearch() {
        console.log('Performing file search');
        this.updateFileList();
    }

    handleActionClick(event) {
        const action = event.target.textContent;
        switch(action) {
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

    updateFileList() {
        // Actualizar lista de archivos basado en filtros
        console.log('Updating file list');
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

    renderFileList(files) {
        this.fileContainer.innerHTML = '';
        files.forEach(file => {
            const fileElement = this.createFileElement(file);
            this.fileContainer.appendChild(fileElement);
        });
    }

    createFileElement(file) {
        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `
            <i class="file-icon icon-file"></i>
            <div class="file-details">
                <div class="file-name">${file.name}</div>
                <div class="file-meta">
                    Last modified: ${file.modifiedDate}
                    Size: ${file.size}
                </div>
            </div>
        `;
        div.addEventListener('click', () => this.handleFileClick(file));
        return div;
    }

    handleFileClick(file) {
        console.log('File clicked:', file);
        // Implementar acción al hacer clic en un archivo
    }
}

// Inicializar el gestor de archivos cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new FileManager();
});