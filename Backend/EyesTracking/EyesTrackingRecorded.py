# -----------------------------------------------------------------------------------
# Nombre:       EyesTrackingRecorded.py
# Descripción:  Este script define un servidor web que recibe y almacena datos de calibración
#               para el sistema de Eye Tracking. Los datos se almacenan en archivos JSON en una
#               carpeta local. El servidor también proporciona una interfaz web para visualizar
#               los datos de calibración y permite registrar puntos en tiempo real.
# Autor:        Iván Alemán 
# Fecha:        19 de Agosto de 2021
# Primero se inicia el servidor de Eye Tracking con el comando "python EyesTrackingRecorded.py"
# Luego se ejecuta el script de calibración con el comando "python run_calibration.py"
# Finalmente, se abre un navegador web en la dirección "http://localhost:5000" para realizar la calibración.
# corremos el electron con "npm start" y abrimos el navegador en "http://localhost:3000" para visualizar la interfaz de calibración.

# -----------------------------------------------------------------------------------
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)

# Ruta base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(BASE_DIR, 'Frontend')

class EyeTrackingRecorder:
    def __init__(self):
        self.data_folder = os.path.join(os.path.dirname(__file__), "recorded_data")
        self.calibration_data = []
        self.ensure_data_folder_exists()

    def ensure_data_folder_exists(self):
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)

    def process_and_save_coordinates(self, coordinates):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.data_folder, f"calibration_data_{timestamp}.json")

        processed_data = {
            "timestamp": timestamp,
            "total_points": len(coordinates),
            "points": coordinates,
            "statistics": self.calculate_statistics(coordinates)
        }

        with open(filename, 'w') as f:
            json.dump(processed_data, f, indent=4)

        self.calibration_data = processed_data
        return processed_data

    def calculate_statistics(self, coordinates):
        if not coordinates:
            return None

        x_coords = [point['x'] for point in coordinates]
        y_coords = [point['y'] for point in coordinates]

        return {
            "average_x": sum(x_coords) / len(x_coords),
            "average_y": sum(y_coords) / len(y_coords),
            "min_x": min(x_coords),
            "max_x": max(x_coords),
            "min_y": min(y_coords),
            "max_y": max(y_coords)
        }

    def get_calibration_data(self):
        return self.calibration_data

recorder = EyeTrackingRecorder()

@app.route('/')
def serve_index():
    return send_from_directory(os.path.join(FRONTEND_DIR, 'Templates', 'EyesTracking'), 'index.html')

@app.route('/Frontend/<path:path>')
def serve_frontend(path):
    return send_from_directory(FRONTEND_DIR, path)

@app.route('/log-point', methods=['POST'])
def log_point():
    data = request.json
    print(f"\nPunto registrado en tiempo real:")
    print(f"Número: {data['pointNumber']}")
    print(f"X: {data['x']} píxeles")
    print(f"Y: {data['y']} píxeles")
    print(f"Timestamp: {data['timestamp']}")
    return jsonify({"status": "success"})

@app.route('/save-calibration', methods=['POST'])
def save_calibration():
    data = request.json
    processed_data = recorder.process_and_save_coordinates(data)
    return jsonify({
        "status": "success",
        "data": processed_data
    })

def start_calibration():
    return recorder

if __name__ == '__main__':
    print("Servidor de Eye Tracking iniciado...")
    print("Esperando datos de calibración...")
    app.run(debug=True, port=5000)