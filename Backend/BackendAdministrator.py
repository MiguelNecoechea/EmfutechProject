import eel
from mne_lsl.stream import StreamLSL as Stream
from IO.FileWriting.AuraDataWriter import AuraDataWriter
from IO.SignalProcessing.AuraTools import rename_aura_channels, is_stream_ready, delete_channels

# Estado para controlar si la recopilación de datos debe detenerse
finished_data_collection = False
aura_stream = None  # Variable global para el stream de Aura

# Inicializar Eel
eel.init('Frontend')

@eel.expose
def connect_aura(stream_id='filtered', buffer_size_multiplier=1):
    global aura_stream
    try:
        aura_stream = Stream(bufsize=buffer_size_multiplier, source_id=stream_id)
        aura_stream.connect(processing_flags='all')
        rename_aura_channels(aura_stream)
        print("Aura conectado correctamente con los canales:", aura_stream.info['ch_names'])
        return {"status": "success", "message": "Aura connected successfully."}
    except Exception as e:
        print("Error al conectar Aura:", str(e))
        return {"status": "error", "message": str(e)}

@eel.expose
def disconnect_aura():
    global aura_stream
    try:
        if aura_stream:
            aura_stream.disconnect()
            aura_stream = None
            print("Aura desconectado correctamente.")
            return {"status": "success", "message": "Aura disconnected successfully."}
        else:
            print("No hay un stream de Aura para desconectar.")
            return {"status": "error", "message": "No Aura stream to disconnect."}
    except Exception as e:
        print("Error al desconectar Aura:", str(e))
        return {"status": "error", "message": str(e)}

@eel.expose
def refresh_channels():
    global aura_stream
    try:
        channels = aura_stream.info['ch_names'] if aura_stream else []
        print("Canales disponibles para Aura:", channels)  # Debug
        return channels
    except Exception as e:
        print("Error al refrescar canales:", str(e))
        return {"status": "error", "message": str(e)}

@eel.expose
def remove_channels(channels_to_remove):
    global aura_stream
    try:
        if aura_stream:
            delete_channels(aura_stream, [], channels_to_remove)
            print(f"Canales {channels_to_remove} eliminados correctamente.")
            return {"status": "success", "message": "Channels removed successfully."}
        else:
            print("No hay un stream de Aura conectado.")
            return {"status": "error", "message": "No Aura stream connected."}
    except Exception as e:
        print("Error al eliminar canales:", str(e))
        return {"status": "error", "message": str(e)}

@eel.expose
def save_route(route_type):
    print(f"Guardando ruta de tipo '{route_type}'.")  # Debug
    return {"status": "success", "message": f"Route type '{route_type}' saved successfully."}

@eel.expose
def select_channels(selected_channels):
    print(f"Canales seleccionados para análisis: {', '.join(selected_channels)}")  # Debug
    return {"status": "success", "message": f"Channels {', '.join(selected_channels)} selected successfully."}

# Función principal para ejecutar el servidor Eel en el puerto 8000
if __name__ == "__main__":
    eel.start('Templates/Configuration/configuration.html', port=8000)
