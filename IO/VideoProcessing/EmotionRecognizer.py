import cv2
from deepface import DeepFace

class EmotionRecognizer:
    __DEFAULT_CAMERA_INDEX = 0
    def __init__(self, backend_model, open_camera=True):
        """
        Creates the object that will hand the predictions of the emotion recognizer.
        :param backend_model: The backend to use to predict the emotion.
        """
        self.__face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.__backend_model = backend_model
        if open_camera:
            cv2.VideoCapture(self.__DEFAULT_CAMERA_INDEX)
            self.cap = cv2.VideoCapture(self.__DEFAULT_CAMERA_INDEX)


    # Public methods
    def recognize_emotion(self, frame=None):
        """
        Applies filters necessary to recognize the main face and the face emotion.
        :param frame: An image-like array containing the data.
        :return: A string with the emotion prediction.
        """
        if frame is None:
            _, frame = self.cap.read()
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)
        faces = self.__face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        result = None
        if len(faces) > 0:
            x = faces[0][0]
            y = faces[0][1]
            w = faces[0][2]
            h = faces[0][3]
            face_roi = rgb_frame[y:y + h, x:x + w]
            result = DeepFace.analyze(face_roi, actions=['emotion'], enforce_detection=False,
                                      detector_backend=self.__backend_model)
        return result
