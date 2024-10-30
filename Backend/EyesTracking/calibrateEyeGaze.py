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

from IO.EyeTracking.LaserGaze.GazeProcessor import GazeProcessor

@eel.expose
def get_coordinates(x, y):
    """
    Recibe y almacena las coordenadas actuales del punto de calibración
    """
    print(f"Punto de calibración: X={x}, Y={y}")
    return x, y

@eel.expose
def start_eye_gaze():
    """
    Starts the eye gaze tracking
    """
    print("Iniciando seguimiento de la mirada")
    gaze_processor = GazeProcessor()
    gaze_processor.start()
    while True:
        gaze_data = gaze_processor.get_gaze_vector()
        if gaze_data[0] is not None and gaze_data[1] is not None:
            break

def main():
    print("Iniciando servidor de Eye Tracking...")
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
