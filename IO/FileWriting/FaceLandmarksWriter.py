from IO.FileWriting.Writer import Writer

class FaceLandmarksWriter(Writer):
    # Selected landmarks for gestures
    SELECTED_LANDMARKS = [
        10, 67, 213, 169, 152, 365, 433, 454, 297, 234,  # Face contour
        107, 105, 70, 336, 334, 301,  # Eyebrows
        33, 133, 362, 263, 159, 145, 386, 374,  # Eyes
        1, 6, 5, 220, 440,  # Nose
        0, 14, 96, 308  # Mouth
    ]

    def __init__(self, file_path, file_name):
        """
        Initializes the FaceLandmarksWriter object with the file path and file name.
        
        :param file_path: The path where the file will be saved.
        :param file_name: The name of the file to store the data.
        """
        # Create header with timestamp and x,y coordinates for each landmark
        header = ["timestamp"] + [f"landmark_{i}_x" for i in self.SELECTED_LANDMARKS] + \
                [f"landmark_{i}_y" for i in self.SELECTED_LANDMARKS]
        super().__init__(file_path, file_name, header)

    def write(self, timestamp, landmarks):
        """
        Writes the facial landmark data to the file.
        
        :param timestamp: The timestamp of the landmark detection
        :param landmarks: MediaPipe face landmarks object
        """
        if not self._is_writer_opened:
            self.create_new_file()

        if landmarks is None:
            raise ValueError("Landmarks cannot be None")

        # Extract x and y coordinates for each selected landmark
        row = [round(timestamp, 3)]
        for idx in self.SELECTED_LANDMARKS:
            x = landmarks.landmark[idx].x
            y = landmarks.landmark[idx].y
            row.extend([x, y])

        self._csv_writer.writerow(row)
        self._csv_file.flush()
        