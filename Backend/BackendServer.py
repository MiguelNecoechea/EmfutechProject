import zmq
import time
import threading
import signal
import sys
import cv2
import os
import queue
from contextlib import contextmanager
import base64
import json
import platform
import weakref
from typing import Set, Optional

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
from IO.FileWriting.KeyboardWriter import KeyboardWriter
from IO.KeyboardTracking.KeyboardTracker import KeyboardTracker
from IO.ScreenRecording.ScreenRecorder import ScreenRecorder
from DataProcessing.ProcessAuraData import process_concentration_data

import subprocess
import sys
from pathlib import Path

from Backend.CameraManager import CameraManager

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
KEYBOARD_FILE_SUFFIX = '_keyboard.csv'
SCREEN_FILE_SUFFIX = '_screen.mp4'

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
        # Add signal handlers first thing
        self._setup_signal_handlers()
        
        # Server setup
        self._aura_training_thread = None
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.PAIR)
        self._socket.bind(f"tcp://*:{port}")

        # Training points coordinates for calibration
        self._current_x_coordinate = 0
        self._current_y_coordinate = 0

        # Add ZMQ socket for eye tracking communication
        self._eye_tracking_socket = self._context.socket(zmq.PAIR)
        self._eye_tracking_socket.bind("tcp://*:5557")
    
        # Add eye tracking process reference
        self._eye_tracking_process = None

        # Flags for the server status.
        self._running = False
        self._shutdown = False

        # OpenCV video capture object
        self._camera = None
        self._emotion_camera = None
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
        self._screen_recorder = None

        # Boolean flags for deciding the experiments to run
        self._run_aura = False
        self._run_emotion = False
        self._run_gaze = False
        self._run_pointer = False
        self._run_screen = False
        self._run_keyboard = False

        # Active threads set using weak references to avoid memory leaks
        self._active_threads: Set[weakref.ref] = set()
        self._threads_lock = threading.Lock()

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

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

        # Add keyboard tracking objects
        self._keyboard_tracker = None
        self._keyboard_writer = None

        # Aura files
        self._aura_file = None
        self._aura_training_file = None

        # Screen recording file
        self._screen_recording_file = None

        self._camera_manager = CameraManager()

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def handle_signal(signum, frame):
            print(f"\nReceived signal {signum}, initiating graceful shutdown...")
            self.cleanup()
            # Use os._exit instead of sys.exit to avoid threading issues
            import os
            os._exit(0)

        # Handle both SIGTERM and SIGINT
        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)

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
        if self._shutdown:  # Prevent multiple cleanups
            return
            
        print("\n=== Starting BackendServer cleanup ===")
        
        try:
            # Set flags first
            self._shutdown = True
            self._running = False
            self._data_collection_active = False
            self._training_data_collection_active = False
            self._viewing_camera = False

            # Stop all active processes first
            print("Stopping all active processes...")
            if self._eye_tracking_process:
                try:
                    print("Stopping eye tracking process...")
                    self._eye_tracking_socket.send_json({"command": "stop"})
                    self._eye_tracking_process.terminate()
                    self._eye_tracking_process.wait(timeout=5)
                    self._eye_tracking_process = None
                except Exception as e:
                    print(f"Error stopping eye tracking process: {e}")

            # Clean up threads first
            print("Cleaning up threads...")
            self._cleanup_threads(timeout=2.0)

            # Clean up other resources that might hold semaphores
            resources_to_cleanup = [
                (self._pointer_tracker, 'stop_tracking'),
                (self._emotion_handler, 'stop_processing'),
                (self._screen_recorder, 'stop_recording')
            ]
            
            for resource, cleanup_method in resources_to_cleanup:
                if resource:
                    try:
                        getattr(resource, cleanup_method)()
                    except Exception as e:
                        print(f"Error cleaning up resource {resource}: {e}")
                    finally:
                        setattr(self, f"_{resource.__class__.__name__.lower()}", None)

            # Close all writers
            writers = [self._aura_writer, self._emotion_writer, 
                      self._gaze_writer, self._pointer_writer]
            for writer in writers:
                if writer:
                    try:
                        writer.close_file()
                    except Exception as e:
                        print(f"Error closing writer: {e}")

            # Clean up camera resources last
            print("Cleaning up camera manager...")
            if hasattr(self, '_camera_manager'):
                # First unregister all users
                for user in ['eye_gaze', 'emotion', 'viewer']:
                    self._camera_manager.unregister_user(user)
                # Then shutdown the manager
                self._camera_manager.shutdown()
                self._camera_manager = None

            # Clean up ZMQ resources
            if hasattr(self, '_socket') and self._socket:
                self._socket.close(linger=0)
            if hasattr(self, '_context') and self._context:
                self._context.term()

            # Final cleanup of resources
            self._last_gaze_frame = None
            self._last_emotion = None
            self._camera = None
            self._emotion_camera = None

            # Force garbage collection
            import gc
            gc.collect()

            print("\n=== Cleanup completed ===")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            # Ensure these are always cleared
            self._aura_writer = None
            self._emotion_writer = None
            self._gaze_writer = None
            self._pointer_writer = None
            
            # Final multiprocessing cleanup
            try:
                print("\n=== Final multiprocessing cleanup ===")
                import multiprocessing
                import multiprocessing.resource_tracker
                
                # Ensure all processes are done before cleaning up resources
                multiprocessing.active_children()
                
                # Clean up resource tracker
                if hasattr(multiprocessing.resource_tracker, '_resource_tracker'):
                    tracker = multiprocessing.resource_tracker._resource_tracker
                    if tracker:
                        tracker._cleanup()
                
                # Force final garbage collection
                gc.collect()
                
            except Exception as e:
                print(f"Error in final multiprocessing cleanup: {str(e)}")

    def __del__(self):
        """Ensure cleanup is called when the object is deleted."""
        if not hasattr(self, '_shutdown') or not self._shutdown:
            print("BackendServer.__del__ calling cleanup")
            self.cleanup()

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
            'set_aura_stream': self.set_aura_stream,
            'shutdown': self.cleanup,
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
        try:
            if not self._fitting_eye_gaze and not self._eye_gaze_running:
                if self._camera_manager.register_user('eye_gaze'):
                    self._create_directories()
                    self._eye_gaze = GazeProcessor()
                    
                    def eye_gaze_task():
                        try:
                            self._add_thread(threading.current_thread())
                            self.send_signal_update(SIGNAL_GAZE, 'connecting')
                            while True:
                                frame = self._camera_manager.get_frame()
                                if frame is not None:   
                                    gaze_data = self._eye_gaze.get_gaze_vector(frame)
                                    if gaze_data[2] is not None:
                                        with threading.Lock():
                                            self._last_gaze_frame = gaze_data[2].copy()
                                
                                    if gaze_data[0] is not None and gaze_data[1] is not None:
                                        break
                            self._eye_gaze_running = True
                            self._fitting_eye_gaze = False
                            self._socket.send_json({"status": STATUS_SUCCESS, "message": START_CALIBRATION_MSG})
                        finally:
                            self._remove_thread(threading.current_thread())

                    local_thread = threading.Thread(target=eye_gaze_task, daemon=True)
                    local_thread.start()
                    return {"status": STATUS_SUCCESS, "message": "Eye gaze tracking started"}
                else:
                    raise Exception("Failed to initialize camera for eye tracking")
            else:
                return {"status": STATUS_ERROR, "message": "Eye gaze is already started or cannot be started"}
        except Exception as e:
            self._camera_manager.unregister_user('eye_gaze')
            print(f"Error starting eye gaze: {e}")
            return {"status": STATUS_ERROR, "message": str(e)}

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
                        self._aura_file = os.path.join(self._path, f'{self._filename}{AURA_FILE_SUFFIX}')
                        self._aura_writer = AuraDataWriter(self._path, f'{self._filename}{AURA_FILE_SUFFIX}', channels_names)
                        self._aura_writer.create_new_file()
                        
                        if self._aura_thread is None or not self._aura_thread.is_alive():
                            self._aura_thread = threading.Thread(
                                target=self._aura_data_collection_loop,
                                args=(TESTING_MODE,),
                                daemon=True
                            )
                            self._socket.send_json({"status": STATUS_SUCCESS, "message": COLLECTION_STARTED_MSG, "signal": SIGNAL_AURA})
                            self._aura_thread.start()
                    except Exception as e:
                        print(f"Error starting Aura thread: {str(e)}")
                        raise
                
                # Emotion
                if self._run_emotion:
                    self._emotion_camera = cv2.VideoCapture(DEFAULT_CAMERA_INDEX)
                    emotion_response = self.start_emotion_detection()
                    if emotion_response["status"] != STATUS_SUCCESS:
                        self._emotion_camera.release()
                        self._emotion_camera = None
                        self.send_signal_update(SIGNAL_EMOTION, 'error')
                        raise Exception(emotion_response["message"])
                    
                    self._emotion_writer = EmotionPredictedWriter(self._path, f'{self._filename}{EMOTION_FILE_SUFFIX}')
                    self._emotion_writer.create_new_file()
                    
                    if self._emotion_thread is None or not self._emotion_thread.is_alive():
                        self._emotion_thread = threading.Thread(
                            target=self._emotion_collection_loop,
                            daemon=True
                        )
                        self._socket.send_json({"status": STATUS_SUCCESS, "message": COLLECTION_STARTED_MSG, "signal": SIGNAL_EMOTION})
                        self._emotion_thread.start()
                
                # Coordinate/Gaze
                if self._run_gaze:
                    self._gaze_writer = CoordinateWriter(self._path, f'{self._filename}{GAZE_FILE_SUFFIX}')
                    self._gaze_writer.create_new_file()
                    
                    if self._eye_tracking_process is not None:
                        # Using Beam eye tracking
                        def beam_gaze_collection_loop():
                            try:
                                self._add_thread(threading.current_thread())
                                while self._data_collection_active:
                                    try:
                                        message = self._eye_tracking_socket.recv_json(flags=zmq.NOBLOCK)
                                        if message.get("type") == "gaze_coordinates":
                                            gaze_data = message["data"]
                                            timestamp = round(time.time() - self._start_time, 3)
                                            self._gaze_writer.write(timestamp, [gaze_data["x"], gaze_data["y"]])
                                    except zmq.error.Again:
                                        time.sleep(0.001)  # Brief sleep when no message
                                    except Exception as e:
                                        print(f"Error in beam gaze collection: {e}")
                                        break
                            finally:
                                self._remove_thread(threading.current_thread())

                        self._regressor_thread = threading.Thread(
                            target=beam_gaze_collection_loop,
                            daemon=True
                        )
                    else:
                        # Using webcam-based tracking
                        self._regressor_thread = threading.Thread(
                            target=self._coordinate_regressor_loop,
                            daemon=True
                        )
                    
                    self._socket.send_json({"status": STATUS_SUCCESS, "message": COLLECTION_STARTED_MSG, "signal": SIGNAL_GAZE})
                    self._regressor_thread.start()
                
                # Pointer
                if self._run_pointer:
                    self._pointer_writer = PointerWriter(self._path, f'{self._filename}{POINTER_FILE_SUFFIX}')
                    self._pointer_writer.create_new_file()
                    pointer_response = self.start_pointer_tracking()
                    if pointer_response["status"] != STATUS_SUCCESS:
                        self.send_signal_update(SIGNAL_POINTER, 'error')
                        raise Exception(pointer_response["message"])
                    self._pointer_tracker.start_time = self._start_time
                    self._pointer_tracker.is_tracking = True
                    self.send_signal_update(SIGNAL_POINTER, 'recording')
                    self._socket.send_json({"status": STATUS_SUCCESS, "message": COLLECTION_STARTED_MSG, "signal": SIGNAL_POINTER})

                # Keyboard
                if self._run_keyboard:
                    self._keyboard_writer = KeyboardWriter(self._path, f'{self._filename}{KEYBOARD_FILE_SUFFIX}')
                    self._keyboard_writer.create_new_file()
                    keyboard_response = self.start_keyboard_tracking()
                    if keyboard_response["status"] != STATUS_SUCCESS:
                        self.send_signal_update(SIGNAL_KEYBOARD, 'error')
                        raise Exception(keyboard_response["message"])
                    self._keyboard_tracker.start_time = self._start_time
                    self._keyboard_tracker.is_tracking = True
                    self.send_signal_update(SIGNAL_KEYBOARD, 'recording')
                    self._socket.send_json({"status": STATUS_SUCCESS, "message": COLLECTION_STARTED_MSG, "signal": SIGNAL_KEYBOARD})

                if self._run_screen:
                    screen_response = self.start_screen_recording()
                    if screen_response["status"] != STATUS_SUCCESS:
                        self.send_signal_update(SIGNAL_SCREEN, 'error')
                    else:
                        self.send_signal_update(SIGNAL_SCREEN, 'recording')
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
                aura_training_thread.start()
            else:
                print(f"Failed to start Aura for training: {aura_response['message']}")

        def training_data_task():
            try:
                self._add_thread(threading.current_thread())
                while True:
                    # Make prediction and write to file
                    frame = self._camera_manager.get_frame()
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
            finally:
                self._remove_thread(threading.current_thread())

        if self._eye_gaze_running:
            self._training_data_collection_active = True
            local_thread = threading.Thread(target=training_data_task, daemon=True)
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
        try:
            self._data_collection_active = False
            self._training_data_collection_active = False

            # Stop pointer tracking
            if self._pointer_tracker is not None:
                self._pointer_tracker.stop_tracking()
                self._pointer_tracker = None  
                self._pointer_tracking_active = False 
                if self._pointer_writer:
                    self._pointer_writer.close_file()
                self._pointer_writer = None

            # Stop emotion detection and unregister from camera
            if self._emotion_handler:
                self._emotion_handler.stop_processing()
                self._emotion_handler = None
                self._camera_manager.unregister_user('emotion')

            # Stop keyboard tracking
            if self._keyboard_tracker is not None:
                self._keyboard_tracker.stop_tracking()
                self._keyboard_tracker = None
                if self._keyboard_writer:
                    self._keyboard_writer.close_file()
                self._keyboard_writer = None

            # Stop screen recording
            if self._screen_recorder is not None:
                try:
                    self._screen_recorder.stop_recording()
                except Exception as e:
                    print(f"Error stopping screen recording: {e}")
                finally:
                    self._screen_recorder = None
                    self.send_signal_update(SIGNAL_SCREEN, 'ready')

            # Join and clear all threads with timeout
            with self._threads_lock:
                threads_copy = self._threads.copy()
            
            for thread in threads_copy:
                if thread and thread.is_alive():
                    thread.join(timeout=1.0)
            
            # Clear the threads list
            with self._threads_lock:
                self._threads.clear()
            
            # Stop camera viewing
            if self._viewing_camera:
                self._viewing_camera = False
                cv2.destroyAllWindows()

            # Unregister all camera users and cleanup camera
            for user in ['eye_gaze', 'emotion', 'viewer']:
                self._camera_manager.unregister_user(user)
            self._camera_manager.cleanup_camera()  # Explicitly cleanup the camera

            if self._run_aura:
                process_concentration_data(self._aura_file, self._aura_training_file)

            # Clear thread references
            self._aura_thread = None
            self._emotion_thread = None
            self._regressor_thread = None
            self._screen_recording_thread = None
            self._start_time = None

            # Close all writers
            writers = [self._aura_writer, self._emotion_writer, 
                      self._gaze_writer, self._pointer_writer]
            for writer in writers:
                if writer:
                    try:
                        writer.close_file()
                    except Exception as e:
                        print(f"Error closing writer: {e}")

            # Clear writer references
            self._aura_writer = None
            self._emotion_writer = None
            self._gaze_writer = None
            self._pointer_writer = None

            # Update signal statuses
            signals = [
                (self._run_aura, SIGNAL_AURA, 'ready'),
                (self._run_gaze, SIGNAL_GAZE, 'need_calibration'),
                (self._run_emotion, SIGNAL_EMOTION, 'ready'),
                (self._run_pointer, SIGNAL_POINTER, 'ready'),
                (self._run_screen, SIGNAL_SCREEN, 'ready'),
                (self._run_keyboard, SIGNAL_KEYBOARD, 'ready'),
                (self._screen_recorder, SIGNAL_SCREEN, 'ready')
            ]
            
            for is_active, signal, status in signals:
                if is_active:
                    self.send_signal_update(signal, status)
            
            # Post-process data at the very end
            self._post_process_eye_gaze()

            return {"status": STATUS_SUCCESS, "message": COLLECTION_STOPPED_MSG}
        except Exception as e:
            print(f"Error in stop_data_collection: {e}")
            return {"status": STATUS_ERROR, "message": str(e)}
        finally:
            # Ensure screen recorder is cleaned up even if an error occurs
            self._screen_recorder = None

    def stop_training_data_collection(self):
        """Stop recording training data."""
        try:
            self._training_data_collection_active = False
            
            # Clean up training-specific resources
            if hasattr(self, '_aura_training_thread') and self._aura_training_thread:
                self._aura_training_thread.join(timeout=1.0)
                self._aura_training_thread = None
            
            self.start_regressor()
            
            # Send both the signal update and calibration complete message
            self.send_signal_update(SIGNAL_GAZE, 'ready')
            
            # Send explicit calibration complete message
            self._socket.send_json({
                "type": "calibration_status",
                "message": CALIBRATION_COMPLETE_MSG
            })
            
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
        if status == True and signal == SIGNAL_GAZE:
            self.send_signal_update(signal, 'need_calibration')
        elif status == True:
            self.send_signal_update(signal, 'ready')
        else:
            self.send_signal_update(signal, 'inactive')
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
                self.send_signal_update(SIGNAL_AURA, 'connecting')
                try:
                    if self._aura_stream_id is None:
                        stream_ids = resolve_aura()
                        if len(stream_ids) == 0:
                            return {"status": STATUS_ERROR, "message": "No aura stream found"}
                        self._aura_stream_id = stream_ids[0]
                        
                    self._stream = Stream(bufsize=buffer_size_multiplier, source_id=self._aura_stream_id)
                    self._stream.connect(processing_flags='all')
                    rename_aura_channels(self._stream)
                    self.send_signal_update(SIGNAL_AURA, 'active')
                except ValueError as e:
                    self.send_signal_update(SIGNAL_AURA, 'error')
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
        """Initialize and start emotion recognition."""
        try:
            if self._camera_manager.register_user('emotion'):
                self._emotion_handler = EmotionRecognizer('opencv')
                self._emotion_thread = threading.Thread(
                    target=self._emotion_collection_loop, 
                    daemon=True
                )
                self.send_signal_update(SIGNAL_EMOTION, 'recording')
                return {"status": STATUS_SUCCESS, "message": "Emotion recognition started"}
            else:
                raise Exception("Failed to initialize camera")
        except Exception as e:
            self._camera_manager.unregister_user('emotion')
            self.send_signal_update(SIGNAL_EMOTION, 'error')
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
            self._add_thread(threading.current_thread())
            aura_writer_training = None
            if collection_type == TRAINING_MODE:
                channels_names = ['timestamp'] + self._stream.info['ch_names']
                self._aura_training_file = os.path.join(self._training_path, TRAINING_AURA_FILE)
                aura_writer_training = AuraDataWriter(self._training_path, TRAINING_AURA_FILE, channels_names)
                aura_writer_training.create_new_file()
            self.send_signal_update(SIGNAL_AURA, 'recording')
            
            while not self._shutdown:
                if is_stream_ready(self._stream):
                    data, ts = self._stream.get_data()
                    if collection_type == TRAINING_MODE:
                        if aura_writer_training:
                            aura_writer_training.write_data(ts, data)
                        if not self._training_data_collection_active:
                            break
                    else:
                        processed_ts = [round(t - self._start_time, 3) for t in ts]
                        self._aura_writer.write_data(processed_ts, data)
                        if not self._data_collection_active:
                            break
                time.sleep(0.001)
            
            self.send_signal_update(SIGNAL_AURA, 'ready')
        except Exception as e:
            print(f"Error in aura collection loop: {str(e)}")
            self.send_signal_update(SIGNAL_AURA, 'error')
            raise
        finally:
            if aura_writer_training:
                aura_writer_training.close_file()
            if self._aura_writer:
                self._aura_writer.close_file()
            self._remove_thread(threading.current_thread())

    def _emotion_collection_loop(self):
        """Continuously collect and write emotion data in a loop."""
        try:
            self._add_thread(threading.current_thread())
            self.send_signal_update(SIGNAL_EMOTION, 'recording')
            while not self._shutdown and self._data_collection_active:
                if self._emotion_handler and self._emotion_camera:
                    _, frame = self._emotion_camera.read()
                    if frame is not None:
                        # Create a copy of the frame to avoid memory sharing
                        frame_copy = frame.copy()
                        try:
                            emotion = self._emotion_handler.recognize_emotion(frame_copy)
                            if emotion is not None:
                                with threading.Lock():
                                    self._last_emotion = emotion
                                emotion = emotion[0]['dominant_emotion']
                                timestamp = round(time.time() - self._start_time, 3)
                                self._emotion_writer.write_data(timestamp, emotion)
                        finally:
                            # Ensure frame is released
                            del frame_copy
                time.sleep(0.033)  # ~30 FPS
        finally:
            if self._emotion_writer:
                self._emotion_writer.close_file()
            if self._emotion_camera:
                self._emotion_camera.release()
                self._emotion_camera = None
            if self._emotion_handler:
                self._emotion_handler.stop_processing()
                self._emotion_handler = None
            self.send_signal_update(SIGNAL_EMOTION, 'ready')
            self._remove_thread(threading.current_thread())

    def _coordinate_regressor_loop(self):
        """Continuously collect eye gaze data and predict screen coordinates."""
        try:
            self._add_thread(threading.current_thread())
            self.send_signal_update(SIGNAL_GAZE, 'recording')
            while not self._shutdown and self._data_collection_active:
                frame = self._camera_manager.get_frame()
                if frame is not None:
                    frame_copy = frame.copy()
                    try:
                        gaze_vector = self._eye_gaze.get_gaze_vector(frame_copy)
                        if gaze_vector[2] is not None:
                            with threading.Lock():
                                if self._last_gaze_frame is not None:
                                    del self._last_gaze_frame
                                self._last_gaze_frame = gaze_vector[2].copy()
                            left_eye = gaze_vector[0]
                            right_eye = gaze_vector[1] 
                            if left_eye is not None and right_eye is not None:
                                gaze_input = [[
                                    *left_eye,
                                    *right_eye
                                ]]
                                predicted_coords = self._regressor.make_prediction(gaze_input)
                                x, y = predicted_coords[0]
                                x = int(x)
                                y = int(y)
                                timestamp = round(time.time() - self._start_time, 3)
                                self._gaze_writer.write(timestamp, [x, y])
                    finally:
                        del frame_copy
                time.sleep(0.033)
        finally:
            self._eye_gaze_running = False
            self._camera_manager.unregister_user('eye_gaze')
            self.send_signal_update(SIGNAL_GAZE, 'need_calibration')
            if self._last_gaze_frame is not None:
                del self._last_gaze_frame
                self._last_gaze_frame = None
            self._remove_thread(threading.current_thread())

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
        """Open or close the camera."""
        try:
            if action == 'open':
                if self._camera is None or not self._camera.isOpened():
                    self._camera = cv2.VideoCapture(DEFAULT_CAMERA_INDEX)
                    if not self._camera.isOpened():
                        raise Exception("Could not open camera")
                    return {"status": STATUS_SUCCESS, "message": "Camera opened successfully"}
            elif action == 'close':
                if self._camera is not None:
                    self._camera.release()
                    self._camera = None
                    cv2.destroyAllWindows()
                    return {"status": STATUS_SUCCESS, "message": "Camera closed successfully"}
            else:
                return {"status": STATUS_ERROR, "message": f"Invalid action: {action}"}
                
        except Exception as e:
            if self._camera is not None:
                self._camera.release()
                self._camera = None
                cv2.destroyAllWindows()
            return {"status": STATUS_ERROR, "message": str(e)}

    def get_frame(self):
        """Get the latest frame from the camera manager."""
        return self._camera_manager.get_frame()

    def view_camera(self):
        """Capture frames from the camera and stream them to the frontend via ZMQ."""
        if self._camera is None or not self._camera.isOpened():
            result = self.manage_camera(OPEN_CAMERA)
            if result["status"] == STATUS_ERROR:
                return result

        def stream_frames():
            try:
                self._add_thread(threading.current_thread())
                print("Starting camera stream...")
                while self._viewing_camera and self._camera and self._camera.isOpened():
                    try:
                        # Get and process camera frame
                        ret, frame = self._camera.read()
                        if not ret or frame is None:
                            print("Failed to capture frame")
                            continue

                        # Process camera frame
                        frame = cv2.resize(frame, (640, 480))
                        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        if ret:
                            frame_data = base64.b64encode(buffer).decode('utf-8')
                            self._socket.send_json({
                                'type': 'frame',
                                'data': frame_data
                            })

                        # Process gaze frame if available
                        gaze_frame = None
                        if hasattr(self, '_last_gaze_frame') and self._last_gaze_frame is not None:
                            with threading.Lock():
                                if self._last_gaze_frame is not None:
                                    gaze_frame = self._last_gaze_frame.copy()
                        
                        if gaze_frame is not None:
                            gaze_frame = cv2.resize(gaze_frame, (640, 480))
                            ret_gaze, buffer_gaze = cv2.imencode('.jpg', gaze_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                            if ret_gaze:
                                gaze_data = base64.b64encode(buffer_gaze).decode('utf-8')
                                self._socket.send_json({
                                    'type': 'gaze_frame',
                                    'data': gaze_data
                                })
                            del gaze_frame
                        
                        time.sleep(0.033)
                        
                    except Exception as e:
                        print(f"Error processing frame: {e}")
                        time.sleep(0.1)
            except Exception as e:
                print(f"Fatal error in stream_frames: {e}")
            finally:
                self._viewing_camera = False
                print("Camera streaming stopped")
                self._remove_thread(threading.current_thread())

        if not self._viewing_camera:
            self._viewing_camera = True
            thread = threading.Thread(target=stream_frames, daemon=True)
            thread.start()
            return {"status": STATUS_SUCCESS, "message": "Camera streaming started"}
        else:
            return {"status": STATUS_ERROR, "message": "Camera is already streaming"}

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
            # Add debug logging
            return {
                "type": "stream_list",  # Add message type
                "status": "success",
                "streams": streams if streams else []  # Ensure we always return a list
            }
        except Exception as e:
            print(f"Error getting AURA streams: {e}")
            return {
                "type": "stream_list",
                "status": "error",
                "message": str(e),
                "streams": []
            }
    
    def set_aura_stream(self, stream_id):
        """
        Set the AURA stream.
        """
        self._aura_stream_id = stream_id
    
    def send_signal_update(self, signal, status):
        """
        Send a signal update message to the frontend.
        """
        try:
            if hasattr(self, '_socket') and self._socket and not self._socket.closed:
                # Add debug logging
                print(f"Backend sending signal update: signal={signal}, status={status}")
                message = {
                    "type": "signal_update", 
                    "signal": signal, 
                    "status": status
                }
                print(f"Sending message: {message}")
                self._socket.send_json(message)
        except Exception as e:
            print(f"Error sending signal update: {str(e)}")

    def start_keyboard_tracking(self):
        """Initialize and start keyboard tracking."""
        if not hasattr(self, '_keyboard_tracker') or self._keyboard_tracker is None:
            self._keyboard_tracker = KeyboardTracker(writer=self._keyboard_writer)
            return {"status": STATUS_SUCCESS, "message": "Keyboard tracking started"}
        else:
            return {"status": STATUS_ERROR, "message": "Keyboard tracking already active"}
    
    def start_screen_recording(self):
        """Initialize and start screen recording."""
        try:
            # Create output directory if it doesn't exist
            if not os.path.exists(self._path):
                os.makedirs(self._path)
                
            # Store the output file path
            self._screen_recording_file = os.path.join(self._path, f"{self._filename}{SCREEN_FILE_SUFFIX}")
            
            # Initialize recorder with default settings
            self._screen_recorder = ScreenRecorder(
                output_path=os.path.join(self._path, ''),  # Ensure path ends with separator
                filename=f"{self._filename}{SCREEN_FILE_SUFFIX}"
            )
            
            success = self._screen_recorder.start_recording(fps=30)
            if not success:
                self.send_signal_update(SIGNAL_SCREEN, 'error')
                return {"status": STATUS_ERROR, "message": "Failed to start screen recording"}
            
            self.send_signal_update(SIGNAL_SCREEN, 'recording')    
            return {"status": STATUS_SUCCESS, "message": "Screen recording started"}
            
        except Exception as e:
            self.send_signal_update(SIGNAL_SCREEN, 'error')
            return {"status": STATUS_ERROR, "message": str(e)}
    
    def stop_screen_recording(self):
        """Stop screen recording."""
        try:
            if not hasattr(self, '_screen_recorder') or self._screen_recorder is None:
                self.send_signal_update(SIGNAL_SCREEN, 'error')
                return {"status": STATUS_ERROR, "message": "No active screen recording found"}
            
            if self._screen_recorder:
                success = self._screen_recorder.stop_recording()
                if not success:
                    self.send_signal_update(SIGNAL_SCREEN, 'error')
                    return {"status": STATUS_ERROR, "message": "Failed to stop screen recording"}
                
                # Properly cleanup the screen recorder
                self._screen_recorder = None
                    
            self.send_signal_update(SIGNAL_SCREEN, 'ready')
            return {"status": STATUS_SUCCESS, "message": "Screen recording stopped"}
            
        except Exception as e:
            print(f"Error stopping screen recording: {e}")
            self.send_signal_update(SIGNAL_SCREEN, 'error')
            return {"status": STATUS_ERROR, "message": str(e)}
        finally:
            # Ensure screen recorder is cleaned up even if an error occurs
            self._screen_recorder = None
