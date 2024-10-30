# Backend/EyesTracking/calibrateEyeGaze.py
#  Backend/EyesTracking/EyesTrackingRecorded.py
# pip install eel
# pip install bottle-websocket
# pip install gevent
# pip install eel bottle-websocket gevent

import eel
import os

@eel.expose
def get_coordinates(x, y):
    """
    Recibe y almacena las coordenadas actuales del punto de calibración
    """
    print(f"Punto de calibración: X={x}, Y={y}")
    return x, y

def main():
    print("Iniciando servidor de Eye Tracking...")
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    eel.init(os.path.join(base_dir, 'Frontend'))
    try:
        eel.start('Templates/EyesTracking/index.html', 
                  mode=None,
                  port=8000, block=True)

    except Exception as e:
        print(f"Error al iniciar el servidor: {e}")

if __name__ == "__main__":
    main()
    print("Finished ")