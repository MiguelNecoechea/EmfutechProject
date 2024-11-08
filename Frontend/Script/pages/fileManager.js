class FileManager {
    constructor() {
        this.initializeComponents();
        this.attachEventListeners();
    }

    initializeComponents() {
        // Referencias a los elementos del formulario
        this.filters = document.querySelectorAll('.filter-select');
        this.searchInput = document.querySelector('.search-input');
        this.searchButton = document.querySelector('.search-btn');
        this.actionButtons = document.querySelectorAll('.action-btn');
        this.fileContainer = document.querySelector('.file-container');
    }

    attachEventListeners() {
        // Event listeners para los filtros
        this.filters.forEach(filter => {
            filter.addEventListener('change', this.handleFilterChange.bind(this));
        });

        // Event listener para el botón de búsqueda
        this.searchButton.addEventListener('click', this.handleSearch.bind(this));

        // Event listeners para los botones de acción
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
        const query = this.searchInput.value;
        console.log('Searching for files with query:', query);
        this.updateFileList(query);
    }

    handleActionClick(event) {
        const action = event.target.textContent;
        switch (action) {
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

    updateFileList(query = '') {
        // Actualizar lista de archivos basado en filtros y búsqueda
        console.log('Updating file list with query:', query);
        // Ejemplo de cómo podrías filtrar los archivos y luego renderizarlos
        const files = this.filterFiles(query);
        this.renderFileList(files);
    }

    filterFiles(query) {
        // Esta función simula el filtrado de archivos basándose en la búsqueda y otros filtros
        // Para fines de ejemplo, generaremos archivos simulados
        const sampleFiles = [
            { name: 'Project Report.docx', modifiedDate: '2024-01-20', size: '1.2 MB' },
            { name: 'Study Data.xlsx', modifiedDate: '2024-01-15', size: '2.4 MB' },
            { name: 'Experiment Results.pdf', modifiedDate: '2024-01-10', size: '1.1 MB' }
        ];
        return sampleFiles.filter(file => file.name.toLowerCase().includes(query.toLowerCase()));
    }

    handleGroupAssignment() {
        console.log('Opening group assignment interface');
        // Lógica para asignar grupos
    }

    handleSegmentation() {
        console.log('Opening segmentation interface');
        // Lógica para segmentación de archivos
    }

    handleGroupEditing() {
        console.log('Opening group editing interface');
        // Lógica para editar grupos de archivos
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
                    Last modified: ${file.modifiedDate} | Size: ${file.size}
                </div>
            </div>
        `;
        div.addEventListener('click', () => this.handleFileClick(file));
        return div;
    }

    handleFileClick(file) {
        console.log('File clicked:', file);
        alert(`File selected: ${file.name}`);
        // Lógica adicional para manejar la selección de archivo
    }
}

// Inicializar el gestor de archivos cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new FileManager();
});
