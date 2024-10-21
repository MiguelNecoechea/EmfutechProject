import subprocess
import platform
import os
import time
from abc import abstractmethod
from typing import Tuple


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
# "ffmpeg -f avfoundation -i \"3\" output.mp4"
# ffmpeg -f avfoundation -list_devices true -i ""
# subprocess.run(["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", "\"\""])
# subprocess.run(["ffmpeg", "-f", "avfoundation", "-i", "3", "output1.mp4"])
#
# for i in range(14):
#     print(i)
#     time.sleep(1)
#
# subprocess.run(["q"])