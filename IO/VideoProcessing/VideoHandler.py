import cv2
from attr import attributes


class VideoHandler:
    """
    A class dedicated to handle the camera video. The backend that is being used is OpenCV
    """
    def __init__(self):
        self.__video = cv2.VideoCapture(0)

    def open_camera(self):
        """
        If the camara is closed establish a connection to the default camara system.
        """
        if not self.__video.isOpened():
            self.__video = cv2.VideoCapture(0)

    def close_camera(self):
        """
        If the camera is open, it is disconnected allowing new connections.
        """
        if self.__video.isOpened():
            self.__video.release()

    def get_frame(self):
        """
        Gets the current frame from the video stream.
        :return: An array which is the image data.
        """
        frame = None
        if self.__video.isOpened():
            _, frame = self.__video.read()
        return frame

    def is_camera_open(self) -> bool:
        """
        Checks if the camera is open.
        :return: A boolean indicating if the camera is open.
        """
        return self.__video.isOpened()
