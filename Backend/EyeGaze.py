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
import threading

# Add the parent directory of 'IO' to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from IO.FileWriting.GazeWriter import GazeWriter
from IO.EyeTracking.LaserGaze.GazeProcessor import GazeProcessor
from Backend.EyeCoordinateRegressor import PositionRegressor

_gaze_processor = GazeProcessor()
__trining_data_writer = GazeWriter('data', 'training_data.csv')
_current_x_coordinate = 0
_current_y_coordinate = 0
_recording_data = False
_regressor = None
_regressor_running = False

# Functions exposed to the web interface
def set_coordinates(x, y):
    """
    Receives and stores the current calibration point coordinates. the coordinates are retrieved from the javascript
    generator of points.

    Args:
        x (int): The x-coordinate of the calibration point.
        y (int): The y-coordinate of the calibration point.
    """
    global _current_y_coordinate
    global _current_x_coordinate
    _current_x_coordinate = x
    _current_y_coordinate = y

def start_eye_gaze():
    """
    Starts the eye gaze tracking and attempts to perform the internal calibration of the gaze processor.
    When the calibration is unsuccessful, the gaze processor is restarted by deleting it from memory and creating a new
    instance.
    """
    global _gaze_processor
    print("Starting eye gaze tracking...")
    _gaze_processor.start()

    while True:
        gaze_data = _gaze_processor.get_gaze_vector()
        if gaze_data[0] is not None and gaze_data[1] is not None:
            break
        elif (gaze_data[0] is None and gaze_data[1] is not None) or (gaze_data[0] is not None and gaze_data[1] is None):
            _gaze_processor.stop_processing()
            del _gaze_processor
            time.sleep(1)
            _gaze_processor = GazeProcessor()
            _gaze_processor.start()

def stop_eye_gaze():
    """
    Stops the eye gaze tracking process. This function should be called when the experiment is over or the user wants to
    stop the gaze tracking.
    """
    _gaze_processor.stop_processing()

def start_recording_training_data():
    """
    Starts recording the gaze data in a separate thread. The recording will continue until stop_recording is called.
    :return:
    """
    global _recording_data
    _recording_data = True
    recording_thread = threading.Thread(target=record_gaze_training_data)
    recording_thread.start()

def stop_recording_training_data():
    """
    Stops recording the gaze data and closes the data file. This function should be called when the training is over.
    :return:
    """
    global _recording_data
    _recording_data = False
    __trining_data_writer.close_file()

def start_regressor():
    """
    Starts the regressor thread. This function is called when the user wants to start the predictions of the eye position
    based on the gaze vector. When the final version is up this function will be called when the experiment begins.
    :return:
    """
    global _regressor
    global _regressor_running
    _regressor = PositionRegressor('data/training_data.csv')
    _regressor_running = True
    _regressor.train_create_model()

def stop_regression():
    """
    Stops the regressor thread. by setting a boolean to false.
    """
    global _regressor_running
    _regressor_running = False

# Python only functions
def record_gaze_training_data():
    """
    Continuously records gaze data while _recording_data is True. This function is supposed to run in a separate thread.
    :return:
    """
    global _recording_data
    while True:
        write_gaze_traing_data()
        if not _recording_data:
            break

def write_gaze_traing_data():
    """
    Writes the current gaze data and calibration point to the data file. This uses the Writing classes from the IO
    module.
    """
    data = _gaze_processor.get_gaze_vector()
    if data[0] is not None and data[1] is not None:
        combined_data = list(data[0]) + list(data[1]) + [_current_x_coordinate, _current_y_coordinate]
        __trining_data_writer.write(combined_data)

def make_prediction():
    if _regressor is None:
        raise RuntimeError("Regressor not trained yet")
    gaze_data = _gaze_processor.get_gaze_vector()
    if gaze_data[0] is not None and gaze_data[1] is not None:
        data = [[gaze_data[0][0], gaze_data[0][1], gaze_data[0][2], gaze_data[1][0], gaze_data[1][1], gaze_data[1][2]]]
        result = _regressor.make_prediction(data)
        return result
    return None
