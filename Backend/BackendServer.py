import json
import zmq
import time
import threading
import signal
import sys
from contextlib import contextmanager

from mne_lsl.stream import StreamLSL as Stream

from EyeGaze import make_prediction
from IO.FileWriting.AuraDataWriter import AuraDataWriter
from IO.FileWriting.EmotionWriter import EmotionPredictedWriter
from IO.SignalProcessing.AuraTools import rename_aura_channels, is_stream_ready
from IO.FileWriting.GazeWriter import GazeWriter
from IO.VideoProcessing.EmotionRecognizer import EmotionRecognizer

class BackendServer:
    def __init__(self, port="5556"):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind(f"tcp://*:{port}")
        self.running = False
        self.data_collection_active = False
        self.threads = []

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def cleanup(self):
        """Clean up resources before shutting down"""
        self.running = False
        self.data_collection_active = False

        # Wait for all threads to complete
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)

        # Clean up ZMQ resources
        if hasattr(self, 'socket') and self.socket:
            self.socket.close()
        if hasattr(self, 'context') and self.context:
            self.context.term()

    @contextmanager
    def thread_tracking(self, thread):
        """Context manager to track active threads"""
        self.threads.append(thread)
        try:
            yield thread
        finally:
            if thread in self.threads:
                self.threads.remove(thread)

    def signal_handler(self, signum, frame):
        print("Signal received, cleaning up...")
        self.cleanup()
        sys.exit(0)

    def start(self):
        self.running = True
        print("Backend server started...")
        while self.running:
            try:
                message = self.socket.recv_json(flags=zmq.NOBLOCK)
                response = self.handle_message(message)
                if response:
                    self.socket.send_json(response)
            except zmq.error.Again:
                # No message available, sleep briefly
                time.sleep(0.001)
            except Exception as e:
                print(f"Error handling message: {e}")
                try:
                    self.socket.send_json({"error": str(e)})
                except:
                    pass


    def handle_message(self, message):
        command = message.get("command")
        params = message.get("params", {})

        handlers = {
            "start_eye_gaze": self.handle_eye_gaze,
            "start_recording_training_data": self.handle_training_data,
            "stop_recording_training_data": self.handle_stop_recording,
            "set_coordinates": self.handle_coordinates,
            "start_regressor": self.handle_regressor,
            "handle_aura_signal": self.handle_aura_signal,
            "handle_emotion": self.handle_emotion,
            "stop": self.handle_stop
        }

        handler = handlers.get(command)
        if handler:
            return handler(**params)
        return {"error": f"Unknown command: {command}"}

    def handle_eye_gaze(self):
        # Your eye gaze initialization code here
        print("Eye gaze tracking started")
        return {"status": "success", "message": "Eye gaze tracking started"}

    def handle_training_data(self):
        self.data_collection_active = True
        # Initialize training data collection
        return {"status": "success", "message": "Training data recording started"}

    def handle_stop_recording(self):
        self.data_collection_active = False
        # Cleanup code here
        return {"status": "success", "message": "Recording stopped"}

    def handle_coordinates(self, x, y):
        # Handle the coordinates update
        print(f"Coordinates updated: {x}, {y}")
        return {"status": "success", "coordinates": [x, y]}

    def handle_regressor(self):
        # Start your regressor
        return {"status": "success", "message": "Regressor started"}

    def handle_aura_signal(self, stream_id, buffer_size_multiplier, output_path='.', file_name='aura_data.csv'):
        try:
            stream = Stream(bufsize=buffer_size_multiplier, source_id=stream_id)
            stream.connect(processing_flags='all')
            rename_aura_channels(stream)
            channels = ['timestamp'] + stream.info['ch_names']

            data_writer = AuraDataWriter(output_path, file_name, channels)
            data_writer.create_new_file()

            # Start data collection in a separate thread
            thread = threading.Thread(
                target=self._data_collection_loop,
                args=(stream, data_writer)
            )
            thread.start()

            return {"status": "success", "message": "Aura signal handling started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def handle_emotion(self, output_path='.', file_name='emotions.csv'):
        try:
            emotion_handler = EmotionRecognizer('opencv')
            emotion_writer = EmotionPredictedWriter(output_path, file_name)
            emotion_writer.create_new_file()

            # Start emotion recognition in a separate thread
            thread = threading.Thread(
                target=self._emotion_collection_loop,
                args=(emotion_handler, emotion_writer)
            )
            thread.start()

            return {"status": "success", "message": "Emotion recognition started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def handle_stop(self):
        print("Stopping server...")
        self.cleanup()
        return {"status": "success", "message": "Server stopped"}

    def _data_collection_loop(self, stream, data_writer):
        while self.data_collection_active:
            if is_stream_ready(stream):
                data, ts = stream.get_data()
                data_writer.write_data(ts, data)
            time.sleep(0.001)  # Small sleep to prevent CPU overuse

        data_writer.close_file()
        stream.disconnect()

    def _emotion_collection_loop(self, emotion_handler, emotion_writer):
        while self.data_collection_active:
            emotion = emotion_handler.recognize_emotion()
            if emotion is not None:
                emotion = emotion[0]['dominant_emotion']
            else:
                emotion = 'Undefined'
            emotion_writer.write_data(time.time(), emotion)
            time.sleep(0.1)  # Adjust sleep time based on your needs

        emotion_writer.close_file()


if __name__ == "__main__":
    server = BackendServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Keyboard interrupt received")
    finally:
        server.cleanup()
