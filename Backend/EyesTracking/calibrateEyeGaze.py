# Backend/EyesTracking/calibrateEyeGaze.py
#  Backend/EyesTracking/EyesTrackingRecorded.py
# pip install eel
# pip install bottle-websocket
# pip install gevent
# pip install eel bottle-websocket gevent

import sys
import os


# Add the parent directory of 'IO' to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import eel
from IO.FileWriting.GazeWriter import GazeWriter
from IO.EyeTracking.LaserGaze.GazeProcessor import GazeProcessor

_gaze_processor = GazeProcessor()
_data_writer = GazeWriter('data', 'gaze_data.csv')
_current_x_coordinate = 0
_current_y_coordinate = 0

@eel.expose
def set_coordinates(x, y):
    """
    Recibe y almacena las coordenadas actuales del punto de calibración
    """
    _current_x_coordinate = x
    _current_y_coordinate = y
    print(f"Punto de calibración: X={_current_x_coordinate}, Y={_current_y_coordinate}")
    if _gaze_processor.running:
        gaze_vector = _gaze_processor.get_gaze_vector()
        print(f"left: {gaze_vector[0]}, right: {gaze_vector[1]}")

    else:
        print("I am closed")


@eel.expose
def start_eye_gaze():
    """
    Starts the eye gaze tracking
    """
    _gaze_processor.start()
    while True:
        gaze_data = _gaze_processor.get_gaze_vector()
        print(f"left: {gaze_data[0]}, right: {gaze_data[1]}")
        if gaze_data[0] is not None and gaze_data[1] is not None:
            break

@eel.expose
def stop_eye_gaze():
    _gaze_processor.stop_processing()


def write_gaze_data():
    data = _gaze_processor.get_gaze_vector()

    # _data_writer.write_gaze_data(data)

def main():
    print("Iniciando servidor de Eye Tracking...")
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _data_writer.create_new_file()

    eel.init(os.path.join(base_dir, 'Frontend'))
    try:
        print("Starting Eel server...")
        eel.start('Templates/EyesTracking/index.html',
                  mode=None,
                  port=8000, block=True)
    except Exception as e:
        print(f"Error al iniciar el servidor: {e}")

if __name__ == "__main__":
    main()
