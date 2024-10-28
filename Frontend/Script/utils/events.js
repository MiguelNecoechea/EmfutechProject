class EventEmitter {
    constructor() {
        this.events = {};
    }

    on(eventName, callback) {
        if (!this.events[eventName]) {
            this.events[eventName] = [];
        }
        this.events[eventName].push(callback);
    }

    emit(eventName, data) {
        const callbacks = this.events[eventName];
        if (callbacks) {
            callbacks.forEach(callback => callback(data));
        }
    }

    off(eventName, callback) {
        const callbacks = this.events[eventName];
        if (callbacks) {
            this.events[eventName] = callbacks.filter(cb => cb !== callback);
        }
    }
}

export const eventBus = new EventEmitter();