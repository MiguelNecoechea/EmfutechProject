from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)

class EyeTrackingRecorder:
    def __init__(self):
        self.data_folder = "recorded_data"
        self.ensure_data_folder_exists()

    def ensure_data_folder_exists(self):
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)

    def save_coordinates(self, coordinates):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.data_folder}/calibration_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(coordinates, f, indent=4)
        
        print("\n=== Datos de Calibración ===")
        print(f"Timestamp: {timestamp}")
        for point in coordinates:
            print(f"\nPunto {point['pointNumber']}:")
            print(f"X: {point['x']} píxeles")
            print(f"Y: {point['y']} píxeles")
            print(f"Timestamp: {point['timestamp']}")
        
        print(f"\nDatos guardados en: {filename}")
        return filename

recorder = EyeTrackingRecorder()

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
    filename = recorder.save_coordinates(data)
    return jsonify({
        "status": "success",
        "filename": filename
    })

if __name__ == '__main__':
    print("Servidor de Eye Tracking iniciado...")
    print("Esperando datos de calibración...")
    app.run(port=5000)