from LaserGaze.LaserGaze import LaserGaze
import cv2
laser_gaze = LaserGaze()
laser_gaze.start_camera_and_processor()

while True:
    data = laser_gaze.get_gaze_vector_and_frame()
    if data is not None:
        frame = data[-1]
        cv2.imshow('LaserGaze', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

laser_gaze.stop()