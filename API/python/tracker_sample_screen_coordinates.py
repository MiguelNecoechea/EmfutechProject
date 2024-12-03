"""
  Copyright (c) 2021 Eyeware Tech SA http://www.eyeware.tech

  This file provides an example on how to receive head and eye tracking data
  from Beam SDK.

  Dependencies:
  - Python 3.6
  - NumPy
"""
import sys
#sys.path.append('C:\\Users\\chpes\\Dropbox\\PythonScripts\\BeamSDK\\BeamSDK-Windows64-1.1.0\\API\\python\\eyeware')
#sys.path.append(r"C:\\Users\\chpes\\Dropbox\\PythonScripts\\BeamSDK\\BeamSDK-Windows64-1.1.0\\API\\python")
#print(sys.path)
from eyeware.client import TrackerClient
import time
import numpy as np

# Build tracker client, to establish a communication with the tracker server (an Eyeware application).
#
# Constructing the tracker client object without arguments sets a default server hostname and port which
# work fine in many configurations.
# However, it is possible to set a specific hostname and port, depending on your setup and network.
# See the TrackerClient API reference for further information.
tracker = TrackerClient()

# Run forever, until we press ctrl+c
print("  * Gaze on Screen:")

while True:
    # Make sure that the connection with the tracker server (Eyeware application) is up and running.

    if tracker.connected:
        screen_gaze = tracker.get_screen_gaze_info()
        screen_gaze_is_lost = screen_gaze.is_lost
#        print("      - Lost track:       ", screen_gaze_is_lost)
        if not screen_gaze_is_lost:
#            print("      - Screen ID:        ", screen_gaze.screen_id)
            print("      - Coordinates:       <x=%5.3f px,   y=%5.3f px>" % (screen_gaze.x, screen_gaze.y))
#            print("      - Confidence:       ", screen_gaze.confidence)

        time.sleep(1 / 30)  # We expect tracking data at 30 Hz
    else:
        # Print a message every MESSAGE_PERIOD_IN_SECONDS seconds
        MESSAGE_PERIOD_IN_SECONDS = 2
        time.sleep(MESSAGE_PERIOD_IN_SECONDS - time.monotonic() % MESSAGE_PERIOD_IN_SECONDS)
        print("No connection with tracker server")
