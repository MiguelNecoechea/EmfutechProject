from ScreenRecorder import ScreenRecorder
import dxcam
import cv2
import os
from screeninfo import get_monitors
from typing import Tuple
import threading

class WindowsScreenRecorder(ScreenRecorder):
    """
    Specific implementation of a basic ScreenRecorder using the dxcam module.
    Since this module requires DirectX components, implementation is intended for Windows systems only.
    """
    def __init__(self, output_path: str, filename, fps: int = 30):
        """
        Constructor of the screen recorder.
        :param output_path: The path where the video will be saved.
        :param filename: The name of the video file.
        :param fps: The target fps of the recording.
        """
        super().__init__(output_path, filename)
        self.camera = dxcam.create(output_idx=0, output_color="BGR")
        self.resolution = self.get_main_screen_resolution()
        self.is_recording = False
        self.record_thread = None
        self.fps = fps  # Frame rate for the video

        # Ensure output path exists and we have permission to write
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        if not os.access(output_path, os.W_OK):
            raise PermissionError(f"No write permission for the directory: {output_path}")

        # Use mp4v codec for mp4 format
        self.writer = cv2.VideoWriter(
            os.path.join(output_path, filename),
            cv2.VideoWriter_fourcc(*'mp4v'),  # Using mp4 codec
            fps,
            self.resolution
        )

    @staticmethod
    def get_main_screen_resolution() -> Tuple[int, int]:
        """
        This function returns the resolution of the main screen.
        :return: A tuple containing the width and height of the screen.
        """
        monitors = get_monitors()
        main_monitor = next((monitor for monitor in monitors if monitor.is_primary), None)
        if main_monitor is None:
            raise RuntimeError("No primary monitor found.")
        return main_monitor.width, main_monitor.height

    def start_recording(self, fps: int = 30) -> bool:
        """
        Starts a thread for capturing all video data and writing it to a file.
        :param fps: The target fps of the recording.
        :return: A boolean indicating if the recording was successfully started.
        """
        if self.is_recording:
            return False

        self.camera.start(target_fps=fps, video_mode=True)
        self.is_recording = True
        self.record_thread = threading.Thread(target=self._record)
        self.record_thread.start()
        return True

    def stop_recording(self) -> bool:
        """
        Stops the recording thread, closes the writer, and releases the video capture.
        :return: A boolean indicating if the recording was successfully stopped.
        """
        if not self.is_recording:
            return False

        self.is_recording = False
        if self.record_thread:
            self.record_thread.join()
        self.camera.stop()
        self.writer.release()
        return True

    def _record(self):
        """
        Captures and writes frames to the video file in a separate thread.
        """
        try:
            while self.is_recording:
                frame = self.camera.get_latest_frame()
                if frame is not None:
                    self.writer.write(frame)
                else:
                    print("No se pudo obtener el fotograma")
        except Exception as e:
            print(f"Error during recording: {e}")
        finally:
            self.writer.release()
            cv2.destroyAllWindows()

    def __del__(self):
        """Free resources by deleting the camera object."""
        del self.camera


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Screen Recorder")
    parser.add_argument("--output", type=str, default="output.mp4", help="Nombre del archivo de salida")
    parser.add_argument("--fps", type=int, default=30, help="Frames por segundo")
    args = parser.parse_args()

    recorder = WindowsScreenRecorder(output_path=".", filename=args.output, fps=args.fps)
    recorder.start_recording(fps=args.fps)
    print("Grabando pantalla. Presiona Ctrl+C para detener.")
    try:
        while True:
            pass  # Mantén el script corriendo
    except KeyboardInterrupt:
        recorder.stop_recording()
        print("Grabación detenida.")
