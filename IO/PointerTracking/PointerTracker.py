from pynput import mouse

class CursorTracker:
    def __init__(self, writer=None):
        """
        Initializes the CursorTracker with a mouse listener and optional writer.
        
        Args:
            writer: Optional PointerWriter object to write coordinates to file
        """
        self._listener = mouse.Listener(on_click=self.on_click)
        self._listener.start()
        self._click_coordinates = []
        self._writer = writer
        self._is_tracking = True

    @property
    def is_tracking(self):
        """Gets the current tracking status."""
        return self._is_tracking

    @is_tracking.setter
    def is_tracking(self, value):
        """Sets the tracking status."""
        self._is_tracking = bool(value)

    def on_click(self, x, y, button, pressed):
        """
        Callback function that is called on mouse click events.

        Args:
            x (int): The x-coordinate of the cursor.
            y (int): The y-coordinate of the cursor.
            button (Button): The mouse button that was clicked.
            pressed (bool): True if the button was pressed, False if released.
        """
        if pressed and self._is_tracking:
            self.handle_click(x, y)

    def handle_click(self, x, y):
        """
        Handles the click event by storing coordinates and writing to file if writer exists.

        Args:
            x (int): The x-coordinate of the cursor.
            y (int): The y-coordinate of the cursor.

        Returns:
            tuple: A tuple containing the (x, y) coordinates.
        """
        coordinates = (int(x), int(y))
        self._click_coordinates.append(coordinates)
        
        # Write to file if writer exists
        if self._writer:
            self._writer.write(coordinates[0], coordinates[1])
            
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

