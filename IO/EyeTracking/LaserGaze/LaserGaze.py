# -----------------------------------------------------------------------------------
# Company: TensorSense
# Project: LaserGaze
# File: LaserGaze.py
# Description: This script demonstrates a basic example of how to use the GazeProcessor class
#              from the LaserGaze project. It sets up the gaze detection system with
#              optional visualization settings and an asynchronous callback for processing
#              gaze vectors. The example provided here can be modified or extended by
#              contributors to fit specific needs or to experiment with different settings
#              and functionalities. It serves as a starting point for developers looking to
#              integrate and build upon the gaze tracking capabilities provided by the
#              GazeProcessor in their own applications.
# Author: Sergey Kuldin
# -----------------------------------------------------------------------------------
from .GazeProcessor import GazeProcessor
from .VisualizationOptions import VisualizationOptions

class LaserGaze:
    """
    This class is just a wrapper around the GazeProcessor. For some reason if the GazeProcessor is called from another
    folder is not working and I don't want to fix that inconvenience. :p
    """
    def __init__(self, automatic_start=False):
        """
        Makes a visual configuration for the visualization of the frame with the gaze vector
        :param automatic_start: Whether to initialize the recording when instantiated.
        """
        vo = VisualizationOptions()
        self.gaze_processor = GazeProcessor(visualization_options=vo)
        if automatic_start:
            self.start_camera_and_processor()

    def start_camera_and_processor(self):
        """
        Wraps the GazeProcessor starting routine.
        """
        self.gaze_processor.start()

    def get_gaze_vector_and_frame(self):
        """
        Wraps the main function of the GazeProcessor class.
        :return: A tuple of the gaze vector and the gaze frame.
        """
        return self.gaze_processor.get_gaze_vector()

    def stop(self):
        """
        Wraps the GazeProcessor.stop() method to stop the GazeProcessor.
        """
        self.gaze_processor.stop_processing()

