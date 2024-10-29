#  Backend/EyesTracking/EyesTrackingRecorded.py
# pip install eel
# pip install bottle-websocket
# pip install gevent
# pip install eel bottle-websocket gevent

import eel
import os
from datetime import datetime
class EyeTrackingRecorder:
    def __init__(self):
        self.current_coordinates = None
        self.coordinates_history = []
        
    @eel.expose
    def get_coordinates(self, x, y):
        """
        Recibe y almacena las coordenadas actuales del punto de calibración
        """
        self.current_coordinates = (x, y)
        self.coordinates_history.append((x, y))
        print(f"Punto de calibración: X={x}, Y={y}")
        return x, y
    
    def get_current_point(self):
        """
        Retorna las coordenadas actuales del punto de calibración
        """
        return self.current_coordinates

def init_eel():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    eel.init(os.path.join(base_dir, 'Frontend'))
    return EyeTrackingRecorder()


