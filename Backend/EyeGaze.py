"""
EyeGaze.py

This module provides functionality for eye gaze tracking and calibration. It creates and manages a GazeProcessor instance
that interfaces with eye tracking hardware to obtain gaze vector data.

The module is designed to be resilient, with automatic retry logic if the initial eye tracking connection fails.

Dependencies:
- sys
- os
- time
- IO.EyeTracking.LaserGaze.GazeProcessor

Functions:
- create_new_eye_gaze(): Creates and initializes a GazeProcessor instance, retrying until valid gaze data is obtained.
  Returns a working GazeProcessor object.

Usage:
This module is typically used as part of a larger eye tracking system, where the GazeProcessor instance is used to
obtain real-time gaze vector data for further processing or analysis.
"""
import sys
import os
import time

from IO.EyeTracking.LaserGaze.GazeProcessor import GazeProcessor

def create_new_eye_gaze() -> GazeProcessor:
    """
    Attempts to create a working instance of the GazeProcessor class. If the instance cannot be created, it will retry
    until it is successful. To achieve this, the object will be deleted and recreated if the gaze data is not valid.
    This function can take a while to complete, as it waits for the gaze data to be valid.
    """
    gaze_processor = GazeProcessor()
    gaze_processor.start()

    while True:
        gaze_data = gaze_processor.get_gaze_vector()
        if gaze_data[0] is not None and gaze_data[1] is not None:
            return gaze_processor
