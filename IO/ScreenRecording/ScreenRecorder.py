import time

import cv2
import numpy as np
import mss
import screeninfo
import threading

class ScreenRecorder:
    """
    A base implementation of a screen recorder. While the performance might not be the best, it is intended to be
    platform-independent. Any platform-specific implementation should inherit from this class. Even then the platform
    specific implementation are still in build
    """
    def __init__(self, output_path: str, filename):
        """
        Constructor of the screen recorder.
        :param output_path: The path where the video will be saved.
        :param filename: The name of the video file.
        """
        self.output_path = output_path
        self.filename = filename
        self.is_recording_active = False
        self.video_data_writer = None
        self.screen_width, self.screen_height = self.__get_main_screen_resolution()
        self.mss_area = {'top': 0, 'left': 0, 'width': self.screen_width, 'height': self.screen_height}

    def __internal_recording_loop(self):
        """
        Internal loop that captures the screen and writes it to the video file.
        """
        with mss.mss() as sct:
            while True:
                if self.video_data_writer is not None:
                    frame = np.array(sct.grab(self.mss_area))
                    formated_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                    if formated_frame.shape[1::-1] != (self.screen_width, self.screen_height):
                        formated_frame = cv2.resize(formated_frame, (self.screen_width, self.screen_height))
                    self.video_data_writer.write(formated_frame)
                if not self.is_recording_active:
                    break


    def __get_main_screen_resolution(self):
        """
        This function returns the resolution of the main screen.
        :return: A tuple containing the width and height of the screen.
        """
        screen = screeninfo.get_monitors()[0]
        return screen.width, screen.height

    def start_recording(self, fps: int = 30) -> bool:
        """
        Starts the recording of the screen. The recording will be saved in the output path with the filename.
        :param fps: The target fps of the recording.
        :return: A boolean indicating if the recording was successfully started.
        """
        if not self.is_recording_active:

            self.is_recording_active = True
            self.video_data_writer = cv2.VideoWriter(
                self.output_path + self.filename,
                cv2.VideoWriter_fourcc(*'mp4v'),
                fps,
                (self.screen_width, self.screen_height),
                isColor=True
            )
            self.record_thread = threading.Thread(target=self.__internal_recording_loop)
            self.record_thread.start()
            return True
        return False


    def stop_recording(self) -> bool:
        """
        Stops the recording of the screen. The video file will be saved in the output path with the filename.
        :return: A boolean indicating if the recording was successfully stopped.
        """
        self.is_recording_active = False
        if hasattr(self, 'record_thread'):  # Added thread joining
            self.record_thread.join()
        return True

# TESTING
# screen_recoreder = ScreenRecorder("/Users/mnecoea/PycharmProjects/AuraSignalProcessing/", "test.mp4")
# screen_recoreder.start_recording()
# time.sleep(5)
# screen_recoreder.stop_recording()
