import zmq
import time
import threading
import signal
import sys
import os
from contextlib import contextmanager


from mne_lsl.stream import StreamLSL as Stream

from IO.FileWriting.CoordinateWriter import CoordinateWriter
from IO.FileWriting.AuraDataWriter import AuraDataWriter
from IO.FileWriting.EmotionWriter import EmotionPredictedWriter
from IO.FileWriting.GazeWriter import GazeWriter

from Backend.EyeGaze import create_new_eye_gaze
from Backend.EyeCoordinateRegressor import PositionRegressor

from IO.SignalProcessing.AuraTools import rename_aura_channels, is_stream_ready, rename_40_channels
from IO.VideoProcessing.EmotionRecognizer import EmotionRecognizer
from IO.PointerTracking.PointerTracker import CursorTracker
from IO.FileWriting.PointerWriter import PointerWriter

class BackendServer:
    """
    Backend server that handles all data collection and processing for eye tracking, emotions, 
    EEG signals and pointer tracking.

    The server uses ZMQ for communication with the frontend and manages multiple threads for
    different data collection tasks.
    """

    def __init__(self, port="5556"):
        """
        Initialize the backend server with all necessary components.

        Args:
            port (str): Port number for ZMQ communication. Defaults to "5556".
        """
        # Server setup
        self.aura_training_thread = None
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind(f"tcp://*:{port}")

        # Training points coordinates for calibration
        self.current_x_coordinate = 0
        self.current_y_coordinate = 0

        # Flags for the server status.
        self.running = False

        # Flags for the data collection soruces.
        self.fitting_eye_gaze = False
        self.eye_gaze_running = False
        self.pointer_tracking_active = False

        # Objects that are the data source.
        self.emotion_handler = None
        self.eye_gaze = None
        self.stream = None
        self.regressor = None
        self.pointer_tracker = None

        # Boolean flags for deciding the experiments to run (Still building this out)
        self.run_aura = False
        self.run_emotion = False
        self.run_gaze = False
        self.run_pointer = False
        self.run_screen_recording = False

        # Threads for the data collection
        self.aura_thread = None
        self.emotion_thread = None
        self.regressor_thread = None
        self.start_time = None
        self.screen_recording_thread = None

        # Path and file names for the data
        # TODO: Make this dynamic so add the frontend code to set the path and filename
        self.path = 'testing'
        self.filename = 'testing'

        # Aura stream id
        # TODO: Make this dynamic
        self.aura_stream_id = 'filtered'

        # Data writers
        self.aura_writer = None
        self.emotion_writer = None
        self.gaze_writer = None
        self.pointer_writer = None

        # Status for the data collection loops
        self.data_collection_active = False
        self.training_data_collection_active = False
        self.threads = []

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def start(self):
        """Start the backend server and begin processing messages."""
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
        """Clean up resources before shutting down the server."""
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
        """Handle system signals for graceful shutdown."""
        print("Signal received, cleaning up...")
        self.cleanup()
        sys.exit(0)

    @contextmanager
    def thread_tracking(self, thread):
        """
        Context manager to track active threads.
        
        Args:
            thread: Thread object to track
        """
        self.threads.append(thread)
        try:
            yield thread
        finally:
            if thread in self.threads:
                self.threads.remove(thread)

    def handle_message(self, message):
        """
        Process incoming messages and route them to appropriate handlers.
        
        Args:
            message (dict): Message containing command and parameters
            
        Returns:
            dict: Response from the handler
        """
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
            "start_pointer_tracking": self.handle_pointer_tracking,
            "stop": self.handle_stop
        }
        print(message)
        handler = handlers.get(command)
        if handler:
            return handler(**params)
        else:
            return {"error": f"Unknown command: {command}"}

    def handle_eye_gaze(self):
        """Initialize and start eye gaze tracking."""
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
        """Start eye tracking calibration process."""
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
        """Start all active data collection threads."""
        try:
            if not self.data_collection_active:
                self.start_time = time.time()
                self.data_collection_active = True
                
                # AURA
                if self.stream is not None:
                    try:
                        channels_names = ['timestamp'] + list(self.stream.info['ch_names'])
                        self.aura_writer = AuraDataWriter(self.path, f'{self.filename}_aura.csv', channels_names)
                        self.aura_writer.create_new_file()
                        
                        if self.aura_thread is None or not self.aura_thread.is_alive():
                            self.aura_thread = threading.Thread(
                                target=self._aura_data_collection_loop,
                                args=('testing',),
                                daemon=True
                            )
                            self.aura_thread.start()
                            self.threads.append(self.aura_thread)
                    except Exception as e:
                        print(f"Error starting Aura thread: {str(e)}")
                        raise
                
                # Emotion
                if self.emotion_handler is not None:
                    self.emotion_writer = EmotionPredictedWriter(self.path, f'{self.filename}_emotions.csv')
                    self.emotion_writer.create_new_file()
                    
                    if self.emotion_thread is None or not self.emotion_thread.is_alive():
                        self.emotion_thread = threading.Thread(
                            target=self._emotion_collection_loop,
                            daemon=True
                        )
                        self.emotion_thread.start()
                        self.threads.append(self.emotion_thread)
                
                # Coordinate/Gaze
                if self.regressor is not None:
                    self._coordinate_writer = CoordinateWriter(self.path, f'{self.filename}_gaze.csv')
                    self._coordinate_writer.create_new_file()
                    
                    if self.regressor_thread is None or not self.regressor_thread.is_alive():
                        self.regressor_thread = threading.Thread(
                            target=self._coordinate_regressor_loop,
                            daemon=True
                        )
                        self.regressor_thread.start()
                        self.threads.append(self.regressor_thread)
                
                # Pointer
                if self.pointer_tracker is not None:
                    self.pointer_writer = PointerWriter(self.path, f'{self.filename}_pointer_data.csv')
                    self.pointer_writer.create_new_file()
                    self.pointer_tracker.is_tracking = True

                return {"status": "success", "message": "Testing started successfully"}
            else:
                return {"status": "error", "message": "Testing already started"}
            
        except Exception as e:
            self.data_collection_active = False
            print(f"Error in start_testing: {str(e)}")
            return {"status": "error", "message": f"Error starting testing: {str(e)}"}

    def handle_stop(self):
        """Stop the server and clean up resources."""
        print("Stopping server...")
        self.cleanup()
        return {"status": "success", "message": "Server stopped"}

    def handle_training_data(self):
        """Start collecting training data for eye gaze tracking."""
        # Create local writer for gaze data
        gaze_writer = GazeWriter('training', 'training_gaze.csv')
        gaze_writer.create_new_file()
        
        def training_data_task():
            training_active = True
            while training_active:
                # Make prediction and write to file
                gaze_vector = self.eye_gaze.get_gaze_vector()
                if self.current_y_coordinate != 0 and self.current_x_coordinate != 0:
                    data = []
                    if gaze_vector[0] is not None and gaze_vector[1] is not None:
                        for i in gaze_vector[0]:
                            data.append(i)
                        for i in gaze_vector[1]:
                            data.append(i)
                        data.append(self.current_x_coordinate)
                        data.append(self.current_y_coordinate)
                        gaze_writer.write(data)
                if not self.training_data_collection_active:
                    gaze_writer.close_file()
                    training_active = False
                    break

        if self.eye_gaze_running:
            self.training_data_collection_active = True
            local_thread = threading.Thread(target=training_data_task)
            local_thread.start()
            return {"status": "success", "message": "Training data recording started"}
        else:
            print("Eye gaze tracking not started")
            return {"status": "error", "message": "Eye gaze tracking not started"}

    def handle_stop_recording(self):
        """Stop all data recording."""
        self.data_collection_active = False
        return {"status": "success", "message": "Recording stopped"}

    def handle_coordinates(self, x, y):
        """
        Update current coordinates.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        print(f"Coordinates updated: {x}, {y}")
        self.current_x_coordinate = x
        self.current_y_coordinate = y
        return {"status": "success", "coordinates": [x, y]}

    def handle_regressor(self):
        """Initialize and start the position regressor."""
        self.regressor = PositionRegressor('training/training_gaze.csv')
        self.regressor.train_create_model()

        def _coordinate_regressor_loop():
            while True:
                gaze_vector = self.eye_gaze.get_gaze_vector()
                left_eye = gaze_vector[0]
                right_eye = gaze_vector[1]
                if left_eye is not None and right_eye is not None:
                    gaze_input = [[
                        *left_eye,   # x, y, z coordinates for left eye
                        *right_eye   # x, y, z coordinates for right eye
                    ]]

                    predicted_coords = self.regressor.make_prediction(gaze_input)
                    x, y = predicted_coords[0]  # Extract x,y from nested array
                    x = int(x)
                    y = int(y)
                    print(f"Predicted coordinates: {x}, {y}")
                    timestamp = round(time.time() - self.start_time, 3)
                    self._coordinate_writer.write(timestamp, [x, y])

                if not self.data_collection_active:
                    break

        self._coordinate_writer.close_file()    
        self.regressor_thread = threading.Thread(
            target=_coordinate_regressor_loop
        )

        return {"status": "success", "message": "Regressor started"}

    def handle_aura_signal(self, buffer_size_multiplier=1):
        try:
            self.stream = Stream(bufsize=buffer_size_multiplier, source_id=self.aura_stream_id)
            self.stream.connect(processing_flags='all')
            rename_aura_channels(self.stream)

            # Create thread without starting it
            self.aura_thread = threading.Thread(
                target=self._aura_data_collection_loop,
                args=('testing',)
            )

            # Add to thread tracking
            self.threads.append(self.aura_thread)

            return {"status": "success", "message": "Aura signal handling initialized"}
        except Exception as e:
            print(f"Error in handle_aura_signal: {str(e)}")
            return {"status": "error", "message": str(e)}

    def handle_emotion(self, output_path='.', file_name='emotions.csv'):
        """
        Initialize and start emotion recognition.
        
        Args:
            output_path (str): Path for output files
            file_name (str): Name of the emotion data file
        """
        try:
            self.emotion_handler = EmotionRecognizer('opencv')

            def _emotion_collection_loop():
                while True:
                    if self.emotion_handler:
                        emotion = self.emotion_handler.recognize_emotion()
                        emotion = emotion[0]['dominant_emotion']
                        timestamp = round(time.time() - self.start_time, 3)
                        self.emotion_writer.write_data(timestamp, emotion)
                    time.sleep(0.001)  # Small sleep to prevent CPU overuse
                    if not self.data_collection_active:
                        break
                self.emotion_writer.close_file()
            
            self.emotion_thread = threading.Thread(target=_emotion_collection_loop)

            return {"status": "success", "message": "Emotion recognition started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def handle_stop_testing(self):
        """Stop all testing and data collection."""
        self.data_collection_active = False
        # self.start_time = None
        if self.pointer_tracker is not None:
            self.pointer_tracker.stop_tracking()
            self.pointer_tracker.is_tracking = False
            self.pointer_tracker.clear_coordinates()
            if self.pointer_writer:
                self.pointer_writer.close_file()
            self.pointer_writer = None  # Clear reference
        
        # Join and clear all threads
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        # Clear the threads list
        self.threads = []
        
        # Reset thread references
        self.aura_thread = None
        self.emotion_thread = None
        self.regressor_thread = None
        self.screen_recording_thread = None
        # Add other threads if necessary

        return {"status": "success", "message": "Testing stopped"}

    def handle_stop_recording_traing_data(self):
        """Stop recording training data."""
        self.training_data_collection_active = False
        return {"status": "success", "message": "Training data recording stopped"}

    def handle_pointer_tracking(self):
        """Initialize and start pointer tracking."""
        if not self.pointer_tracking_active:
            # Initialize tracker with the writer
            self.pointer_tracker = CursorTracker(writer=self.pointer_writer)

            return {"status": "success", "message": "Pointer tracking started"}
        else:
            return {"status": "error", "message": "Pointer tracking already active"}

    # End of Message Handling Functions


    def _aura_data_collection_loop(self, type):
        """
        Collect Aura data and write to file.
        The mode of operation is determined by the type argument. Is importat to handle
        this internally to avoid user error.
        Args:
            type (str): 'training' or 'testing'
        """
        try:
            if type == 'training':
                channels_names = ['timestamp'] + self.stream.info['ch_names']
                aura_writer_training = AuraDataWriter('training', 'training_aura.csv', channels_names)
                aura_writer_training.create_new_file()
            
            while True:
                if is_stream_ready(self.stream):
                    data, ts = self.stream.get_data()
                    if type == 'training':
                        aura_writer_training.write_data(ts, data)
                    else:
                        processed_ts = [round(t - self.start_time, 3) for t in ts]
                        self.aura_writer.write_data(processed_ts, data)

                time.sleep(0.001)

                if type == 'training' and not self.training_data_collection_active:
                    aura_writer_training.close_file()
                    break
                elif type == 'testing' and not self.data_collection_active:
                    if self.aura_writer:
                        self.aura_writer.close_file()
                    break
                    
        except Exception as e:
            print(f"Error in aura collection loop: {str(e)}")
            raise