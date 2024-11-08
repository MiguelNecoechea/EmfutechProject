"""
EyeGaze.py

This module handles the calibration and recording of eye gaze data using the GazeProcessor and GazeWriter classes.
It exposes several functions to the main web interface using the Eel library.

Dependencies:
- sys
- os
- time
- threading
- eel
- GazeWriter from IO.FileWriting
- GazeProcessor from IO.EyeTracking.LaserGaze

Global Variables:
- _gaze_processor: Instance of GazeProcessor used for processing gaze data.
- _data_writer: Instance of GazeWriter used for writing gaze data to a file.
- _current_x_coordinate: Current x-coordinate of the calibration point.
- _current_y_coordinate: Current y-coordinate of the calibration point.
- _recording_data: Boolean flag to control the recording of gaze data.

Functions:
- set_coordinates(x, y): Receives and stores the current calibration point coordinates.
- start_eye_gaze(): Starts the eye gaze tracking process.
- stop_eye_gaze(): Stops the eye gaze tracking process.
- start_recording(): Starts recording the gaze data in a separate thread.
- stop_recording(): Stops recording the gaze data and closes the data file.
- record_gaze_data(): Continuously records gaze data while _recording_data is True.
- write_gaze_data(): Writes the current gaze data and calibration point to the data file.
- main(): Initializes the Eel server and starts the web interface.

Usage:
Run this script to start the Eye Tracking server and expose the functions to the web interface.
"""
import sys
import os
import time

# Add the parent directory of 'IO' to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
        elif (gaze_data[0] is None and gaze_data[1] is not None) or (gaze_data[0] is not None and gaze_data[1] is None):
            gaze_processor.stop_processing()
            del gaze_processor
            time.sleep(1)
            gaze_processor = GazeProcessor()
            gaze_processor.start()