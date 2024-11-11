import numpy as np
from pylsl import StreamInlet, StreamInfo, StreamOutlet, resolve_stream
from scipy.signal import butter, lfilter
import time

# Funciones para crear y aplicar filtros de banda
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

# Parámetros del filtro
fs = 100  # Frecuencia de muestreo (ajustar según tus datos)
lowcut_alpha = 8.0
highcut_alpha = 12.0
lowcut_theta = 4.0
highcut_theta = 8.0

# Resolver el stream de AURA_Power
print("Buscando el stream 'AURA_Power'...")
streams = resolve_stream('name', 'AURA_Power')

# Crear un nuevo stream LSL para enviar triggers con un ID de fuente único
info = StreamInfo('eeg_stream', 'Markers', 1, 0, 'string', 'unique_source_id_eeg_stream_001')
outlet = StreamOutlet(info)

# Crear un inlet para el stream AURA_Power
inlet = StreamInlet(streams[0])

def send_trigger(trigger_name):
    outlet.push_sample([trigger_name])
    print(f'Trigger enviado: {trigger_name}')

# Mapa de triggers basados en el índice de relajación
def determine_trigger(value):
    if value < 0.1:
        return 'low_relaxation'
    elif value < 0.3:
        return 'medium_relaxation'
    elif value < 0.5:
        return 'high_relaxation'
    else:
        return 'very_high_relaxation'

print("Recibiendo datos del stream 'AURA_Power'...")
eeg_data = []
while True:
    sample, timestamp = inlet.pull_sample()
    if sample:
        eeg_data.append(sample[:40])  # Suponiendo que sample contiene 8 valores de los electrodos de EEG

        if len(eeg_data) >= fs * 1:  # Procesar cada 5 segundos
            eeg_data_np = np.array(eeg_data)
            eeg_data = []  # Reiniciar el buffer

            alpha_power = np.mean([np.sum(bandpass_filter(eeg_data_np[:, i], lowcut_alpha, highcut_alpha, fs)**2) for i in range(8)])
            theta_power = np.mean([np.sum(bandpass_filter(eeg_data_np[:, i], lowcut_theta, highcut_theta, fs)**2) for i in range(8)])

            relaxation_index = alpha_power / theta_power  # Índice simplificado de relajación

            print(f"Alpha Power: {alpha_power}, Theta Power: {theta_power}, Relaxation Index: {relaxation_index}")

            trigger = determine_trigger(relaxation_index)
            send_trigger(trigger)

            time.sleep(1)  # Ajusta el intervalo de tiempo según sea necesario
