from pynput import mouse
from pynput.mouse import Controller
import time

class CursorTracker:
    def __init__(self, writer=None):
        """
        Initializes the CursorTracker with mouse listener and optional writer.
        """
        self._listener = mouse.Listener(
            on_click=self.on_click,
            on_move=self.on_move
        )
        self._listener.start()
        self._mouse_controller = Controller()
        self._click_coordinates = []
        self._writer = writer
        self._start_time = None
        self._is_tracking = False
        self._is_clicked = False
        self._tracking_interval = 1 / 30  # 30 samples per second
        self._last_track_time = 0

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

    def on_click(self, x, y, button, pressed):
        """Callback for click events"""
        if self._is_tracking:
            self._is_clicked = pressed
            self.handle_position(x, y)

    def on_move(self, x, y):
        """Callback for mouse movement"""
        if self._is_tracking:
            current_time = time.time()
            # Only track movement at specified intervals
            if current_time - self._last_track_time >= self._tracking_interval:
                self.handle_position(x, y)
                self._last_track_time = current_time

    def handle_position(self, x, y):
        """
        Handles tracking of pointer position and click state
        """
        coordinates = (int(x), int(y))
        
        if self._writer and self._start_time is not None:
            timestamp = time.time() - self._start_time
            self._writer.write(timestamp, coordinates[0], coordinates[1], self._is_clicked)
            
        return coordinates

    def clear_coordinates(self):
        """Clears the stored click coordinates."""
        self._click_coordinates.clear()

    def stop_tracking(self):
        """
        Stops the mouse listener and closes the writer if it exists.
        """
        self._is_tracking = False
        self._listener.stop()
        if self._writer:
            self._writer.close_file()

