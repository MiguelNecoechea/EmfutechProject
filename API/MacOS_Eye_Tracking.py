"""
Copyright (c) 2024

This is a simple eye tracking simulator for MacOS.
It is used to develop the new eye tracking backend. Special for windows.
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
import random

class EyeTracker:
    """Class to simulate eye tracking functionality for MacOS."""
    
    def __init__(self):
        """Initialize the eye tracker simulator."""
        try:
            # Initialize ZMQ context and socket for communication with main backend
            print("Initializing ZMQ context and socket for communication with main backend")
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.PAIR)
            self.socket.connect("tcp://localhost:5557")  # Connect to main backend

            self.running = False
            self.update_rate = 30  # Hz
            
            # Set screen dimensions for random coordinate generation
            self.screen_width = 1920  # Default screen width
            self.screen_height = 1080  # Default screen height
            
        except Exception as e:
            print(f"Failed to initialize EyeTracker: {str(e)}")
            raise ConnectionError(f"Failed to initialize EyeTracker: {str(e)}")

    def get_gaze_coordinates(self) -> Optional[Tuple[float, float]]:
        """
        Generate random gaze coordinates.
        
        Returns:
            Optional[Tuple[float, float]]: Random (x, y) coordinates in pixels
        """
        x = random.uniform(0, self.screen_width)
        y = random.uniform(0, self.screen_height)
        return (x, y)

    def start_tracking(self):
        """Start the eye tracking simulation loop."""
        self.running = True
        
        try:
            while self.running:
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
                else:
                    # Simulate disconnection/tracking loss
                    self._handle_disconnection()
                
                time.sleep(1 / self.update_rate)
                    
                # Check for messages from main backend
                try:
                    message = self.socket.recv_json(flags=zmq.NOBLOCK)
                    self._handle_message(message)
                except zmq.error.Again:
                    pass  # No message available
                    
        except KeyboardInterrupt:
            print("\nEye tracking simulation stopped by user")
        except Exception as e:
            print(f"Error during tracking simulation: {str(e)}")
        finally:
            self.stop_tracking()

    def stop_tracking(self):
        """Stop the eye tracking simulation loop."""
        self.running = False
        self.socket.close()
        self.context.term()

    def _handle_disconnection(self):
        """Handle simulated tracking loss."""
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
    """Main function to run the eye tracking simulator."""
    try:
        tracker = EyeTracker()
        tracker.start_tracking()
    except ConnectionError as e:
        print(f"Failed to initialize eye tracker simulator: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 