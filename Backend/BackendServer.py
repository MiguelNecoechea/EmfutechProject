import zmq
import time
import threading
import signal
import sys
import cv2
import os
import queue
from contextlib import contextmanager
from cryptography.fernet import Fernet
import base64

from mne_lsl.stream import StreamLSL as Stream
from DataProcessing.LLMProcessor import DataAnalyzer


from IO.FileWriting.CoordinateWriter import CoordinateWriter
from IO.FileWriting.AuraDataWriter import AuraDataWriter
from IO.FileWriting.EmotionWriter import EmotionPredictedWriter
from IO.FileWriting.GazeWriter import GazeWriter

from Backend.EyeCoordinateRegressor import PositionRegressor

from IO.EyeTracking.LaserGaze.GazeProcessor import GazeProcessor
from IO.SignalProcessing.AuraTools import resolve_aura
from IO.SignalProcessing.AuraTools import rename_aura_channels, is_stream_ready
from IO.VideoProcessing.EmotionRecognizer import EmotionRecognizer
from IO.PointerTracking.PointerTracker import CursorTracker
from IO.FileWriting.PointerWriter import PointerWriter

# Constants
DEFAULT_PORT = "5556"
DEFAULT_AURA_STREAM_ID = 'filtered'
DEFAULT_PARTICIPANT = 'unnamed_participant'
TRAINING_FOLDER = 'training'
COLLECTED_FOLDER = 'collected'
DEFAULT_CAMERA_INDEX = 0

# File suffixes
AURA_FILE_SUFFIX = '_aura.csv'
EMOTION_FILE_SUFFIX = '_emotions.csv'
GAZE_FILE_SUFFIX = '_gaze.csv'
POINTER_FILE_SUFFIX = '_pointer_data.csv'
TRAINING_GAZE_FILE = 'training_gaze.csv'
TRAINING_AURA_FILE = 'training_aura.csv'

# Collection types
TRAINING_MODE = 'training'
TESTING_MODE = 'testing'

# Signal types
SIGNAL_AURA = 'aura'
SIGNAL_GAZE = 'gaze'
SIGNAL_EMOTION = 'emotion'
SIGNAL_POINTER = 'pointer'
SIGNAL_SCREEN = 'screen'
SIGNAL_KEYBOARD = 'keyboard'
OPEN_CAMERA = 'open'
CLOSE_CAMERA = 'close'

# Status messages
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
START_CALIBRATION_MSG = "start-calibration"
COLLECTION_STARTED_MSG = "collection-started"
COLLECTION_STOPPED_MSG = "collection-stopped"
CALIBRATION_COMPLETE_MSG = "calibration-complete"

# Encryption constants
KEY_FILE = '.key'
ENCRYPTED_API_KEY_FILE = '.openai_key'

class BackendServer:
    """
    Backend server that handles all data collection and processing for eye tracking, emotions, 
    EEG signals and pointer tracking.

    The server uses ZMQ for communication with the frontend and manages multiple threads for
    different data collection tasks.
    """

    def __init__(self, port=DEFAULT_PORT):
        """
        Initialize the backend server with all necessary components.

        Args:
            port (str): Port number for ZMQ communication. Defaults to DEFAULT_PORT.
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

        # OpenCV video capture object
        self._camera = None
        self._last_gaze_frame = None
        self._last_emotion = None
        self._viewing_camera = False

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
        self._run_keyboard = False

        # Threads for the data collection
        self._aura_thread = None
        self._emotion_thread = None
        self._regressor_thread = None
        self._start_time = None
        self._screen_recording_thread = None

        # Path and file names for the data
        self._path = None
        self._filename = DEFAULT_PARTICIPANT

        # Aura stream id
        self._aura_stream_id = None

        # Data writers
        self._aura_writer = None
        self._emotion_writer = None
        self._gaze_writer = None
        self._pointer_writer = None

        # Folders created
        self._folders_created = False

        # OpenAI status
        self._openai_available = False

        # Status for the data collection loops
        self._data_collection_active = False
        self._training_data_collection_active = False
        self._threads = []
        self._threads_lock = threading.Lock()  # Added lock for thread-safe operations

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        # Set up OpenAI key from encrypted storage
    #     self._setup_openai_key()

    # def _setup_openai_key(self):
    #     """Set up OpenAI API key from encrypted storage."""
    #     try:
    #         # Check if key files exist, if not create them
    #         if not os.path.exists(KEY_FILE) or not os.path.exists(ENCRYPTED_API_KEY_FILE):
    #             self._initialize_encryption()
            
    #         # Load the encryption key
    #         with open(KEY_FILE, 'rb') as key_file:
    #             key = key_file.read()
            
    #         # Create Fernet instance for decryption
    #         f = Fernet(key)
            
    #         # Read and decrypt the API key
    #         with open(ENCRYPTED_API_KEY_FILE, 'rb') as api_key_file:
    #             encrypted_api_key = api_key_file.read()
    #             decrypted_api_key = f.decrypt(encrypted_api_key).decode()
            
    #         # Set the environment variable
    #         os.environ['OPENAI_API_KEY'] = decrypted_api_key
    #         self._openai_available = True
    #     except Exception as e:
    #         print(f"Error setting up OpenAI key: {e}")
    #         raise

    # def _initialize_encryption(self):
    #     """Initialize encryption key and encrypted API key storage."""
    #     try:
    #         # Generate encryption key
    #         key = Fernet.generate_key()
            
    #         # Save encryption key
    #         with open(KEY_FILE, 'wb') as key_file:
    #             key_file.write(key)
            
    #         # Create Fernet instance
    #         f = Fernet(key)
            
    #         # Get API key from user
    #         api_key = input("Please enter your OpenAI API key: ").strip()
            
    #         # Encrypt and save API key
    #         encrypted_api_key = f.encrypt(api_key.encode())
    #         with open(ENCRYPTED_API_KEY_FILE, 'wb') as api_key_file:
    #             api_key_file.write(encrypted_api_key)
            
    #     except Exception as e:
    #         print(f"Error initializing encryption: {e}")
    #         raise

    @contextmanager
    def thread_tracking(self, thread):
        """
        Context manager to track active threads.

        Args:
            thread: Thread object to track
        """
        with self._threads_lock:
            self._threads.append(thread)
        try:
            yield thread
        finally:
            with self._threads_lock:
                if thread in self._threads:
                    self._threads.remove(thread)

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
        with self._threads_lock:
            threads_copy = self._threads.copy()
        for thread in threads_copy:
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
            'update_signal': self.handle_update_signal_status,
            'start_eye_gaze': self.start_eye_gaze,
            'start': self.start_data_collection,
            'stop': self.stop_data_collection,
            'start_recording_training_data': self.start_training_data_collection,
            'stop_recording_training_data': self.stop_training_data_collection,
            'set_coordinates': self.update_coordinates,
            'update_output_path': self.update_output_path,
            'update_participant_name': self.update_participant_name,
            'new_participant': self.handle_new_participant,
            'generate_report': self.generate_report,
            'view_camera': self.view_camera,
            'stop_camera_view': self.stop_camera_view,
            'get_aura_streams': self.get_aura_streams,
            'set_aura_stream': self.set_aura_stream
        }
        handler = handlers.get(command)
        if handler:
            try:
                return handler(**params)
            except TypeError:
                # In case the handler doesn't expect any parameters
                return handler()
        else:
            return {"status": STATUS_ERROR, "message": f"Unknown command: {command}"}

    def start_eye_gaze(self):
        """Initialize and start eye gaze tracking."""
        self.manage_camera(OPEN_CAMERA)
        self._create_directories()
        self._eye_gaze = GazeProcessor()
        def eye_gaze_task():
            with self.thread_tracking(threading.current_thread()):
                while True:
                    if self._camera:
                        frame = self.get_frame()
                        gaze_data = self._eye_gaze.get_gaze_vector(frame)
                        if gaze_data[2] is not None:
                            with threading.Lock():
                                self._last_gaze_frame = gaze_data[2].copy()
                        
                        if gaze_data[0] is not None and gaze_data[1] is not None:
                            break
                self._eye_gaze_running = True
                self._fitting_eye_gaze = False
                self._socket.send_json({"status": STATUS_SUCCESS, "message": START_CALIBRATION_MSG})

        if not self._fitting_eye_gaze and not self._eye_gaze_running:
            local_thread = threading.Thread(target=eye_gaze_task, daemon=True)
            local_thread.start()
            return {"status": STATUS_SUCCESS, "message": "Eye gaze tracking started"}
        else:
            return {"status": STATUS_ERROR, "message": "Eye gaze is already started or cannot be started"}

    def start_data_collection(self):
        """Start all active data collection threads."""
        try:
            if not self._data_collection_active:
                # Create directory structure
                self._create_directories()
                self._start_time = time.time()
                self._data_collection_active = True

                # AURA
                if self._run_aura:
                    aura_response = self.start_aura()
                    if aura_response["status"] != STATUS_SUCCESS:
                        raise Exception(aura_response["message"])
                    try:
                        channels_names = ['timestamp'] + list(self._stream.info['ch_names'])
                        self._aura_writer = AuraDataWriter(self._path, f'{self._filename}{AURA_FILE_SUFFIX}', channels_names)
                        self._aura_writer.create_new_file()
                        
                        if self._aura_thread is None or not self._aura_thread.is_alive():
                            self._aura_thread = threading.Thread(
                                target=self._aura_data_collection_loop,
                                args=(TESTING_MODE,),
                                daemon=True
                            )
                            with self.thread_tracking(self._aura_thread):
                                self._socket.send_json({"status": STATUS_SUCCESS, "message": COLLECTION_STARTED_MSG, "signal": SIGNAL_AURA})
                                self._aura_thread.start()
                    except Exception as e:
                        print(f"Error starting Aura thread: {str(e)}")
                        raise
                
                # Emotion
                if self._run_emotion:
                    self.manage_camera(OPEN_CAMERA)
                    emotion_response = self.start_emotion_detection()
                    if emotion_response["status"] != STATUS_SUCCESS:
                        raise Exception(emotion_response["message"])
                    
                    self._emotion_writer = EmotionPredictedWriter(self._path, f'{self._filename}{EMOTION_FILE_SUFFIX}')
                    self._emotion_writer.create_new_file()
                    
                    if self._emotion_thread is None or not self._emotion_thread.is_alive():
                        self._emotion_thread = threading.Thread(
                            target=self._emotion_collection_loop,
                            daemon=True
                        )
                        with self.thread_tracking(self._emotion_thread):
                            self._socket.send_json({"status": STATUS_SUCCESS, "message": COLLECTION_STARTED_MSG, "signal": SIGNAL_EMOTION})
                            self._emotion_thread.start()
                
                # Coordinate/Gaze
                if self._run_gaze:
                    print("Starting tracking") # TODO: Remove
                    self._gaze_writer = CoordinateWriter(self._path, f'{self._filename}{GAZE_FILE_SUFFIX}')
                    self._gaze_writer.create_new_file()
                    
                    if self._regressor_thread is None or not self._regressor_thread.is_alive():
                        self._regressor_thread = threading.Thread(
                            target=self._coordinate_regressor_loop,
                            daemon=True
                        )
                        with self.thread_tracking(self._regressor_thread):
                            self._socket.send_json({"status": STATUS_SUCCESS, "message": COLLECTION_STARTED_MSG, "signal": SIGNAL_GAZE})
                            self._regressor_thread.start()
                
                # Pointer
                if self._run_pointer:
                    self._pointer_writer = PointerWriter(self._path, f'{self._filename}{POINTER_FILE_SUFFIX}')
                    self._pointer_writer.create_new_file()
                    pointer_response = self.start_pointer_tracking()
                    if pointer_response["status"] != STATUS_SUCCESS:
                        raise Exception(pointer_response["message"])
                    self._pointer_tracker.start_time = self._start_time
                    self._pointer_tracker.is_tracking = True
                    self._socket.send_json({"status": STATUS_SUCCESS, "message": COLLECTION_STARTED_MSG, "signal": SIGNAL_POINTER})

                # TODO: Add screen recording

                return {"status": STATUS_SUCCESS, "message": COLLECTION_STARTED_MSG}
            else:
                return {"status": STATUS_ERROR, "message": "Data collection already started"}
            
        except Exception as e:
            self._data_collection_active = False
            print(f"Error in start_data_collection: {str(e)}")
            return {"status": STATUS_ERROR, "message": f"Error starting data collection: {str(e)}"}

    def handle_stop(self):
        """Stop the server and clean up resources."""
        print("Stopping server...")
        self.cleanup()
        return {"status": STATUS_SUCCESS, "message": "Server stopped"}

    def start_training_data_collection(self):
        """Start collecting training data for eye gaze tracking."""
        # Create local writer for gaze data
        gaze_writer = GazeWriter(self._training_path, TRAINING_GAZE_FILE)
        gaze_writer.create_new_file()
        aura_training_thread = None
        if self._run_aura:
            aura_response = self.start_aura()
            if aura_response["status"] == STATUS_SUCCESS:
                aura_training_thread = threading.Thread(
                    target=self._aura_data_collection_loop,
                    args=(TRAINING_MODE,),
                    daemon=True
                )
                with self.thread_tracking(aura_training_thread):
                    aura_training_thread.start()
            else:
                print(f"Failed to start Aura for training: {aura_response['message']}")

        def training_data_task():
            with self.thread_tracking(threading.current_thread()):
                while True:
                    # Make prediction and write to file
                    if self._camera:
                        frame = self.get_frame()
                        gaze_vector = self._eye_gaze.get_gaze_vector(frame)
                        if gaze_vector[2] is not None:
                            with threading.Lock():
                                self._last_gaze_frame = gaze_vector[2].copy()
                        if gaze_vector[0] is not None and gaze_vector[1] is not None:
                            data = []
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
            local_thread = threading.Thread(target=training_data_task, daemon=True)
            with self.thread_tracking(local_thread):
                local_thread.start()
            return {"status": STATUS_SUCCESS, "message": START_CALIBRATION_MSG}
        else:
            return {"status": STATUS_ERROR, "message": "Eye gaze tracking not started"}

    def handle_stop_recording(self):
        """Stop all data recording."""
        self._data_collection_active = False
        return {"status": STATUS_SUCCESS, "message": "Recording stopped"}

    def stop_data_collection(self):
        """Stop all testing and data collection."""
        self._data_collection_active = False
        self._start_time = None
        if self._pointer_tracker is not None:
            self._pointer_tracker.stop_tracking()
            self._pointer_tracker = None  
            self._pointer_tracking_active = False 
            if self._pointer_writer:
                self._pointer_writer.close_file()
            self._pointer_writer = None  # Clear reference
        
        # Join and clear all threads
        with self._threads_lock:
            threads_copy = self._threads.copy()
        for thread in threads_copy:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        # Clear the threads list
        with self._threads_lock:
            self._threads = []
        
        # Reset thread references
        if self._viewing_camera:
            self._viewing_camera = False
            cv2.destroyAllWindows()

        self.manage_camera(CLOSE_CAMERA)
        self._aura_thread = None
        self._emotion_thread = None
        self._regressor_thread = None
        self._screen_recording_thread = None
        # Add other threads if necessary

        return {"status": STATUS_SUCCESS, "message": COLLECTION_STOPPED_MSG}

    def stop_training_data_collection(self):
        """Stop recording training data."""
        try:
            self._training_data_collection_active = False
            
            # Clean up training-specific resources
            if hasattr(self, '_aura_training_thread') and self._aura_training_thread:
                self._aura_training_thread.join(timeout=1.0)
                self._aura_training_thread = None
            
            self.start_regressor()
            return {"status": STATUS_SUCCESS, "message": CALIBRATION_COMPLETE_MSG}
        except Exception as e:
            print(f"Error stopping training data recording: {e}")
            return {"status": STATUS_ERROR, "message": str(e)}
    
    def handle_update_signal_status(self, signal, status):
        """Update the status of a signal."""
        print(f"Updating signal {signal} to {status}")
        
        # Validate signal type
        valid_signals = [SIGNAL_AURA, SIGNAL_GAZE, SIGNAL_EMOTION, 
                        SIGNAL_POINTER, SIGNAL_SCREEN, SIGNAL_KEYBOARD]
        if signal not in valid_signals:
            return {"status": STATUS_ERROR, "message": f"Invalid signal type: {signal}"}

        # Update internal state
        signal_updated = False
        if signal == SIGNAL_AURA:
            self._run_aura = status
            signal_updated = True
        elif signal == SIGNAL_GAZE:
            self._run_gaze = status
            signal_updated = True
        elif signal == SIGNAL_EMOTION:
            self._run_emotion = status
            signal_updated = True
        elif signal == SIGNAL_POINTER:
            self._run_pointer = status
            signal_updated = True
        elif signal == SIGNAL_SCREEN:
            self._run_screen = status
            signal_updated = True
        elif signal == SIGNAL_KEYBOARD:
            self._run_keyboard = status
            signal_updated = True

        if not signal_updated:
            return {"status": STATUS_ERROR, "message": "No signal was updated"}

        # Send status update message
        self._socket.send_json({
            "type": "signal_update",
            "signal": signal,
            "status": status,
            "message": f"Signal {signal} updated to {status}"
        })
        
        return {"status": STATUS_SUCCESS, "message": f"Signal {signal} updated to {status}"}

    # Signal initialization functions

    def start_pointer_tracking(self):
        """Initialize and start pointer tracking."""
        if not self._pointer_tracking_active:
            self._pointer_tracker = CursorTracker(writer=self._pointer_writer)
            self._pointer_tracking_active = True
            return {"status": STATUS_SUCCESS, "message": "Pointer tracking started"}
        else:
            return {"status": STATUS_ERROR, "message": "Pointer tracking already active"}
        
    def start_regressor(self):
        """Initialize and start the position regressor."""
        path = os.path.join(self._training_path, TRAINING_GAZE_FILE)
        self._regressor = PositionRegressor(path)
        self._regressor.train_create_model()

        self._regressor_thread = threading.Thread(
            target=self._coordinate_regressor_loop,
            daemon=True
        )

        return {"status": STATUS_SUCCESS, "message": "Regressor started"}

    def start_aura(self, buffer_size_multiplier=1):
        try:
            if self._aura_stream_id is None:
                try:
                    if self._aura_stream_id is None:
                        stream_ids = resolve_aura()
                        if len(stream_ids) == 0:
                            return {"status": STATUS_ERROR, "message": "No aura stream found"}
                        self._aura_stream_id = stream_ids[0]
                        
                    self._stream = Stream(bufsize=buffer_size_multiplier, source_id=self._aura_stream_id)
                    self._stream.connect(processing_flags='all')
                    rename_aura_channels(self._stream)
                except ValueError as e:
                    return {"status": STATUS_ERROR, "message": str(e)}
                
            # Create thread without starting it
            self._aura_thread = threading.Thread(
                target=self._aura_data_collection_loop,
                args=(TESTING_MODE,),
                daemon=True
            )

            # Add to thread tracking
            self._threads.append(self._aura_thread)

            return {"status": STATUS_SUCCESS, "message": "Aura signal handling initialized"}
        except Exception as e:
            print(f"Error in handle_aura_signal: {str(e)}")
            return {"status": STATUS_ERROR, "message": str(e)}

    def start_emotion_detection(self):
        """
        Initialize and start emotion recognition.
        """
        try:
            self._emotion_handler = EmotionRecognizer('opencv')
            self._emotion_thread = threading.Thread(target=self._emotion_collection_loop, daemon=True)

            return {"status": STATUS_SUCCESS, "message": "Emotion recognition started"}
        except Exception as e:
            return {"status": STATUS_ERROR, "message": str(e)}
    
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
            if collection_type == TRAINING_MODE:
                channels_names = ['timestamp'] + self._stream.info['ch_names']
                aura_writer_training = AuraDataWriter(self._training_path, TRAINING_AURA_FILE, channels_names)
                aura_writer_training.create_new_file()
            
            while True:
                if is_stream_ready(self._stream):
                    data, ts = self._stream.get_data()
                    if collection_type == TRAINING_MODE:
                        if aura_writer_training:
                            aura_writer_training.write_data(ts, data)
                    else:
                        processed_ts = [round(t - self._start_time, 3) for t in ts]
                        self._aura_writer.write_data(processed_ts, data)

                time.sleep(0.001)

                if collection_type == TRAINING_MODE and not self._training_data_collection_active:
                    if aura_writer_training:
                        aura_writer_training.close_file()
                    break
                elif collection_type == TESTING_MODE and not self._data_collection_active:
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
        with self.thread_tracking(threading.current_thread()):
            while True:
                if self._emotion_handler and self._camera:
                    frame = self.get_frame()
                    emotion = self._emotion_handler.recognize_emotion(frame)
                    with threading.Lock():
                        self._last_emotion = emotion
                    if emotion is not None:
                        emotion = emotion[0]['dominant_emotion']
                        timestamp = round(time.time() - self._start_time, 3)
                        self._emotion_writer.write_data(timestamp, emotion)
                time.sleep(0.001)  # Small sleep to prevent CPU overuse
                if not self._data_collection_active:
                    break
            if self._emotion_writer:
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
        with self.thread_tracking(threading.current_thread()):
            while True:
                if self._camera:
                    frame = self.get_frame()
                    gaze_vector = self._eye_gaze.get_gaze_vector(frame)
                    if gaze_vector[2] is not None:
                        with threading.Lock():
                            self._last_gaze_frame = gaze_vector[2].copy()
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
                        timestamp = round(time.time() - self._start_time, 3)
                        self._gaze_writer.write(timestamp, [x, y])
                        
                if not self._data_collection_active:
                    break

    def update_coordinates(self, x, y):
        """
        Update current coordinates.

        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        self._current_x_coordinate = x
        self._current_y_coordinate = y
        return {"status": STATUS_SUCCESS, "coordinates": [x, y]}
    
    def update_output_path(self, path):
        """Update the base output path and create necessary subdirectories."""
        try:
            self._base_path = path
            self._participant_folder = path
            self._path = os.path.join(path, COLLECTED_FOLDER)
            self._training_path = os.path.join(path, TRAINING_FOLDER)
            
            return {"status": STATUS_SUCCESS, "message": "Output path updated"}
        except Exception as e:
            return {"status": STATUS_ERROR, "message": str(e)}

    def update_participant_name(self, name):
        """Update the participant name and update folder structure accordingly."""
        try:
            self._filename = name if name else DEFAULT_PARTICIPANT
            
            # Update paths with new participant name
            if hasattr(self, '_base_path'):
                self.update_output_path(self._base_path)
            
            return {"status": STATUS_SUCCESS, "message": f"Participant name updated to {name}"}
        except Exception as e:
            return {"status": STATUS_ERROR, "message": str(e)}
    
    def handle_new_participant(self):
        """Handle a new participant by resetting name and creating new directories."""
        try:
            self._filename = DEFAULT_PARTICIPANT
            self._current_x_coordinate = 0
            self._current_y_coordinate = 0
            self._folders_created = False
            # Update paths for new participant
            if hasattr(self, '_base_path'):
                self.update_output_path(self._base_path)
            
            if self._eye_gaze:
                self._eye_gaze.stop_processing()
            if self._emotion_handler:
                self._emotion_handler.stop_processing()
            
            return {"status": STATUS_SUCCESS, "message": "New participant started"}
        except Exception as e:
            return {"status": STATUS_ERROR, "message": str(e)}
    
    def generate_report(self):
        """
        Generates a report by sending data files to the OpenAI API and querying for analysis.
        Saves the report in markdown format.
        """
        data_analyzer = DataAnalyzer()
        try:
            # Initialize DataAnalyzer
            data_files = self._get_data_files()
            if not data_files:
                return {
                    "status": STATUS_ERROR,
                    "message": "No data files available for report generation."
                }

            # Upload files and handle potential upload errors
            try:
                for file_path in data_files:
                    if AURA_FILE_SUFFIX in file_path:
                        training_file = os.path.join(os.path.dirname(self._training_path), 'training', f'{self._filename}_{TRAINING_AURA_FILE}')
                        print(training_file)
                        print(file_path)
                        data_analyzer.preprocess_aura(file_path, training_file)
                    else:
                        data_analyzer.upload_file(file_path)
            except Exception as e:
                return {
                    "status": STATUS_ERROR,
                    "message": f"Failed to upload files to OpenAI: {str(e)}"
                }
            
            # Read and concatenate CSV file contents
            csv_contents = {}
            for file_path in data_files:
                try:
                    with open(file_path, 'r') as file:
                        csv_contents[os.path.basename(file_path)] = file.read()
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    return {
                        "status": STATUS_ERROR,
                        "message": f"Failed to read {os.path.basename(file_path)}: {str(e)}"
                    }

            # Construct the prompt with rules and CSV data
            prompt = f"""
            <context>
            You are analyzing data files from a user attention study. Your task is to perform ONLY factual, data-driven analysis based on the actual contents of the provided files.

            Available Data Channels:
            """
            if self._run_aura:
                prompt += f"- EEG data (BETA waves) from file: {self._filename}{AURA_FILE_SUFFIX}\n"
            if self._run_gaze:
                prompt += f"- Gaze tracking data from file: {self._filename}{GAZE_FILE_SUFFIX}\n"
            if self._run_pointer:
                prompt += f"- Mouse pointer data from file: {self._filename}{POINTER_FILE_SUFFIX}\n"
            if self._run_emotion:
                prompt += f"- Facial emotion data from file: {self._filename}{EMOTION_FILE_SUFFIX}\n"

            prompt += """
            CRITICAL ANALYSIS RULES:
            1. Only analyze data from files that are actually present in the provided content
            2. Make NO assumptions about data you cannot see
            3. Every single statement must be backed by specific data points from the files
            5. For any pattern or trend mentioned, cite the exact data points that demonstrate it
            6. Express uncertainty clearly when data is incomplete or inconclusive
            7. NO speculation about user intent or psychological state unless directly measured
            8. NO references to data channels that are not present in the files

            REQUIRED DATA VALIDATION:
            - List the exact files you are analyzing
            - Report the exact number of data points in each file
            - Note any gaps or inconsistencies in the data
            - Specify the time range covered by each data stream
            """
            for filename, content in csv_contents.items():
                prompt += f"### {filename}\n{content}\n\n"

            prompt += """
            Provide a strictly data-driven report with these sections:

            1. Data Inventory and Quality Assessment:
            - Exact files analyzed with row counts
            - Complete timestamp ranges
            - Data completeness metrics
            - Sampling rates and consistency

            2. Statistical Analysis Per Channel:
            - Basic statistics (mean, median, std dev, range)
            - Distribution analysis with specific values
            - Temporal patterns supported by timestamps
            - Anomaly detection with exact data points

            3. Cross-Channel Correlations (only for present channels):
            - Pearson/Spearman correlation coefficients
            - Temporal alignment analysis
            - Synchronized events with timestamps
            - Statistical significance levels

            4. Evidence-Based Findings:
            - Only patterns visible in the data
            - Confidence intervals for all metrics
            - Limitations of the analysis
            - Areas where data is insufficient

            FORMAT REQUIREMENTS:
            - Every finding must reference specific data
            - Use precise numbers and timestamps
            - Include confidence levels for all conclusions
            - Explicitly state when something cannot be determined from the data
            - Do not ask questions or suggest further analysis

            ABOUT THE DATA:
            The EEG data is normalized using the training data averages. This is done by dividing each beta value by its corresponding training average.
            The value of reference is 1 anything that is 1 or close to 1 is normal, above 1 is above average and below 1 is below average. All of these of beta waves that consider concentation.
            The timestamp is rounded to 3 decimal places to reduce the amount of data sent to the LLM. And there migh be small variations of it.
            """

            # Call OpenAI API via DataAnalyzer
            try:
                llm_response = data_analyzer.query(prompt)
                if not llm_response:
                    return {
                        "status": STATUS_ERROR,
                        "message": "No response received from the AI model."
                    }
                
                # Save report as markdown file
                report_filename = f"{self._filename}_report.md"
                report_path = os.path.join(self._participant_folder, report_filename)
                try:
                    with open(report_path, 'w') as f:
                        f.write(llm_response)
                except Exception as e:
                    print(f"Warning: Failed to save report file: {e}")
                
                return {
                    "status": STATUS_SUCCESS,
                    "message": llm_response,
                }
            except TimeoutError:
                return {
                    "status": STATUS_ERROR,
                    "message": "Report generation timed out. Please try again."
                }
            except Exception as e:
                return {
                    "status": STATUS_ERROR,
                    "message": f"Error during AI analysis: {str(e)}"
                }

        except Exception as e:
            print(f"Error in generate_report: {e}")
            return {
                "status": STATUS_ERROR,
                "message": f"Failed to generate report: {str(e)}"
            }
        finally:
            # Ensure cleanup of resources
            if data_analyzer:
                try:
                    data_analyzer.cleanup_files()
                except Exception as e:
                    print(f"Warning: Failed to cleanup files: {e}")
    
    def _create_directories(self):
        if not self._folders_created:
            os.makedirs(self._participant_folder, exist_ok=True)
            os.makedirs(self._path, exist_ok=True)
            os.makedirs(self._training_path, exist_ok=True)
            self._folders_created = True
        
    def _get_data_files(self):
        """
        Retrieve the list of data files to be uploaded.
        """
        suffixes = [
            AURA_FILE_SUFFIX,
            EMOTION_FILE_SUFFIX,
            GAZE_FILE_SUFFIX,
            POINTER_FILE_SUFFIX
        ]
        files = []
        for suffix in suffixes:
            file_path = os.path.join(self._path, f"{self._filename}{suffix}")
            if os.path.exists(file_path):
                files.append(file_path)
            else:
                print(f"Warning: {file_path} does not exist and will be skipped.")
        return files

    def manage_camera(self, action='open'):
        """
        Open or close the camera.
        
        Args:
            action (str): Either 'open' or 'close'. Defaults to 'open'.
            
        Returns:
            dict: Status message indicating success or failure
        """
        try:
            if action == 'open':
                if self._camera is None or not self._camera.isOpened():
                    self._camera = cv2.VideoCapture(DEFAULT_CAMERA_INDEX)
                    if not self._camera.isOpened():
                        raise Exception("Could not open camera")
            elif action == 'close':
                if self._camera is not None:
                    self._camera.release()
                    self._camera = None     
            else:
                return {"status": STATUS_ERROR, "message": f"Invalid action: {action}"}
                
        except Exception as e:
            if self._camera is not None:
                self._camera.release()
                self._camera = None

    def get_frame(self):
        """
        Get the current frame from the video capture object.
        """
        if self._camera is not None:
            _, frame = self._camera.read()
            return frame
        return None
    
    def view_camera(self):
        """
        Capture frames from the camera and stream them to the frontend via ZMQ.
        """
        # Make sure camera is open
        if self._camera is None or not self._camera.isOpened():
            self.manage_camera(OPEN_CAMERA)
            
        def stream_frames():
            try:
                print("Starting camera stream...")
                while self._viewing_camera:
                    try:
                        # Get and process camera frame
                        frame = self.get_frame()
                        if frame is not None:
                            # Encode camera frame
                            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                            if ret:
                                # Send camera frame
                                self._socket.send_json({
                                    'type': 'frame',
                                    'data': base64.b64encode(buffer).decode('utf-8')
                                })
                        
                        # Get and process gaze frame if available
                        with threading.Lock():
                            gaze_frame = getattr(self, '_last_gaze_frame', None)
                            if gaze_frame is not None:
                                # Encode gaze frame
                                ret, gaze_buffer = cv2.imencode('.jpg', gaze_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                                if ret:
                                    # Send gaze frame
                                    self._socket.send_json({
                                        'type': 'gaze_frame',
                                        'data': base64.b64encode(gaze_buffer).decode('utf-8')
                                    })
                        
                        time.sleep(0.033)  # ~30 FPS
                    except Exception as e:
                        print(f"Error processing frame: {e}")
                        time.sleep(0.1)  # Add delay on error
                        
            except Exception as e:
                print(f"Fatal error in stream_frames: {e}")
            finally:
                self._viewing_camera = False
                print("Camera streaming stopped")

        # Start streaming in a new thread if not already streaming
        if not self._viewing_camera:
            self._viewing_camera = True
            threading.Thread(target=stream_frames, daemon=True).start()
            return {"status": "success", "message": "Camera streaming started"}
        else:
            return {"status": "error", "message": "Camera is already streaming"}

    def stop_camera_view(self):
        """Stop the camera stream."""
        self._viewing_camera = False
        return {"status": "success", "message": "Camera streaming stopped"}
    
    def get_aura_streams(self):
        """
        Get the list of AURA streams.
        """
        try:
            streams = resolve_aura()
            return {"status": "success", "streams": streams}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def set_aura_stream(self, stream_id):
        """
        Set the AURA stream.
        """
        self._aura_stream_id = stream_id