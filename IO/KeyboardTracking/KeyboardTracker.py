from pynput import keyboard
import time

class KeyboardTracker:
    def __init__(self, writer=None):
        """
        Initializes the KeyboardTracker with keyboard listener and optional writer.
        """
        self._listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self._listener.start()
        self._writer = writer
        self._start_time = None
        self._is_tracking = False
        self._current_key = None
        self._is_pressed = False

    @property
    def start_time(self):
        """Gets the start time."""
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        """Sets the start time."""
        self._start_time = value

    @property
    def is_tracking(self):
        """Gets the current tracking status."""
        return self._is_tracking

    @is_tracking.setter
    def is_tracking(self, value):
        """Sets the tracking status."""
        self._is_tracking = bool(value)

    def on_press(self, key):
        """Callback for key press events"""
        if self._is_tracking:
            self._is_pressed = True
            self._current_key = self._get_key_name(key)
            self.handle_key_event()

    def on_release(self, key):
        """Callback for key release events"""
        if self._is_tracking:
            self._is_pressed = False
            self._current_key = self._get_key_name(key)
            self.handle_key_event()

    def _get_key_name(self, key):
        """Convert key to string representation"""
        try:
            return key.char
        except AttributeError:
            return str(key)

    def handle_key_event(self):
        """
        Handles tracking of keyboard events
        """
        if self._writer and self._start_time is not None:
            timestamp = time.time() - self._start_time
            self._writer.write(timestamp, self._current_key, self._is_pressed)

    def stop_tracking(self):
        """
        Stops the keyboard listener and closes the writer if it exists.
        """
        self._is_tracking = False
        self._listener.stop()
        if self._writer:
            self._writer.close_file() 