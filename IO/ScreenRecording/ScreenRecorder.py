from abc import abstractmethod

class ScreenRecorder:
    def __init__(self, path_to_save, filename):
        self._path = path_to_save
        self._filename = filename

    @abstractmethod
    def start_recording(self):
        pass

    @abstractmethod
    def stop_recording(self):
        pass

    def __del__(self):
        self.stop_recording()
