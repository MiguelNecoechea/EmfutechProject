from IO.ScreenRecording.ScreenRecorder import ScreenRecorder
import dxcam
import cv2
import numpy as np
import time
import os
from screeninfo import get_monitors
from typing import Tuple, Optional
import threading

class WindowsScreenRecorder(ScreenRecorder):
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.camera = dxcam.create(output_idx=0, output_color="BGR")
        self.resolution = self.get_screen_resolution()
        self.is_recording = False
        self.record_thread = None

    def get_screen_resolution(self):
        monitors = get_monitors()
        main_monitor = None
        for monitor in monitors:
            if monitor[-1] == True:
                main_monitor = monitor
        if main_monitor is None:
            main_monitor = (0, 0, 0, 0)

        return main_monitor[2], main_monitor[3]

    def start_recording(self, fps: int = 30):
        if self.is_recording:
            print("Recording is already in progress.")
            return

        self.is_recording = True
        self.record_thread = threading.Thread(target=self._record, args=(fps,))
        self.record_thread.start()
        print("Recording started.")


    def stop_recording(self):
        if not self.is_recording:
            print("No recording in progress.")
            return

        self.is_recording = False
        if self.record_thread:
            self.record_thread.join()
        print("Recording stopped.")

    def _record(self, fps: int):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(self.output_path, fourcc, fps, self.resolution)

        start_time = time.time()
        frame_count = 0

        try:
            while self.is_recording:
                writer.write(self.camera.get_latest_frame())

            duration = time.time() - start_time
            actual_fps = frame_count / duration if duration > 0 else 0
            print(f"Recording completed. Output saved to: {self.output_path}")
            print(f"Recorded {frame_count} frames in {duration:.2f} seconds (approx. {actual_fps:.2f} FPS)")
        except Exception as e:
            print(f"Error during recording: {e}")
        finally:
            writer.release()
            cv2.destroyAllWindows()

    def __del__(self):
        del self.camera

    def __str__(self):
        return f"DXCamScreenRecorder(resolution={self.resolution}, output_path={self.output_path}, region={self.region})"

for m in get_monitors():
    print(str(m))
