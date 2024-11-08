import zmq
import time
import threading
import signal
import sys
import os
from contextlib import contextmanager


# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mne_lsl.stream import StreamLSL as Stream
from IO.FileWriting.CoordinateWriter import CoordinateWriter

from EyeGaze import create_new_eye_gaze
from IO.FileWriting.AuraDataWriter import AuraDataWriter
from EyeCoordinateRegressor import PositionRegressor
from IO.FileWriting.EmotionWriter import EmotionPredictedWriter
from IO.SignalProcessing.AuraTools import rename_aura_channels, is_stream_ready, rename_40_channels
from IO.FileWriting.GazeWriter import GazeWriter
from IO.VideoProcessing.EmotionRecognizer import EmotionRecognizer

class BackendServer:
    def __init__(self, port="5556"):
        # Server setup
        self.aura_training_thread = None
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind(f"tcp://*:{port}")

        # Training points coordinates
        self.current_x_coordinate = 0
        self.current_y_coordinate = 0

        self.running = False
        self.fitting_eye_gaze = False
        self.eye_gaze_running = False

        self.emotion_handler = None
        self.eye_gaze = None
        self.stream = None
        self.regressor = None

        # Threads for the data collection
        self.aura_thread = None
        self.emotion_thread = None
        self.regressor_thread = None
        channels_names = rename_40_channels()
        channels_names = ['timestamp'] + [channels_names[str(i)] for i in range(40)]
        # Writers for the training and reference data

        # Gaze
        self.gaze_writer_training = GazeWriter('training', 'training_gaze.csv')
        self.gaze_writer_training.create_new_file()

        # Aura
        self.aura_writer_training = AuraDataWriter('training', 'training_aura.csv', channels_names)
        self.aura_writer_training.create_new_file()

        # Writers for the actual output data

        # Coordinate
        self._coordinate_writer = CoordinateWriter('testing', 'testing_gaze.csv')
        self._coordinate_writer.create_new_file()

        # Emotion
        self.emotion_writer = EmotionPredictedWriter('testing', 'testing_emotions.csv')
        self.emotion_writer.create_new_file()

        # Aura
        self.aura_writer = AuraDataWriter('testing', 'testing_aura.csv', channels_names)
        self.aura_writer.create_new_file()

        # Status for the data collection loops
        self.data_collection_active = False
        self.training_data_collection_active = False
        self.threads = []

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    # Server Handling Functions
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

    def signal_handler(self, signum, frame):
        print("Signal received, cleaning up...")
        self.cleanup()
        sys.exit(0)

    # Server Handling Functions End

    # Thread Management Functions
    @contextmanager
    def thread_tracking(self, thread):
        """Context manager to track active threads"""
        self.threads.append(thread)
        try:
            yield thread
        finally:
            if thread in self.threads:
                self.threads.remove(thread)

    # Thread Management Functions End

    def handle_message(self, message):
        command = message.get("command")
        params = message.get("params", {})

        handlers = {
            "start_eye_gaze": self.handle_eye_gaze,
            "calibrate_eye_tracking": self.start_et_calibration,
            "start_testing": self.start_testing,
            "stop_testing": self.handle_stop_testing,
            "start_regressor": self.handle_regressor,
            "connect_aura": self.handle_aura_signal,
            "start_emotions": self.handle_emotion,
            "start_recording_training_data": self.handle_training_data,
            "stop_recording_training_data": self.handle_stop_recording_traing_data,
            "set_coordinates": self.handle_coordinates,
            "stop": self.handle_stop
        }
        print(message)
        handler = handlers.get(command)
        if handler:
            return handler(**params)
        else:
            return {"error": f"Unknown command: {command}"}

    # Message Handling Functions

    def handle_eye_gaze(self):

        def eye_gaze_task():
            self.eye_gaze = create_new_eye_gaze()
            print("Eye gaze tracking started")
            self.eye_gaze_running = True


        if not self.fitting_eye_gaze:
            self.fitting_eye_gaze = True
            local_thread = threading.Thread(target=eye_gaze_task)
            local_thread.start()
            return {"status": "success", "message": "Eye gaze tracking started"}
        else:
            return {"status": "error", "message": "Eye gaze tracking already started"}

    def start_et_calibration(self):
        if self.eye_gaze_running:
            if self.stream is not None:
                aura_thread = threading.Thread(
                    target=self._aura_data_collection_loop,
                    args=('training',)
                )
                aura_thread.start()
            return {"status": "start-calibration", "message": "Eye gaze tracking started"}
        else:
            return {"status": "error", "message": "Eye gaze tracking not started"}

    def start_testing(self):
        if not self.data_collection_active:
            self.data_collection_active = True

            if self.aura_thread is not None:
                self.aura_thread.start()
            if self.emotion_thread is not None:
                self.emotion_thread.start()
            if self.regressor_thread is not None:
                self.regressor_thread.start()

            return {"status": "success", "message": "Eye gaze tracking started"}
        else:
            return {"status": "error", "message": "Testing already started"}

    def handle_stop(self):
        print("Stopping server...")
        self.cleanup()
        return {"status": "success", "message": "Server stopped"}

    def handle_training_data(self):
        self.training_data_collection_active = True
        def training_data_task():
            while True:
                # Make prediction and write to file
                gaze_vector = self.eye_gaze.get_gaze_vector()
                if self.current_y_coordinate != 0 and self.current_x_coordinate != 0:
                    data = []
                    for i in gaze_vector[0]:
                        data.append(i)
                    for i in gaze_vector[1]:
                        data.append(i)
                    data.append(self.current_x_coordinate)
                    data.append(self.current_y_coordinate)
                    # data = gaze_vector[0] + gaze_vector[1] + [self.current_x_coordinate, self.current_y_coordinate]
                    self.gaze_writer_training.write(data)
                if self.training_data_collection_active is False:
                    self.gaze_writer_training.close_file()
                    break

        if self.eye_gaze_running:
            print("Starting training data recording")
            local_thread = threading.Thread(target=training_data_task)
            local_thread.start()
            return {"status": "success", "message": "Training data recording started"}
        else:
            print("Eye gaze tracking not started")
            return {"status": "error", "message": "Eye gaze tracking not started"}

    def handle_stop_recording(self):
        self.data_collection_active = False
        return {"status": "success", "message": "Recording stopped"}

    def handle_coordinates(self, x, y):
        # Handle the coordinates update
        print(f"Coordinates updated: {x}, {y}")
        self.current_x_coordinate = x
        self.current_y_coordinate = y
        return {"status": "success", "coordinates": [x, y]}

    def handle_regressor(self):
        # Start your regressor
        self.regressor = PositionRegressor('training/training_gaze.csv')
        self.regressor.train_create_model()
        self.regressor_thread = threading.Thread(
            target=self._coordinate_regressor_loop
        )

        return {"status": "success", "message": "Regressor started"}

    def handle_aura_signal(self, stream_id='AURA_Power', buffer_size_multiplier=1):
        try:
            self.stream = Stream(bufsize=buffer_size_multiplier, source_id=stream_id)
            self.stream.connect(processing_flags='all')
            rename_aura_channels(self.stream)
            # Start data collection in a separate thread
            self.aura_thread = threading.Thread(
                target=self._aura_data_collection_loop,
                args=('testing',)
            )
            
            self.aura_training_thread = threading.Thread(
                target=self._aura_data_collection_loop,
                args=('training',)
            )

            return {"status": "success", "message": "Aura signal handling started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def handle_emotion(self, output_path='.', file_name='emotions.csv'):
        try:
            self.emotion_handler = EmotionRecognizer('opencv')

            # Start emotion recognition in a separate thread
            self.emotion_thread = threading.Thread(
                target=self._emotion_collection_loop
            )

            return {"status": "success", "message": "Emotion recognition started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def handle_stop_testing(self):
        self.data_collection_active = False
        return {"status": "success", "message": "Testing stopped"}

    def handle_stop_recording_traing_data(self):
        self.training_data_collection_active = False
        return {"status": "success", "message": "Training data recording stopped"}

    # End of Message Handling Functions

    # Internal data collection loops
    def _aura_data_collection_loop(self, type):
        while True:
            if is_stream_ready(self.stream):
                data, ts = self.stream.get_data()
                if type == 'training':
                    self.aura_writer_training.write_data(ts, data)
                else:
                    self.aura_writer.write_data(ts, data)

            time.sleep(0.001)  # Small sleep to prevent CPU overuse

            if type == 'training' and self.training_data_collection_active is False:
                self.aura_writer_training.close_file()
                break
            elif type == 'testing' and self.data_collection_active is False:
                self.aura_writer.close_file()
                break
        # stream.disconnect()

    def _emotion_collection_loop(self):
        while True:
            emotion = self.emotion_handler.recognize_emotion()
            if emotion is not None:
                emotion = emotion[0]['dominant_emotion']
            else:
                emotion = 'Undefined'
            self.emotion_writer.write_data(time.time(), emotion)
            time.sleep(0.01)  # Adjust sleep time based on your needs
            if not self.data_collection_active:
                break

        self.emotion_writer.close_file()

    def _coordinate_regressor_loop(self):
        while True:
            gaze_vector = self.eye_gaze.get_gaze_vector()
            if gaze_vector[0] is not None and gaze_vector[1] is not None:
                gaze_vector_list = [[gaze_vector[0][0], gaze_vector[0][1], gaze_vector[0][2], gaze_vector[1][0], gaze_vector[1][1], gaze_vector[1][2]]]
                data = self.regressor.make_prediction(gaze_vector_list)
                data = [data[0][0], data[0][1]]
                self._coordinate_writer.write(data)
            if not self.data_collection_active:
                break

        self._coordinate_writer.close_file()


if __name__ == "__main__":
    server = BackendServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Keyboard interrupt received")
    finally:
        server.cleanup()
