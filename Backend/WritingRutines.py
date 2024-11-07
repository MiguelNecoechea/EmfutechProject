"""
This will handle all the writing objects that will be executed on separated threads to avoid any locking of the main
thread, which is responsible for handling the web interface. This module also ensures a more manageable project
by making the BackendServer class more readable and maintainable.
"""

def write_gaze_traing_data(gaze_writer, gaze_vector, current_x_coordinate, current_y_coordinate) -> bool:
    """
    Writes the current gaze data and calibration point to the training file. This uses the Writing classes from the IO
    module.
    :param gaze_writer: The GazeWriter object that will be used to write the data to the file.
    """
    if gaze_vector[0] is not None and gaze_vector[1] is not None:
        combined_data = list(gaze_vector[0]) + list(gaze_vector[1]) + [current_x_coordinate, current_y_coordinate]
        gaze_writer.write(combined_data)