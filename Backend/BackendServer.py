import zmq
import time
import threading
import signal
import sys
import os
from contextlib import contextmanager
import hashlib
from datetime import datetime

from mne_lsl.stream import StreamLSL as Stream
from DataProcessing.LLMProcessor import DataAnalyzer


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

# Constants
DEFAULT_PORT = "5556"
DEFAULT_FILENAME = 'unnamed'
DEFAULT_AURA_STREAM_ID = 'filtered'
DEFAULT_PARTICIPANT = 'unnamed_participant'
TRAINING_FOLDER = 'training'
COLLECTED_FOLDER = 'collected'

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

# Status messages
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
START_CALIBRATION_MSG = "start-calibration"
COLLECTION_STARTED_MSG = "collection-started"
COLLECTION_STOPPED_MSG = "collection-stopped"
CALIBRATION_COMPLETE_MSG = "calibration-complete"

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
        self._path = None
        self._filename = DEFAULT_FILENAME

        # Aura stream id
        # TODO: Make this dynamic
        self._aura_stream_id = DEFAULT_AURA_STREAM_ID

        # Data writers
        self._aura_writer = None
        self._emotion_writer = None
        self._gaze_writer = None
        self._pointer_writer = None

        # Status for the data collection loops
        self._data_collection_active = False
        self._training_data_collection_active = False
        self._threads = []
        self._threads_lock = threading.Lock()  # Added lock for thread-safe operations

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

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
            'update_signal_status': self.handle_update_signal_status,
            'start_eye_gaze': self.start_eye_gaze,
            'start': self.start_data_collection,
            'stop': self.stop_data_collection,
            'start_recording_training_data': self.start_training_data_collection,
            'stop_recording_training_data': self.stop_training_data_collection,
            'set_coordinates': self.update_coordinates,
            'update_output_path': self.update_output_path,
            'update_participant_name': self.update_participant_name,
            'new_participant': self.handle_new_participant,
            'generate_report': self.generate_report
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
        def eye_gaze_task():
            with self.thread_tracking(threading.current_thread()):
                self._eye_gaze = create_new_eye_gaze()
                self._eye_gaze_running = True
                self._fitting_eye_gaze = False
                self._socket.send_json({"status": STATUS_SUCCESS, "message": START_CALIBRATION_MSG})

        if not self._fitting_eye_gaze and self._run_gaze:
            self._fitting_eye_gaze = True
            local_thread = threading.Thread(target=eye_gaze_task, daemon=True)
            local_thread.start()
            return {"status": STATUS_SUCCESS, "message": "Eye gaze tracking started"}
        else:
            return {"status": STATUS_ERROR, "message": "Eye gaze is already started or cannot be started"}

    def start_data_collection(self):
        """Start all active data collection threads."""
        try:
            if not self._data_collection_active:
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
                                self._aura_thread.start()
                    
                    except Exception as e:
                        print(f"Error starting Aura thread: {str(e)}")
                        raise
                
                # Emotion
                if self._run_emotion:
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
                            self._emotion_thread.start()
                
                # Coordinate/Gaze
                if self._run_gaze:
                    self._gaze_writer = CoordinateWriter(self._path, f'{self._filename}{GAZE_FILE_SUFFIX}')
                    self._gaze_writer.create_new_file()
                    
                    if self._regressor_thread is None or not self._regressor_thread.is_alive():
                        self._regressor_thread = threading.Thread(
                            target=self._coordinate_regressor_loop,
                            daemon=True
                        )
                        with self.thread_tracking(self._regressor_thread):
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
        # self._start_time = None
        if self._pointer_tracker is not None:
            self._pointer_tracker.stop_tracking()
            self._pointer_tracker.is_tracking = False
            self._pointer_tracker.clear_coordinates()
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
        bool_status = status.lower() == 'true'
        if signal == SIGNAL_AURA:
            self._run_aura = bool_status
        elif signal == SIGNAL_GAZE:
            self._run_gaze = bool_status
        elif signal == SIGNAL_EMOTION:
            self._run_emotion = bool_status
        elif signal == SIGNAL_POINTER:
            self._run_pointer = bool_status
        elif signal == SIGNAL_SCREEN:
            self._run_screen = bool_status
        
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
            self._stream = Stream(bufsize=buffer_size_multiplier, source_id=self._aura_stream_id)
            self._stream.connect(processing_flags='all')
            rename_aura_channels(self._stream)

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
                if self._emotion_handler:
                    emotion = self._emotion_handler.recognize_emotion()
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
            self._participant_folder = os.path.join(path, self._filename or DEFAULT_PARTICIPANT)
            self._path = os.path.join(self._participant_folder, COLLECTED_FOLDER)
            self._training_path = os.path.join(self._participant_folder, TRAINING_FOLDER)
            
            # Create directory structure
            os.makedirs(self._participant_folder, exist_ok=True)
            os.makedirs(self._path, exist_ok=True)
            os.makedirs(self._training_path, exist_ok=True)
            
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
            Generates a report by uploading data files to the LLMProcessor and querying for analysis.
            """
            try:
                # Initialize DataAnalyzer
                data_analyzer = DataAnalyzer()

                # Generate and set collection_id
                collection_id = self._generate_collection_id()
                data_analyzer.collection_id = collection_id

                # Retrieve data files
                data_files = self._get_data_files()
                if not data_files:
                    return {
                        "status": STATUS_ERROR,
                        "message": "No data files available for report generation."
                    }

                # Upload files and add to collection
                for file_path in data_files:
                    file_id = data_analyzer.upload_file(file_path)
                    data_analyzer.add_file_to_collection(file_id)

                # Query the LLM for report generation
                query = f"""
                I am giving you data files from a user study about user attention on screen. The following data channels are available:
                {f'- EEG data (focusing on BETA waves for brain activity analysis)' if self._run_aura else ''}
                {f'- Gaze tracking data (screen coordinates where user is looking)' if self._run_gaze else ''}
                {f'- Mouse pointer data (click coordinates)' if self._run_pointer else ''}
                {f'- Facial emotion data' if self._run_emotion else ''}

                All files use timestamps in seconds that are synchronized across channels.

                Please generate a comprehensive report analyzing:
                - Average duration of user attention spans
                - Speed/patterns of focus movement across the screen
                - Notable patterns or correlations between available data channels
                - Key insights about user attention and engagement

                Only analyze the data channels listed above as available. Do not speculate about unavailable data.
                Provide a complete report without requesting additional information. JUST THE REPORT, NO OTHER TEXT.
                """
                llm_response = data_analyzer.query(query)

                return {
                    "status": STATUS_SUCCESS,
                    "message": llm_response,
                }

            except Exception as e:
                print(f"Error in generate_report: {e}")
                return {
                    "status": STATUS_ERROR,
                    "message": f"Failed to generate report: {str(e)}"
                }
    
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

    def _generate_collection_id(self):
        """
        Generate a unique collection ID based on the current day, path, and participant name.
        """
        current_day = datetime.now().strftime("%Y-%m-%d")
        path_str = self._path or "default_path"
        name_str = self._filename or "default_name"
        unique_str = f"{current_day}_{path_str}_{name_str}"
        return hashlib.sha256(unique_str.encode()).hexdigest()
    