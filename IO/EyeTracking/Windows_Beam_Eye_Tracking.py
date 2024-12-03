"""
Copyright (c) 2021 Eyeware Tech SA http://www.eyeware.tech

This file provides an example on how to receive head and eye tracking data
from Beam SDK using an Object-Oriented approach.

Dependencies:
- Python 3.6
- NumPy
- pyzmq
"""
from typing import Optional, Tuple
import sys
import time
import zmq
import json
import numpy as np
import os
from pathlib import Path

# Add the parent directory of the API folder to sys.path
api_path = Path(__file__).parent.parent.parent
sys.path.append(str(api_path))

try:
    from API.python.eyeware.client import TrackerClient
except ImportError as e:
    print(f"Error importing TrackerClient: {e}")
    print(f"Current sys.path: {sys.path}")
    print(f"Looking for API at: {api_path}")
    raise

class EyeTracker:
    """Class to handle eye tracking functionality using Beam SDK."""
    
    def __init__(self, host: str = None, port: int = None):
        """
        Initialize the eye tracker.
        
        Args:
            host (str, optional): Server hostname. Defaults to None.
            port (int, optional): Server port. Defaults to None.
        """
        try:
            # Initialize ZMQ context and socket for communication with main backend
            print("Initializing ZMQ context and socket for communication with main backend")
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.PAIR)
            self.socket.connect("tcp://localhost:5557")  # Connect to main backend

            self.tracker = TrackerClient(host, port) if (host or port) else TrackerClient()
            self.running = False
            self.update_rate = 30  # Hz
        except Exception as e:
            print(f"Failed to initialize TrackerClient: {str(e)}")
            raise ConnectionError(f"Failed to initialize TrackerClient: {str(e)}")

    def get_gaze_coordinates(self) -> Optional[Tuple[float, float]]:
        """
        Get the current gaze coordinates.
        
        Returns:
            Optional[Tuple[float, float]]: (x, y) coordinates in pixels, or None if tracking is lost
        """
        if not self.tracker.connected:
            return None
            
        screen_gaze = self.tracker.get_screen_gaze_info()
        
        if screen_gaze.is_lost:
            return None
            
        return (screen_gaze.x, screen_gaze.y)

    def start_tracking(self):
        """Start the eye tracking loop."""
        self.running = True
        
        try:
            while self.running:
                if self.tracker.connected:
                    coordinates = self.get_gaze_coordinates()
                    if coordinates:
                        x, y = coordinates
                        # Send coordinates to main backend
                        message = {
                            "type": "gaze_coordinates",
                            "data": {"x": x, "y": y}
                        }
                        print(f"x: {x}, y: {y}")
                        self.socket.send_json(message)
                    time.sleep(1 / self.update_rate)
                else:
                    self._handle_disconnection()
                    
                # Check for messages from main backend
                try:
                    message = self.socket.recv_json(flags=zmq.NOBLOCK)
                    self._handle_message(message)
                except zmq.error.Again:
                    pass  # No message available
                    
        except KeyboardInterrupt:
            print("\nEye tracking stopped by user")
        except Exception as e:
            print(f"Error during tracking: {str(e)}")
        finally:
            self.stop_tracking()

    def stop_tracking(self):
        """Stop the eye tracking loop."""
        self.running = False
        self.socket.close()
        self.context.term()

    def _handle_disconnection(self):
        """Handle tracker server disconnection."""
        MESSAGE_PERIOD = 2  # seconds
        time.sleep(MESSAGE_PERIOD - time.monotonic() % MESSAGE_PERIOD)
        message = {
            "type": "connection_status",
            "status": "disconnected"
        }
        self.socket.send_json(message)

    def _handle_message(self, message):
        """Handle messages from main backend."""
        if message.get("command") == "stop":
            self.stop_tracking()


def main():
    """Main function to run the eye tracker."""
    try:
        tracker = EyeTracker()
        tracker.start_tracking()
    except ConnectionError as e:
        print(f"Failed to initialize eye tracker: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
