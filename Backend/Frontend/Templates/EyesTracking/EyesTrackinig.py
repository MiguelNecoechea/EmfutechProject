import sys
import os
import tkinter as tk


# Añadir la ruta de LaserGaze
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../IO/EyeTracking/LaserGaze'))
from GazeProcessor import GazeProcessor
from AffineTransformer import AffineTransformer
from EyeballDetector import EyeballDetector
from landmarks import detect_landmarks

# Crear una lista para almacenar las coordenadas de mapeo
mapped_coordinates = []

# Inicializar los módulos de procesamiento
gaze_processor = GazeProcessor(AffineTransformer(), EyeballDetector())

def run_eye_tracking():
    # Crear la ventana principal
    root = tk.Tk()
    root.title("Eye Tracking Simulation")
    
    # Ajustar el tamaño de la ventana a pantalla completa
    root.attributes('-fullscreen', True)
    root.configure(bg='black')

    # Crear un canvas que cubra toda la pantalla
    canvas = tk.Canvas(root, bg='black')
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # Función para cerrar la aplicación
    def close_app(event):
        root.destroy()

    # Posiciones de los 9 puntos (coordenadas en proporción al tamaño de la pantalla)
    points = [
        (0.1, 0.1),  # Esquina superior izquierda
        (0.5, 0.1),  # Centro superior
        (0.9, 0.1),  # Esquina superior derecha
        (0.1, 0.5),  # Centro izquierda
        (0.5, 0.5),  # Centro de la pantalla
        (0.9, 0.5),  # Centro derecha
        (0.1, 0.9),  # Esquina inferior izquierda
        (0.5, 0.9),  # Centro inferior
        (0.9, 0.9)   # Esquina inferior derecha
    ]

    current_point = 0  # Índice del punto actual

    # Función para mover el punto de seguimiento ocular
    def move_eye_point():
        nonlocal current_point
        canvas.delete("all")  # Limpiar el canvas

        # Obtener el tamaño actual de la ventana
        width = root.winfo_width()
        height = root.winfo_height()
        
        # Obtener las coordenadas del punto actual
        x_prop, y_prop = points[current_point]
        x = int(x_prop * width)
        y = int(y_prop * height)
        
        # Dibujar el punto en la nueva posición (ahora blanco)
        canvas.create_oval(x-20, y-20, x+20, y+20, fill="white", outline="white")

        # Procesar la posición del ojo simulada y obtener coordenadas de mirada
        face_landmarks = detect_landmarks()  # Esta función debe adaptarse para obtener los datos en tiempo real
        gaze_point = gaze_processor.process_gaze(face_landmarks)

        if gaze_point:
            mapped_coordinates.append(gaze_point)
            print(f"Punto de mirada mapeado: {gaze_point}")

        # Cambiar al siguiente punto (hay 9 puntos en total)
        current_point = (current_point + 1) % len(points)
        
        # Volver a mover el punto después de 3 segundos
        if len(mapped_coordinates) < 9:  # Sólo mapear 9 puntos
            root.after(3000, move_eye_point)
        else:
            print("Mapeo completado:", mapped_coordinates)
            # Mostrar el mensaje al usuario
            canvas.create_text(width//2, height//2, text="Presiona Enter para salir", font=("Arial", 24), fill="white")
            root.bind("<Return>", close_app)  # Esperar que el usuario presione Enter para cerrar la app

    # Comenzar la simulación
    move_eye_point()
    
    # Ejecutar la ventana principal de Tkinter
    root.mainloop()

if __name__ == "__main__":
    run_eye_tracking()
