import time
import subprocess
import os

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
            
            # Use H.264 codec with fallbacks
            codecs_to_try = [
                'avc1',  # H.264/AVC
                'h264',  # Alternative name for H.264
                'X264',  # Another alternative
                'XVID'   # Last resort
            ]
            
            for codec in codecs_to_try:
                try:
                    self.video_data_writer = cv2.VideoWriter(
                        self.output_path + self.filename,
                        cv2.VideoWriter_fourcc(*codec),
                        fps,
                        (self.screen_width, self.screen_height),
                        isColor=True
                    )
                    if self.video_data_writer.isOpened():
                        break
                except Exception as e:
                    print(f"Failed to initialize codec {codec}: {str(e)}")
                    continue
            
            if not self.video_data_writer.isOpened():
                print("Failed to initialize any video codec")
                self.is_recording_active = False
                return False
            
            self.record_thread = threading.Thread(target=self.__internal_recording_loop)
            self.record_thread.start()
            return True
        return False


    def stop_recording(self) -> bool:
        """
        Stops the recording of the screen and converts the video to a web-compatible format.
        :return: A boolean indicating if the recording was successfully stopped and converted.
        """
        # First stop the recording as before
        self.is_recording_active = False
        if hasattr(self, 'record_thread'):
            self.record_thread.join()
        
        if self.video_data_writer:
            self.video_data_writer.release()
        
        # Now convert the video to web-compatible format
        original_file = self.output_path + self.filename
        temp_file = original_file + '.temp.mp4'
        
        try:
            # FFmpeg command for converting to web-compatible format
            command = [
                'ffmpeg',
                '-i', original_file,  # Input file
                '-c:v', 'h264',       # Video codec
                '-preset', 'medium',   # Encoding preset
                '-profile:v', 'baseline',  # Maximum compatibility
                '-level', '3.0',
                '-movflags', '+faststart',  # Web playback optimization
                '-pix_fmt', 'yuv420p',      # Ensure pixel format compatibility
                '-f', 'mp4',                # Force MP4 format
                temp_file
            ]
            
            # Run the conversion
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if process.returncode == 0:
                # If conversion was successful, replace the original file
                os.replace(temp_file, original_file)
                print("Video successfully converted to web-compatible format")
                return True
            else:
                error_message = process.stderr.decode()
                print(f"Error converting video: {error_message}")
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return False
                
        except Exception as e:
            print(f"Error during video conversion: {str(e)}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False
