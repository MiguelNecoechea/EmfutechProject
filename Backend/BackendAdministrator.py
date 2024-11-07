import time
import eel
import threading
import os

from mne_lsl.stream import StreamLSL as Stream

from calibrateEyeGaze import make_prediction
from IO.FileWriting.AuraDataWriter import AuraDataWriter
from IO.FileWriting.EmotionWriter import EmotionPredictedWriter
from IO.SignalProcessing.AuraTools import rename_aura_channels, is_stream_ready
from IO.FileWriting.GazeWriter import GazeWriter
from IO.VideoProcessing.EmotionRecognizer import EmotionRecognizer

__OUT_TESTING_PATH = '/Users/mnecoea/PycharmProjects/AuraSignalProcessing/TestingOutput'
__EEL_SERVER_PORT = 8000
finished_data_collection = False

# Global Stopping function
@eel.expose
def stop_data_collection():
    global finished_data_collection
    print("Stopping data collection")
    finished_data_collection = True


# Thread specific functions to collect data using other threads.
def _data_collection_loop(stream, data_writer):
    while True:
        if is_stream_ready(stream):
            data, ts = stream.get_data()
            data_writer.write_data(ts, data)

        if finished_data_collection:
            break

    data_writer.close_file()
    stream.disconnect()
    del data_writer
    del stream

def _emotion_collection_loop(emotion_handler, emotion_writer):
    while True:
        emotion = emotion_handler.recognize_emotion()
        if emotion is not None:
            emotion = emotion[0]['dominant_emotion']
        else:
            emotion = 'Undefined'
        emotion_writer.write_data(time.time(), emotion)

        if finished_data_collection:
            break

    emotion_writer.close_file()
    del emotion_writer
    del emotion_handler

def _regressor_gaze_loop(gaze_writer):
    while True:
        gaze = make_prediction()
        if gaze is not None:
            gaze_writer.write_data(gaze)

        if finished_data_collection:
            break

    del gaze_writer

# Data specific handler for each type of "Signal" to be collected. This functions must be expiosed to the frontend.
@eel.expose
def handle_aura_signal(stream_id, buffer_size_multiplier, output_path='.', file_name='aura_data.csv'):
    stream = Stream(bufsize=buffer_size_multiplier, source_id=stream_id)
    stream.connect(processing_flags='all')
    rename_aura_channels(stream)
    channels = ['timestamp'] + stream.info['ch_names']
    data_writer = AuraDataWriter(output_path, file_name, channels)
    data_writer.create_new_file()

    data_thread = threading.Thread(target=_data_collection_loop, args=(stream, data_writer))
    data_thread.start()

@eel.expose
def handle_emotion(output_path='.', file_name='emotions.csv'):
    emotion_handler = EmotionRecognizer('opencv')
    emotion_writer = EmotionPredictedWriter(output_path, file_name)
    emotion_writer.create_new_file()

    emotion_thread = threading.Thread(target=_emotion_collection_loop, args=(emotion_handler, emotion_writer))
    emotion_thread.start()

@eel.expose
def handle_gaze():
    raise NotImplementedError("Gaze collection is not implemented yet.")

# EEL server to allow communication with the frontend.
def start_eel():
    """
     Initializes the Eel server and starts the web interface.
     """
    try:
        # Get the absolute path to the Frontend directory relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        frontend_path = os.path.join(base_dir, 'Frontend')

        print(f"Starting eye tracking server...")
        print(f"Serving files from: {frontend_path}")

        # Initialize eel with the frontend directory
        eel.init(frontend_path)

        # Start the application
        # TODO Move to localhost so it can be Ipv4 and Ipv6 compatible
        eel.start('Templates/EyesTracking/index.html',
                  mode=None,
                  host='127.0.0.1',
                  port=__EEL_SERVER_PORT,
                  block=True)

    except Exception as e:
        print(f"Error starting server: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Frontend path: {frontend_path}")

# Main function.
def main():
    global finished_data_collection
    start_eel()
    # eel_thread = threading.Thread(target=start_eel)
    # eel_thread.start()
    print("Hello main is free")
    # handle_aura_signal('AURA_Power', 1, __OUT_TESTING_PATH, 'aura_data.csv')
    # handle_emotion(__OUT_TESTING_PATH)
    # handle_gaze()
    # for i in range(5):
    #     print(i)
    #     time.sleep(1)
    # finished_data_collection = True

if __name__ == '__main__':
    main()
