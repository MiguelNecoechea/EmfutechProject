# -----------------------------------------------------------------------------------
# Company: TensorSense
# Project: LaserGaze
# File: GazeProcessor.py
# Description: This class processes video input to detect facial landmarks and estimate
#              gaze vectors using MediaPipe. The gaze estimation results are asynchronously
#              output via a callback function. This class leverages advanced facial
#              recognition and affine transformation to map detected landmarks into a
#              3D model space, enabling precise gaze vector calculation.
# Author: Sergey Kuldin
# -----------------------------------------------------------------------------------
import mediapipe as mp
import cv2
import os
import time
import numpy as np
from .landmarks import *
from .face_model import *
from .AffineTransformer import AffineTransformer
from .EyeballDetector import EyeballDetector

class GazeProcessor:
    """
    Processes video input to detect facial landmarks and estimate gaze vectors using the MediaPipe library.
    Outputs gaze vector estimates asynchronously via a provided callback function.
    """

    def __init__(self, camera_idx=0, visualization_options=None):
        """
        Initializes the gaze processor with optional camera settings and visualization configurations.
        Args:
        - camera_idx (int): Index of the camera to be used for video capture.
        - visualization_options (object): Options for visual feedback on the video frame.
        """
        self.__camera_idx = camera_idx
        self.__vis_options = visualization_options
        self.__left_detector = EyeballDetector(DEFAULT_LEFT_EYE_CENTER_MODEL)
        self.__right_detector = EyeballDetector(DEFAULT_RIGHT_EYE_CENTER_MODEL)
        self._running = False
        self.__cap = None
        self.__landmarker = None

        model_path = os.path.join(os.path.dirname(__file__), 'face_landmarker.task')
        BaseOptions = mp.tasks.BaseOptions
        self.FaceLandmarker = mp.tasks.vision.FaceLandmarker
        FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode
        self.options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.VIDEO
        )

    @property
    def is_running(self):
        """
        Returns the current state of the gaze processor.
        :return: True if the gaze processor is running, False otherwise.
        """
        return self._running

    def start(self):
        """
        Starts the video processing loop to detect facial landmarks and calculate gaze vectors.
        Continuously updates the video display and invokes callback with gaze data.
        """
        print("Inicializando cámara para Eye Tracking...")
        self.__cap = cv2.VideoCapture(self.__camera_idx)
        if not self.__cap.isOpened():
            print("Error al abrir la cámara. Verifique que la cámara esté conectada y reinicie la aplicación.")
            return
        self.__landmarker = self.FaceLandmarker.create_from_options(self.options)
        self._running = True
        print("Cámara inicializada correctamente.")

    def get_gaze_vector(self):
        """
        Detects the facial landmarks and estimate gaze vectors using the MediaPipe library and components from the laser
        gaze module.
        :return: A tuple of None if the data is being calibrated, otherwise a tuple of vectors containing the gaze info.
        """
        if not self._running:
            raise RuntimeError("Gaze processor is not started, start() must be called first.")

        success, frame = self.__cap.read()
        if not success:
            return None, None, frame

        timestamp_ms = int(time.time() * 1000)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

        face_landmarker_result = self.__landmarker.detect_for_video(mp_image, timestamp_ms)

        if face_landmarker_result.face_landmarks:
            lms_s = np.array([[lm.x, lm.y, lm.z] for lm in face_landmarker_result.face_landmarks[0]])
            lms_2 = (lms_s[:, :2] * [frame.shape[1], frame.shape[0]]).round().astype(int)

            mp_hor_pts = [lms_s[i] for i in OUTER_HEAD_POINTS]
            mp_ver_pts = [lms_s[i] for i in [NOSE_BRIDGE, NOSE_TIP]]
            model_hor_pts = OUTER_HEAD_POINTS_MODEL
            model_ver_pts = [NOSE_BRIDGE_MODEL, NOSE_TIP_MODEL]

            at = AffineTransformer(lms_s[BASE_LANDMARKS, :], BASE_FACE_MODEL, mp_hor_pts, mp_ver_pts,
                                   model_hor_pts, model_ver_pts)

            indices_for_left_eye_center_detection = LEFT_IRIS + ADJACENT_LEFT_EYELID_PART
            left_eye_iris_points = lms_s[indices_for_left_eye_center_detection]
            left_eye_iris_points_in_model_space = [at.to_m2(mpp) for mpp in left_eye_iris_points]
            self.__left_detector.update(left_eye_iris_points_in_model_space, timestamp_ms)

            indices_for_right_eye_center_detection = RIGHT_IRIS + ADJACENT_RIGHT_EYELID_PART
            right_eye_iris_points = lms_s[indices_for_right_eye_center_detection]
            right_eye_iris_points_in_model_space = [at.to_m2(mpp) for mpp in right_eye_iris_points]
            self.__right_detector.update(right_eye_iris_points_in_model_space, timestamp_ms)

            left_gaze_vector, right_gaze_vector = None, None

            if self.__left_detector.center_detected:
                left_eyeball_center = at.to_m1(self.__left_detector.eye_center)
                left_pupil = lms_s[LEFT_PUPIL]
                left_gaze_vector = left_pupil - left_eyeball_center

            if self.__right_detector.center_detected:
                right_eyeball_center = at.to_m1(self.__right_detector.eye_center)
                right_pupil = lms_s[RIGHT_PUPIL]
                right_gaze_vector = right_pupil - right_eyeball_center

            return left_gaze_vector, right_gaze_vector, frame
        return None, None, frame

    def stop_processing(self):
        """
        Releases the webcam from the current experiment.
        """
        if self.__cap:
            self.__cap.release()
        self._running = False

