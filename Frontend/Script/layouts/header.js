class Header {
    constructor() {
        this.header = document.querySelector('.top-nav');
        this.initializeHeader();
    }

    initializeHeader() {
        this.setupNavigation();
        this.setupUserMenu();
    }

    setupNavigation() {
        const navLinks = this.header.querySelectorAll('.nav-tabs a');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleNavigation(link);
            });
        });
    }

    setupUserMenu() {
        const userMenu = this.header.querySelector('.user-menu');
        if (userMenu) {
            userMenu.addEventListener('click', () => {
                this.toggleUserDropdown();
            });
        }
    }

    handleNavigation(link) {
        // Remover clase active de todos los links
        this.header.querySelectorAll('.nav-tabs a').forEach(el => {
            el.classList.remove('active');
        });
        // Agregar clase active al link clickeado
        link.classList.add('active');
    }

    toggleUserDropdown() {
        const dropdown = this.header.querySelector('.user-dropdown');
        if (dropdown) {
            dropdown.classList.toggle('show');
        }
    }
}

// Inicializar el header cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new Header();
});