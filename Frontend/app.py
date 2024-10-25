import sys
import os
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'Templates/EyesTracking'))
from EyesTrackinig import run_eye_tracking


# Importar la función que ejecutará la interfaz de Eye Tracking
from Templates.EyesTracking.EyesTrackinig import run_eye_tracking

if __name__ == "__main__":
    run_eye_tracking()  # Ejecutar la 
    