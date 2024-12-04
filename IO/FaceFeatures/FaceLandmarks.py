import cv2
import mediapipe as mp
import time

class FaceLandmarksDetector:
    # Selected landmark indices based on the uploaded image
    SELECTED_LANDMARKS = [
        # Face contour
        10, 67, 213, 169, 152, 365, 433, 454, 297, 234,
        # Eyebrows
        107, 105, 70, 336, 334, 301,
        # Eyes
        33, 133, 362, 263, 159, 145, 386, 374,
        # Nose
        1, 6, 5, 220, 440,
        # Mouth
        0, 14, 96, 308
    ]

    def __init__(self):
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils

    def process_frame(self, frame):
        """
        Process a single frame and detect face landmarks.
        
        Args:
            frame: BGR image frame from OpenCV
            
        Returns:
            frame: The processed frame with landmarks drawn
        """
        # Convert the image to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame with MediaPipe
        results = self.face_mesh.process(rgb_frame)

        # Draw selected face landmarks if detected
        row = []
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                for idx in self.SELECTED_LANDMARKS:
                    x = int(face_landmarks.landmark[idx].x * frame.shape[1])
                    y = int(face_landmarks.landmark[idx].y * frame.shape[0])
                    csv_x = face_landmarks.landmark[idx].x
                    csv_y = face_landmarks.landmark[idx].y
                    row.extend([csv_x, csv_y])
                    cv2.circle(frame, (x, y), 2, (255, 255, 255), -1)

        return frame, row

    def __del__(self):
        """Cleanup when the object is destroyed"""
        self.face_mesh.close()
