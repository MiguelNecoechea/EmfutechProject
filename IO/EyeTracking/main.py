from LaserGaze.GazeProcessor import GazeProcessor
from LaserGaze.VisualizationOptions import VisualizationOptions
import cv2
vo = VisualizationOptions()
laser_gaze = GazeProcessor(visualization_options=vo)
laser_gaze.start()

while True:
    data = laser_gaze.get_gaze_vector()
    if data is not None:
        frame = data[-1]
        print("left: ", data[0], " right: ",data[1])
        cv2.imshow('LaserGaze', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

laser_gaze.stop_processing()