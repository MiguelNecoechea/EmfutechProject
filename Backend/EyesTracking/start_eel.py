# Backend/EyesTracking/start_eel.py
import eel
from EyesTrackingRecorded import init_eel

def main():
    print("Iniciando servidor de Eye Tracking...")
    recorder = init_eel()
    
    try:
        eel.start('Templates/EyesTracking/index.html', 
                  mode=None,
                  port=8000,
                  block=True)
    except Exception as e:
        print(f"Error al iniciar el servidor: {e}")

if __name__ == "__main__":
    main()