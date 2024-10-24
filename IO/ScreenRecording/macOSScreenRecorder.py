from IO.ScreenRecording.ScreenRecorder import ScreenRecorder


class macOSScreenRecorder(ScreenRecorder):
    def __init__(self, path_to_save, filename):
        self._path = path_to_save
        self._filename = filename
        super().__init__(path_to_save, filename)

    def start_recording(self):
        raise NotImplementedError("macOS not supported")

    def stop_recording(self):
        raise NotImplementedError("macOS not supported")