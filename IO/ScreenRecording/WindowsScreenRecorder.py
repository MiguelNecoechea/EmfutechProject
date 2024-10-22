from IO.ScreenRecording.ScreenRecorder import ScreenRecorder
import dxcam
import cv2
import os
from screeninfo import get_monitors
from typing import Tuple
import threading

class WindowsScreenRecorder(ScreenRecorder):
    """
    Specific implementation of a basic ScreenRecorder using the dxcam module.
    Since this module requires directX components implementation is intended to only windows systems.
    """
    def __init__(self, output_path: str, filename, fps: int = 30):
        """
        Constructor of the screen recorder. The format of the file is mp4.
        :param output_path: The path where the video will be saved.
        :param filename: The name of the video file.
        :param fps: The target fps of the recording.
        """
        super().__init__(output_path, filename)
        self.camera = dxcam.create(output_idx=0, output_color="BGR")
        self.resolution = self.get_main_screen_resolution()
        self.is_recording = False
        self.record_thread = None
        self.writer = cv2.VideoWriter(os.path.join(output_path, filename),
                                      cv2.VideoWriter_fourcc(*'mp4v'), fps, self.resolution)

    @staticmethod
    def get_main_screen_resolution() -> Tuple[int, int]:
        """
        This function returns the resolution of the screens connected to a display adapter.
        :return: A tuple containing the width and height of the screen.
        """
        monitors = get_monitors()
        main_monitor = None
        for monitor in monitors:
            if monitor.is_primary:
                main_monitor = monitor

        if main_monitor is None:
            raise RuntimeError("No primary monitor found")
        return main_monitor.width, main_monitor.height

    def start_recording(self, fps: int = 30) -> bool:
        """
        Initializes a thread that will be capturing all video data and writing it.
        :param fps: The target fps of the recording.
        :return: A boolean indicating if the recording was successfully started.
        """
        start_recording = False
        if self.is_recording:
            return start_recording

        self.camera.start(target_fps=fps, video_mode=True)

        self.is_recording = start_recording = True
        self.record_thread = threading.Thread(target=self._record)
        self.record_thread.start()
        return start_recording


    def stop_recording(self) -> bool:
        """
        Stops the recording thread, closes the writer and releases the video capture.
        :return: A boolean indicating if the recording was successfully stopped.
        """
        stopped_recording = False
        if not self.is_recording:
            return stopped_recording

        self.is_recording = False
        stopped_recording = True
        if self.record_thread:
            self.record_thread.join()
        self.camera.stop()
        self.writer.release()
        return stopped_recording

    def _record(self):
        """
        An auxiliary function that is targeted to run on a separate thread. For the frame capture.
        """
        try:
            while True:
                self.writer.write(self.camera.get_latest_frame())
        except Exception as e:
            print(f"Error during recording: {e}")
        finally:
            self.writer.release()
            cv2.destroyAllWindows()

    def __del__(self):
        """
        Frees resources by deleting the camera object.
        """
        del self.camera
