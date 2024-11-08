
import eel
from mne_lsl.stream import StreamLSL as Stream
from IO.FileWriting.AuraDataWriter import AuraDataWriter
from IO.SignalProcessing.AuraTools import rename_aura_channels, is_stream_ready, delete_channels
from IO.EyeTracking.LaserGaze.GazeProcessor import GazeProcessor

# Variables para el procesamiento y la transmisión de datos
finished_data_collection = False
aura_stream = None  # Variable global para el stream de Aura
gaze_processor = GazeProcessor()  # Instancia de GazeProcessor para el seguimiento ocular

# Inicializar Eel con la ruta a los archivos frontend
eel.init('Frontend')

@eel.expose
def connect_aura(stream_id='filtered', buffer_size_multiplier=1):
    global aura_stream
    try:
        aura_stream = Stream(bufsize=buffer_size_multiplier, source_id=stream_id)
        aura_stream.connect(processing_flags='all')
        rename_aura_channels(aura_stream)
        print("Aura connected with channels:", aura_stream.info['ch_names'])
        return {"status": "success", "message": "Aura connected successfully."}
    except Exception as e:
        print("Error connecting Aura:", str(e))
        return {"status": "error", "message": str(e)}

@eel.expose
def disconnect_aura():
    global aura_stream
    try:
        if aura_stream:
            aura_stream.disconnect()
            aura_stream = None
            print("Aura disconnected.")
            return {"status": "success", "message": "Aura disconnected."}
        else:
            print("No Aura stream to disconnect.")
            return {"status": "error", "message": "No Aura stream to disconnect."}
    except Exception as e:
        print("Error disconnecting Aura:", str(e))
        return {"status": "error", "message": str(e)}

@eel.expose
def refresh_channels():
    global aura_stream
    try:
        channels = aura_stream.info['ch_names'] if aura_stream else []
        print("Available Aura channels:", channels)
        return channels
    except Exception as e:
        print("Error refreshing channels:", str(e))
        return {"status": "error", "message": str(e)}

@eel.expose
def remove_channels(channels_to_remove):
    global aura_stream
    try:
        if aura_stream:
            delete_channels(aura_stream, [], channels_to_remove)
            print(f"Channels {channels_to_remove} removed successfully.")
            return {"status": "success", "message": "Channels removed successfully."}
        else:
            print("No Aura stream connected.")
            return {"status": "error", "message": "No Aura stream connected."}
    except Exception as e:
        print("Error removing channels:", str(e))
        return {"status": "error", "message": str(e)}

@eel.expose
def save_route(route_type):
    print(f"Saving route type '{route_type}'.")
    return {"status": "success", "message": f"Route type '{route_type}' saved successfully."}

@eel.expose
def select_channels(selected_channels):
    print(f"Channels selected for analysis: {', '.join(selected_channels)}")
    return {"status": "success", "message": f"Channels {', '.join(selected_channels)} selected successfully."}

# Funciones específicas para el GazeProcessor
@eel.expose
def start_eye_gaze():
    try:
        gaze_processor.start()
        print("Gaze Processor started.")
        return {"status": "success", "message": "Gaze Processor started."}
    except Exception as e:
        print("Error starting Gaze Processor:", str(e))
        return {"status": "error", "message": str(e)}

@eel.expose
def stop_eye_gaze():
    try:
        gaze_processor.stop_processing()
        print("Gaze Processor stopped.")
        return {"status": "success", "message": "Gaze Processor stopped."}
    except Exception as e:
        print("Error stopping Gaze Processor:", str(e))
        return {"status": "error", "message": str(e)}

@eel.expose
def get_gaze_data():
    try:
        left_gaze, right_gaze, frame = gaze_processor.get_gaze_vector()
        return {
            "status": "success",
            "data": {
                "left_gaze": left_gaze.tolist() if left_gaze is not None else None,
                "right_gaze": right_gaze.tolist() if right_gaze is not None else None
            }
        }
    except Exception as e:
        print("Error getting gaze data:", str(e))
        return {"status": "error", "message": str(e)}

# Iniciar el servidor Eel y exponer los puntos de entrada para frontend
if __name__ == "__main__":
    try:
        eel.start('Templates/Configuration/configuration.html', port=8000)
    except Exception as e:
        print(f"Error starting Eel server: {e}")
