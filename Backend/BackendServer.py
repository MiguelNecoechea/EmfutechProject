"""
BackendServer.py

This module implements a ZMQ-based backend server that handles eye tracking, emotion recognition,
pointer tracking, and data collection functionality. It manages multiple concurrent data streams
and provides an interface for controlling various tracking and recording features.

The server uses a thread manager to handle multiple concurrent operations and provides clean
shutdown handling through signal handlers.

Classes:
    BackendServer: Main server class that handles all backend functionality

Dependencies:
    - zmq: For network communication
    - threading: For concurrent operations
    - signal: For graceful shutdown handling
    - mne_lsl: For LSL stream handling
    - Various custom IO and processing modules
"""

import zmq
import time
import threading
import signal
import sys
import os
from contextlib import contextmanager


# Add the parent directory to the Python path

from mne_lsl.stream import StreamLSL as Stream
from IO.FileWriting.CoordinateWriter import CoordinateWriter

from Backend.EyeGaze import create_new_eye_gaze
from Backend.EyeCoordinateRegressor import PositionRegressor
from Backend.ThreadManager import ThreadManager

from IO.FileWriting.AuraDataWriter import AuraDataWriter
from IO.FileWriting.EmotionWriter import EmotionPredictedWriter
from IO.FileWriting.GazeWriter import GazeWriter
from IO.FileWriting.PointerWriter import PointerWriter

from IO.SignalProcessing.AuraTools import rename_aura_channels, is_stream_ready, rename_40_channels
from IO.VideoProcessing.EmotionRecognizer import EmotionRecognizer
from IO.PointerTracking.PointerTracker import CursorTracker

class BackendServer:
    """
    A ZMQ-based backend server that manages eye tracking, emotion recognition, and data collection.
    
    This class provides functionality to:
    - Track eye gaze and calibrate eye tracking
    - Record and process emotion data
    - Track pointer/cursor movements
    - Collect and save various data streams (Aura, gaze, emotions, pointer)
    - Manage concurrent operations through threading
    
    Attributes:
        port (str): The port number for the ZMQ server
        running (bool): Flag indicating if the server is running
        fitting_eye_gaze (bool): Flag for eye gaze calibration status
        eye_gaze_running (bool): Flag indicating if eye tracking is active
        pointer_tracking_active (bool): Flag for pointer tracking status
        data_collection_active (bool): Flag for data collection status
        training_data_collection_active (bool): Flag for training data collection
    """

    def __init__(self, port="5556"):
        """
        Initialize the backend server with all necessary components.
        
        Args:
            port (str): Port number for the ZMQ server (default: "5556")
        """
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
        self.pointer_tracking_active = False

        self.emotion_handler = None
        self.eye_gaze = None
        self.stream = None
        self.regressor = None
        self.pointer_tracker = None

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

        # Pointer 
        self.pointer_writer = PointerWriter('testing', 'testing_pointer.csv')
        self.pointer_writer.create_new_file()


        # Status for the data collection loops
        self.data_collection_active = False
        self.training_data_collection_active = False
        self.threads = []

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

        self.thread_manager = ThreadManager()

    # Server Handling Functions
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
        
        # Stop all threads
        self.thread_manager.stop_all_threads()

        # Clean up ZMQ resources
        if hasattr(self, 'socket') and self.socket:
            self.socket.close()
        if hasattr(self, 'context') and self.context:
            self.context.term()

        # Close all writers
        if hasattr(self, 'gaze_writer_training'):
            self.gaze_writer_training.close_file()
        # ... close other writers ...

    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        print("Signal received, cleaning up...")
        self.cleanup()
        sys.exit(0)

    # Server Handling Functions End

    # Thread Management Functions
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

    # Thread Management Functions End

    def handle_message(self, message):
        """
        Process incoming messages and route to appropriate handlers.
        
        Args:
            message (dict): Message containing command and parameters
            
        Returns:
            dict: Response message with status and any relevant data
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

    # Message Handling Functions

    def handle_eye_gaze(self):
        """Start eye gaze tracking in a separate thread."""
        def eye_gaze_task(stop_event):
            self.eye_gaze = create_new_eye_gaze()
            self.eye_gaze_running = True
            while not stop_event.is_set():
                # Your eye gaze processing code
                time.sleep(0.001)

        if not self.fitting_eye_gaze:
            self.fitting_eye_gaze = True
            self.thread_manager.add_thread("eye_gaze", eye_gaze_task)
            self.thread_manager.start_thread("eye_gaze")
            return {"status": "success", "message": "Eye gaze tracking started"}
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
        if not self.data_collection_active:
            self.data_collection_active = True

            if self.aura_thread is not None:
                self.aura_thread.start()
            if self.emotion_thread is not None:
                self.emotion_thread.start()
            if self.regressor_thread is not None:
                self.regressor_thread.start()
            if self.pointer_tracker is not None:
                self.pointer_tracker.is_tracking = True

            return {"status": "success", "message": "Eye gaze tracking started"}
        else:
            return {"status": "error", "message": "Testing already started"}

    def handle_stop(self):
        """Stop the server and clean up resources."""
        print("Stopping server...")
        self.cleanup()
        return {"status": "success", "message": "Server stopped"}

    def handle_training_data(self):
        """Start collecting training data for eye tracking calibration."""
        def training_data_task(stop_event):
            while not stop_event.is_set():
                gaze_vector = self.eye_gaze.get_gaze_vector()
                if self.current_y_coordinate != 0 and self.current_x_coordinate != 0:
                    data = []
                    for i in gaze_vector[0]:
                        data.append(i)
                    for i in gaze_vector[1]:
                        data.append(i)
                    data.append(self.current_x_coordinate)
                    data.append(self.current_y_coordinate)
                    self.gaze_writer_training.write(data)
                time.sleep(0.001)
            self.gaze_writer_training.close_file()

        if self.eye_gaze_running:
            self.thread_manager.add_thread("training_data", training_data_task)
            self.thread_manager.start_thread("training_data")
            return {"status": "success", "message": "Training data recording started"}
        return {"status": "error", "message": "Eye gaze tracking not started"}

    def handle_stop_recording(self):
        """Stop all data collection."""
        self.data_collection_active = False
        return {"status": "success", "message": "Recording stopped"}

    def handle_coordinates(self, x, y):
        """
        Update current coordinates for training.
        
        Args:
            x (float): X coordinate
            y (float): Y coordinate
        """
        print(f"Coordinates updated: {x}, {y}")
        self.current_x_coordinate = x
        self.current_y_coordinate = y
        return {"status": "success", "coordinates": [x, y]}

    def handle_regressor(self):
        """Initialize and start the coordinate regressor."""
        self.regressor = PositionRegressor('training/training_gaze.csv')
        self.regressor.train_create_model()

        def _coordinate_regressor_loop():
            while True:
                gaze_vector = self.eye_gaze.get_gaze_vector()
                left_eye, right_eye = gaze_vector
                if left_eye is not None and right_eye is not None:
                    gaze_input = [[
                        *left_eye,   # x, y, z coordinates for left eye
                        *right_eye   # x, y, z coordinates for right eye
                    ]]

                    predicted_coords = self.regressor.make_prediction(gaze_input)
                    x, y = predicted_coords[0]  # Extract x,y from nested array
                    
                    self._coordinate_writer.write([x, y])

                if not self.data_collection_active:
                    break

        self._coordinate_writer.close_file()    
        self.regressor_thread = threading.Thread(
            target=_coordinate_regressor_loop
        )

        return {"status": "success", "message": "Regressor started"}

    def handle_aura_signal(self, stream_id='AURA_Power', buffer_size_multiplier=1):
        """
        Initialize and start Aura signal processing.
        
        Args:
            stream_id (str): ID of the LSL stream to connect to
            buffer_size_multiplier (int): Multiplier for the buffer size
        """
        try:
            self.stream = Stream(bufsize=buffer_size_multiplier, source_id=stream_id)
            self.stream.connect(processing_flags='all')
            rename_aura_channels(self.stream)

            def _aura_data_collection_loop(type):
                while True:
                    if is_stream_ready(self.stream):
                        data, ts = self.stream.get_data()
                        if type == 'training':
                            self.aura_writer_training.write_data(ts, data)
                        else:
                            self.aura_writer.write_data(ts, data)

                        time.sleep(0.001)

                        if type == 'training' and self.training_data_collection_active is False:
                            self.aura_writer_training.close_file()
                            break
                        elif type == 'testing' and self.data_collection_active is False:
                            self.aura_writer.close_file()
                            break

            self.aura_thread = threading.Thread(
                target=_aura_data_collection_loop,
                args=('testing',)
            )
            
            self.aura_training_thread = threading.Thread(
                target=_aura_data_collection_loop,
                args=('training',)
            )

            return {"status": "success", "message": "Aura signal handling started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def handle_emotion(self, output_path='.', file_name='emotions.csv'):
        """
        Initialize and start emotion recognition.
        
        Args:
            output_path (str): Path to save emotion data
            file_name (str): Name of the emotion data file
        """
        try:
            self.emotion_handler = EmotionRecognizer('opencv')

            def _emotion_collection_loop():
                while True:
                    if self.emotion_handler:
                        emotion = self.emotion_handler.get_emotion()
                        self.emotion_writer.write_data(emotion)
                    time.sleep(0.001)
                    if not self.data_collection_active:
                        break
                self.emotion_writer.close_file()

            self.emotion_thread = threading.Thread(target=_emotion_collection_loop)

            return {"status": "success", "message": "Emotion recognition started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def handle_stop_testing(self):
        """Stop all testing and data collection processes."""
        self.data_collection_active = False

        if self.pointer_tracker is not None:
            self.pointer_tracker.stop_tracking()
            self.pointer_tracker.is_tracking = False
            self.pointer_tracker.clear_coordinates()
            self.pointer_writer.close_file()
        return {"status": "success", "message": "Testing stopped"}

    def handle_stop_recording_traing_data(self):
        """Stop recording training data."""
        self.training_data_collection_active = False
        return {"status": "success", "message": "Training data recording stopped"}

    def handle_pointer_tracking(self):
        """Initialize and start pointer tracking."""
        if not self.pointer_tracking_active:
            self.pointer_tracker = CursorTracker(writer=self.pointer_writer)
            return {"status": "success", "message": "Pointer tracking started"}
        else:
            return {"status": "error", "message": "Pointer tracking already active"}

