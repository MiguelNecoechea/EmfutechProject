import time
import os
import cv2
import numpy as np
import mss
import screeninfo
import threading
from collections import deque
from DataProcessing.ffmpegPostProcessing import post_process_video

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
        self.can_write_frame = False
        self.video_data_writer = None
        self.screen_width, self.screen_height = self.__get_main_screen_resolution()
        self.mss_area = {'top': 0, 'left': 0, 'width': self.screen_width, 'height': self.screen_height}
        
        # Frame buffer and FPS monitoring
        self.frame_buffer = deque(maxlen=120)  # 2 seconds buffer at 60fps
        self.fps_buffer = deque(maxlen=60)  # Store last 60 frame timestamps
        self.current_fps = 0.0  # Current observed FPS
        self.frame_count = 0
        self.start_time = None
        self.target_fps = 30  # Fixed target FPS
        self.frame_interval = 1.0 / self.target_fps  # Time between frames
        self.last_frame_time = None
        self.previous_frame = None

    def __calculate_current_fps(self):
        """Calculate the current FPS based on total frames and elapsed time"""
        if self.start_time is None or self.frame_count == 0:
            return 0.0
        
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 0:
            return self.frame_count / elapsed_time
        return 0.0

    def __interpolate_frames(self, frame1, frame2, alpha):
        """Interpolate between two frames"""
        return cv2.addWeighted(frame1, 1 - alpha, frame2, alpha, 0)

    def __internal_recording_loop(self):
        with mss.mss() as sct:
            self.start_time = time.time()
            self.frame_count = 0
            self.last_frame_time = self.start_time
            target_frame_time = self.start_time
            
            while True:
                if self.video_data_writer is not None:
                    current_time = time.time()
                    frame = np.array(sct.grab(self.mss_area))
                    formated_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                    if formated_frame.shape[1::-1] != (self.screen_width, self.screen_height):
                        formated_frame = cv2.resize(formated_frame, (self.screen_width, self.screen_height))
                    
                    # Always generate exactly one frame per target interval
                    while target_frame_time <= current_time:
                        if self.previous_frame is not None:
                            # Calculate interpolation factor
                            alpha = (target_frame_time - self.last_frame_time) / (current_time - self.last_frame_time)
                            alpha = max(0.0, min(1.0, alpha))  # Clamp between 0 and 1
                            
                            interpolated = self.__interpolate_frames(
                                self.previous_frame,
                                formated_frame,
                                alpha
                            )
                            self.frame_buffer.append((interpolated, target_frame_time))
                        else:
                            # First frame
                            self.frame_buffer.append((formated_frame, target_frame_time))
                        
                        self.frame_count += 1
                        target_frame_time += self.frame_interval
                    
                    self.last_frame_time = current_time
                    self.previous_frame = formated_frame.copy()
                    self.current_fps = self.__calculate_current_fps()
                    
                    # Write frames from buffer if enabled
                    if self.can_write_frame:
                        while self.frame_buffer and len(self.frame_buffer) > 30:  # Keep some buffer
                            frame_data = self.frame_buffer.popleft()
                            self.video_data_writer.write(frame_data[0])

                if not self.is_recording_active:
                    # Write remaining frames in buffer
                    if self.can_write_frame:
                        while self.frame_buffer:
                            frame_data = self.frame_buffer.popleft()
                            self.video_data_writer.write(frame_data[0])
                    break

    def __get_main_screen_resolution(self):
        """
        This function returns the resolution of the main screen.
        :return: A tuple containing the width and height of the screen.
        """
        screen = screeninfo.get_monitors()[0]
        return screen.width, screen.height

    def start_recording(self, fps: int = None) -> bool:
        """
        Starts the recording of the screen.
        :param fps: Ignored as we now use fixed 30 FPS
        :return: A boolean indicating if the recording was successfully started.
        """
        if not self.is_recording_active:
            self.is_recording_active = True
            self.frame_count = 0
            self.current_fps = 0.0
            self.start_time = None
            self.last_frame_time = None
            self.previous_frame = None
            
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
                        self.target_fps,  # Use fixed FPS for the writer
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

    def get_current_fps(self) -> float:
        """
        Get the current observed FPS of the recording.
        :return: The current FPS as a float
        """
        return self.current_fps

    def stop_recording(self) -> bool:
        """
        Stops the recording of the screen and converts the video to a web-compatible format.
        :return: A boolean indicating if the recording was successfully stopped and converted.
        """
        # First stop the recording
        self.is_recording_active = False
        if hasattr(self, 'record_thread'):
            self.record_thread.join()
        
        if self.video_data_writer:
            self.video_data_writer.release()
        
        # Get file paths
        original_file = self.output_path + self.filename
        
        # Post-process the video using the shared function
        return post_process_video(original_file, original_file)

    def set_frame_writing(self, enabled: bool) -> None:
        """
        Enable or disable frame writing during recording.
        :param enabled: Boolean indicating if frames should be written
        """
        self.can_write_frame = enabled

    def get_frame_writing_state(self) -> bool:
        """
        Get the current frame writing state.
        :return: Boolean indicating if frames are being written
        """
        return self.can_write_frame
