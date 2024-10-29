
# Purpose: Run the calibration system and save a summary of the results in a text file.
# Type: Script
# Version: 1.0
# Este script ejecuta el sistema de calibración de la mirada y guarda un resumen de los resultados en un archivo de texto.
# El sistema de calibración se ejecuta en un servidor web local y se accede a través de un navegador web.
# El resumen de los resultados se guarda en un archivo de texto en la misma carpeta que este script.
# El resumen incluye la fecha y hora de la calibración, el total de puntos registrados, estadísticas de los puntos registrados
# y los valores de cada punto registrado.
# El script también imprime los resultados en la consola.
# -----------------------------------------------------------------------------------
from EyesTrackingRecorded import start_calibration
import webbrowser
import time
from datetime import datetime
import os

def run_calibration_and_return_data():
    print("Iniciando sistema de calibración...")
    recorder = start_calibration()
    
    print("Abriendo interfaz de calibración...")
    webbrowser.open('http://localhost:5000')
    
    print("Esperando datos de calibración...")
    max_wait_time = 300
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        data = recorder.get_calibration_data()
        if data:
            return data
        time.sleep(1)
    
    return None

def save_calibration_summary(data):
    if not data:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(os.path.dirname(__file__), f"calibration_summary_{timestamp}.txt")
    
    with open(filename, 'w') as f:
        f.write("=== Resumen de Calibración ===\n\n")
        f.write(f"Fecha y hora: {data['timestamp']}\n")
        f.write(f"Total de puntos: {data['total_points']}\n\n")
        
        stats = data['statistics']
        f.write("Estadísticas:\n")
        f.write(f"Promedio X: {stats['average_x']:.2f}\n")
        f.write(f"Promedio Y: {stats['average_y']:.2f}\n")
        f.write(f"Rango X: {stats['min_x']} - {stats['max_x']}\n")
        f.write(f"Rango Y: {stats['min_y']} - {stats['max_y']}\n\n")
        
        f.write("Puntos registrados:\n")
        for point in data['points']:
            f.write(f"Punto {point['pointNumber']}: X={point['x']}, Y={point['y']}\n")
    
    print(f"\nResumen guardado en: {filename}")
    return filename

def main():
    calibration_data = run_calibration_and_return_data()
    
    if calibration_data:
        print("\n=== Resultados de Calibración ===")
        print(f"Total de puntos: {calibration_data['total_points']}")
        
        stats = calibration_data['statistics']
        print("\nEstadísticas:")
        print(f"Promedio X: {stats['average_x']:.2f}")
        print(f"Promedio Y: {stats['average_y']:.2f}")
        print(f"Rango X: {stats['min_x']} - {stats['max_x']}")
        print(f"Rango Y: {stats['min_y']} - {stats['max_y']}")
        
        summary_file = save_calibration_summary(calibration_data)
        return {
            "calibration_data": calibration_data,
            "summary_file": summary_file
        }
    
    print("No se obtuvieron datos de calibración")
    return None

if __name__ == "__main__":
    result = main()