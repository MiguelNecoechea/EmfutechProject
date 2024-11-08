<<<<<<< Updated upstream
#  Backend/EyesTracking/EyesTrackingRecorded.py
# pip install eel
# pip install bottle-websocket
# pip install gevent
# pip install eel bottle-websocket gevent
=======
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import json
import os
>>>>>>> Stashed changes

import eel
import os

class EyeTrackingRecorder:
    def __init__(self):
        self.current_coordinates = None
        self.coordinates_history = []

    def get_current_point(self):
        """
        Retorna las coordenadas actuales del punto de calibración
        """
        return self.current_coordinates

@eel.expose
def get_coordinates(x, y):
    """
    Recibe y almacena las coordenadas actuales del punto de calibración
    """
    print(f"Punto de calibración: X={x}, Y={y}")
    return x, y


<<<<<<< Updated upstream
def init_eel():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    eel.init(os.path.join(base_dir, 'Frontend'))
    return EyeTrackingRecorder()
=======
@app.route('/')
def home():
    # Renderiza la plantilla index.html
    return render_template('/Backend/EyesTracking/index.html')

@app.route('/log-point', methods=['POST'])
def log_point():
    data = request.json
    print(f"\nPunto registrado en tiempo real:")
    print(f"Número: {data['pointNumber']}")
    print(f"X: {data['x']} píxeles")
    print(f"Y: {data['y']} píxeles")
    print(f"Timestamp: {data['timestamp']}")
    return jsonify({"status": "success"})
>>>>>>> Stashed changes


