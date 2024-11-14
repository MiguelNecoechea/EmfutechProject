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

from IO.SignalProcessing.AuraTools import rename_aura_channels, is_stream_ready
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
        self._aura_training_thread = None
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.PAIR)
        self._socket.bind(f"tcp://*:{port}")

        # Training points coordinates for calibration
        self._current_x_coordinate = 0
        self._current_y_coordinate = 0

        # Flags for the server status.
        self._running = False

        # Flags for the data collection sources.
        self._fitting_eye_gaze = False
        self._eye_gaze_running = False
        self._pointer_tracking_active = False

        # Objects that are the data source.
        self._emotion_handler = None
        self._eye_gaze = None
        self._stream = None
        self._regressor = None
        self._pointer_tracker = None

        # Boolean flags for deciding the experiments to run (Still building this out)
        self._run_aura = False
        self._run_emotion = False
        self._run_gaze = False
        self._run_pointer = False
        self._run_screen = False

        # Threads for the data collection
        self._aura_thread = None
        self._emotion_thread = None
        self._regressor_thread = None
        self._start_time = None
        self._screen_recording_thread = None

        # Path and file names for the data
        # TODO: Make this dynamic so add the frontend code to set the path and filename
        self._path = 'testing'
        self._training_path = 'training'
        self._filename = 'testing'

        # Aura stream id
        # TODO: Make this dynamic
        self._aura_stream_id = 'filtered'

        # Data writers
        self._aura_writer = None
        self._emotion_writer = None
        self._gaze_writer = None
        self._pointer_writer = None

        # Status for the data collection loops
        self._data_collection_active = False
        self._training_data_collection_active = False
        self._threads = []

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def start(self):
        """Start the backend server and begin processing messages."""
        self._running = True
        print("Backend server started...")
        while self._running:
            try:
                message = self._socket.recv_json(flags=zmq.NOBLOCK)
                response = self.handle_message(message)
                if response:
                    self._socket.send_json(response)
            except zmq.error.Again:
                # No message available, sleep briefly
                time.sleep(0.001)
            except Exception as e:
                print(f"Error handling message: {e}")
                try:
                    self._socket.send_json({"error": str(e)})
                except:
                    pass

    def cleanup(self):
        """Clean up resources before shutting down the server."""
        print("Cleaning up resources...")
        self._running = False
        self._data_collection_active = False
        self._training_data_collection_active = False

        # Stop all data collection first
        if self._pointer_tracker:
            self._pointer_tracker.stop_tracking()
            self._pointer_tracker.is_tracking = False

        # Close all file writers
        writers = [
            self._aura_writer,
            self._emotion_writer,
            self._gaze_writer,
            self._pointer_writer
        ]
        for writer in writers:
            if writer:
                try:
                    if writer:
                        writer.close_file()
                except Exception as e:
                    print(f"Error closing writer: {e}")

        # Wait for all threads to complete
        for thread in self._threads:
            if thread and thread.is_alive():
                thread.join(timeout=1.0)

        # Clean up ZMQ resources
        if hasattr(self, '_socket') and self._socket:
            self._socket.close()
        if hasattr(self, '_context') and self._context:
            self._context.term()

        print("Cleanup completed")

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
        self._threads.append(thread)
        try:
            yield thread
        finally:
            if thread in self._threads:
                self._threads.remove(thread)

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
            'update_signal_status': self.handle_update_signal_status,
            'start_eye_gaze': self.start_eye_gaze,
            'start': self.start_testing,
            'stop': self.handle_stop_testing,
            'start_recording_training_data': self.handle_training_data,
            'stop_recording_training_data': self.stop_recording_training_data,
            'set_coordinates': self.handle_coordinates
        }
        handler = handlers.get(command)
        if handler:
            return handler(**params)
        else:
            return {"error": f"Unknown command: {command}"}

    def start_eye_gaze(self):
        """Initialize and start eye gaze tracking."""
        def eye_gaze_task():
            self._eye_gaze = create_new_eye_gaze()
            print("Eye gaze tracking started")
            self._eye_gaze_running = True
            self._fitting_eye_gaze = False
            self._socket.send_json({"status": "success", "message": "start-calibration"})

        if not self._fitting_eye_gaze and self._run_gaze:
            self._fitting_eye_gaze = True
            local_thread = threading.Thread(target=eye_gaze_task)
            local_thread.start()
            return {"status": "success", "message": "Eye gaze tracking started"}
        else:
            return {"status": "error", "message": "Eye gaze is already started or cannot be started"}

    def start_testing(self):
        """Start all active data collection threads."""
        try:
            if not self._data_collection_active:
                self._start_time = time.time()
                self._data_collection_active = True

                # AURA
                if self._run_aura:
                    self.start_aura()
                    try:
                        channels_names = ['timestamp'] + list(self._stream.info['ch_names'])
                        self._aura_writer = AuraDataWriter(self._path, f'{self._filename}_aura.csv', channels_names)
                        self._aura_writer.create_new_file()
                        
                        if self._aura_thread is None or not self._aura_thread.is_alive():
                            self._aura_thread = threading.Thread(
                                target=self._aura_data_collection_loop,
                                args=('testing',),
                                daemon=True
                            )
                        self._aura_thread.start()
                        self._threads.append(self._aura_thread)

                    except Exception as e:
                        print(f"Error starting Aura thread: {str(e)}")
                        raise
                
                # Emotion
                if self._run_emotion:
                    self.start_emotion_detection()
                    self._emotion_writer = EmotionPredictedWriter(self._path, f'{self._filename}_emotions.csv')
                    self._emotion_writer.create_new_file()
                    
                    if self._emotion_thread is None or not self._emotion_thread.is_alive():
                        self._emotion_thread = threading.Thread(
                            target=self._emotion_collection_loop,
                            daemon=True
                        )
                    self._emotion_thread.start()
                    self._threads.append(self._emotion_thread)                    
                
                # Coordinate/Gaze
                if self._run_gaze:
                    self._gaze_writer = CoordinateWriter(self._path, f'{self._filename}_gaze.csv')
                    self._gaze_writer.create_new_file()
                    
                    if self._regressor_thread is None or not self._regressor_thread.is_alive():
                        self._regressor_thread = threading.Thread(
                            target=self._coordinate_regressor_loop,
                            daemon=True
                        )
                    self._regressor_thread.start()
                    self._threads.append(self._regressor_thread)
                
                # Pointer
                if self._run_pointer:
                    self._pointer_writer = PointerWriter(self._path, f'{self._filename}_pointer_data.csv')
                    self._pointer_writer.create_new_file()
                    self.start_pointer_tracking()
                    self._pointer_tracker.start_time = self._start_time
                    self._pointer_tracker.is_tracking = True

                return {"status": "success", "message": "Testing started successfully"}
            else:
                return {"status": "error", "message": "Testing already started"}
            
        except Exception as e:
            self._data_collection_active = False
            print(f"Error in start_testing: {str(e)}")
            return {"status": "error", "message": f"Error starting testing: {str(e)}"}

    def handle_stop(self):
        """Stop the server and clean up resources."""
        print("Stopping server...")
        self.cleanup()
        return {"status": "success", "message": "Server stopped"}

    # End of main start/stop functions

    def handle_training_data(self):
        """Start collecting training data for eye gaze tracking."""
        # Create local writer for gaze data
        gaze_writer = GazeWriter(self._training_path, 'training_gaze.csv')
        gaze_writer.create_new_file()
        aura_training_thread = None
        if self._run_aura:
            self.start_aura()
            aura_training_thread = threading.Thread(
                target=self._aura_data_collection_loop,
                args=('training',)
            )
        
        def training_data_task():
            while True:
                # Make prediction and write to file
                gaze_vector = self._eye_gaze.get_gaze_vector()
                if self._current_y_coordinate != 0 and self._current_x_coordinate != 0:
                    data = []
                    if gaze_vector[0] is not None and gaze_vector[1] is not None:
                        for i in gaze_vector[0]:
                            data.append(i)
                        for i in gaze_vector[1]:
                            data.append(i)
                        data.append(self._current_x_coordinate)
                        data.append(self._current_y_coordinate)
                        gaze_writer.write(data)
                if not self._training_data_collection_active:
                    gaze_writer.close_file()
                    break

        if self._eye_gaze_running:
            self._training_data_collection_active = True
            local_thread = threading.Thread(target=training_data_task)
            local_thread.start()
            if aura_training_thread:
                aura_training_thread.start()

            return {"status": "success", "message": "Training data recording started"}
        else:
            print("Eye gaze tracking not started")
            return {"status": "error", "message": "Eye gaze tracking not started"}

    def handle_stop_recording(self):
        """Stop all data recording."""
        self._data_collection_active = False
        return {"status": "success", "message": "Recording stopped"}

    def handle_stop_testing(self):
        """Stop all testing and data collection."""
        self._data_collection_active = False
        # self._start_time = None
        if self._pointer_tracker is not None:
            self._pointer_tracker.stop_tracking()
            self._pointer_tracker.is_tracking = False
            self._pointer_tracker.clear_coordinates()
            if self._pointer_writer:
                self._pointer_writer.close_file()
            self._pointer_writer = None  # Clear reference
        
        # Join and clear all threads
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        # Clear the threads list
        self._threads = []
        
        # Reset thread references
        self._aura_thread = None
        self._emotion_thread = None
        self._regressor_thread = None
        self._screen_recording_thread = None
        # Add other threads if necessary

        return {"status": "success", "message": "Testing stopped"}

    def stop_recording_training_data(self):
        """Stop recording training data."""
        try:
            self._training_data_collection_active = False
            
            # Clean up training-specific resources
            if hasattr(self, '_aura_training_thread') and self._aura_training_thread:
                self._aura_training_thread.join(timeout=1.0)
                self._aura_training_thread = None
            
            self.start_regressor()
            return {"status": "success", "message": "Training data recording stopped"}
        except Exception as e:
            print(f"Error stopping training data recording: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_update_signal_status(self, signal_type, status):
        """Update the status of a signal."""
        bool_status = True if status == 'true' else False
        if signal_type == 'aura':
            self._run_aura = bool_status
        elif signal_type == 'gaze':
            self._run_gaze = bool_status
        elif signal_type == 'emotion':
            self._run_emotion = bool_status
        elif signal_type == 'pointer':
            self._run_pointer = bool_status
        elif signal_type == 'screen':
            self._run_screen = bool_status
        
        return {"status": "success", "message": f"Signal {signal_type} updated to {status}"}

    # End of Message Handling Functions

    # Signal initialization functions

    def start_pointer_tracking(self):
        """Initialize and start pointer tracking."""
        if not self._pointer_tracking_active:
            self._pointer_tracker = CursorTracker(writer=self._pointer_writer)
            return {"status": "success", "message": "Pointer tracking started"}
        else:
            return {"status": "error", "message": "Pointer tracking already active"}
        

    def start_regressor(self):
        """Initialize and start the position regressor."""
        path = os.path.join(self._training_path, 'training_gaze.csv')
        self._regressor = PositionRegressor(path)
        self._regressor.train_create_model()

        self._regressor_thread = threading.Thread(
            target=self._coordinate_regressor_loop
        )

        return {"status": "success", "message": "Regressor started"}

    def start_aura(self, buffer_size_multiplier=1):
        try:
            self._stream = Stream(bufsize=buffer_size_multiplier, source_id=self._aura_stream_id)
            self._stream.connect(processing_flags='all')
            rename_aura_channels(self._stream)

            # Create thread without starting it
            self._aura_thread = threading.Thread(
                target=self._aura_data_collection_loop,
                args=('testing',)
            )

            # Add to thread tracking
            self._threads.append(self._aura_thread)

            return {"status": "success", "message": "Aura signal handling initialized"}
        except Exception as e:
            print(f"Error in handle_aura_signal: {str(e)}")
            return {"status": "error", "message": str(e)}

    def start_emotion_detection(self):
        """
        Initialize and start emotion recognition.
        """
        try:
            self._emotion_handler = EmotionRecognizer('opencv')
            self._emotion_thread = threading.Thread(target=self._emotion_collection_loop)

            return {"status": "success", "message": "Emotion recognition started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # Signal collection functions end.

    # Training data collection functions
    def handle_coordinates(self, x, y):
        """
        Update current coordinates.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        self._current_x_coordinate = x
        self._current_y_coordinate = y
        return {"status": "success", "coordinates": [x, y]}
    
    # Signal collection loops
    def _aura_data_collection_loop(self, collection_type):
        """
        Collect Aura data and write to file.
        The mode of operation is determined by the type argument. Is important to handle
        this internally to avoid user error.
        Args:
            collection_type (str): 'training' or 'testing'
        """
        try:
            aura_writer_training = None
            if collection_type == 'training':
                channels_names = ['timestamp'] + self._stream.info['ch_names']
                aura_writer_training = AuraDataWriter(self._training_path, 'training_aura.csv', channels_names)
                aura_writer_training.create_new_file()
            
            while True:
                if is_stream_ready(self._stream):
                    data, ts = self._stream.get_data()
                    if collection_type == 'training':
                        if aura_writer_training:
                            aura_writer_training.write_data(ts, data)
                    else:
                        processed_ts = [round(t - self._start_time, 3) for t in ts]
                        self._aura_writer.write_data(processed_ts, data)

                time.sleep(0.001)

                if collection_type == 'training' and not self._training_data_collection_active:
                    aura_writer_training.close_file()
                    break
                elif collection_type == 'testing' and not self._data_collection_active:
                    if self._aura_writer:
                        self._aura_writer.close_file()
                    break
                    
        except Exception as e:
            print(f"Error in aura collection loop: {str(e)}")
            raise

    def _emotion_collection_loop(self):
        """
        Continuously collect and write emotion data in a loop.
        
        Uses the emotion_handler to recognize emotions and writes the dominant emotion
        along with a timestamp to the emotion_writer. Runs until data_collection_active
        is set to False.
        """
        while True:
            if self._emotion_handler:
                emotion = self._emotion_handler.recognize_emotion()
                if emotion is not None:
                    emotion = emotion[0]['dominant_emotion']
                    timestamp = round(time.time() - self._start_time, 3)
                    self._emotion_writer.write_data(timestamp, emotion)
            time.sleep(0.001)  # Small sleep to prevent CPU overuse
            if not self._data_collection_active:
                break
        self._emotion_writer.close_file()

    def _coordinate_regressor_loop(self):
        """
        Continuously collect eye gaze data and predict screen coordinates in a loop.
        
        Gets gaze vectors for both eyes from the eye tracker, uses the regressor to
        predict x,y screen coordinates, and writes the predictions with timestamps
        to the coordinate writer. Runs until data_collection_active is set to False.
        
        The gaze input consists of x,y,z coordinates for both left and right eyes.
        Predictions are rounded to integer screen coordinates before writing.
        """
        while True:
            gaze_vector = self._eye_gaze.get_gaze_vector()
            left_eye = gaze_vector[0]
            right_eye = gaze_vector[1]
            if left_eye is not None and right_eye is not None:
                gaze_input = [[
                    *left_eye,   # x, y, z coordinates for left eye
                    *right_eye   # x, y, z coordinates for right eye
                ]]

                predicted_coords = self._regressor.make_prediction(gaze_input)
                x, y = predicted_coords[0]  # Extract x,y from nested array
                x = int(x)
                y = int(y)
                print(f"Predicted coordinates: {x}, {y}")
                timestamp = round(time.time() - self._start_time, 3)
                self._gaze_writer.write(timestamp, [x, y])

            if not self._data_collection_active:
                break
