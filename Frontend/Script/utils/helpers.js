export const helpers = {
    formatDate(date) {
        return new Date(date).toLocaleDateString();
    },

    formatTime(date) {
        return new Date(date).toLocaleTimeString();
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    generateId() {
        return Math.random().toString(36).substr(2, 9);
    }
};