from abc import abstractmethod

class ScreenRecorder:
    """
    An abstract class containing the base implementation for a screen recorder.
    Specific OS implementations should be in a different file.
    """
    def __init__(self, path_to_save, filename):
        self._path = path_to_save
        self._filename = filename

    @abstractmethod
    def start_recording(self):
        print("Starting recording...")
        pass

    @abstractmethod
    def stop_recording(self):
        pass


