from IO.FileWriting.Writer import Writer

class GazeWriter(Writer):
    def __init__(self, file_path, file_name):
        """
        Initializes the GazeWriter object with the file path and file name.
        :param file_path: The path where the file will be saved.
        :param file_name: The name of the file to store the data.
        """
        super().__init__(file_path, file_name, ['l_x', 'l_y', 'l_z', 'r_x', 'r_y', 'r_z', 'x', 'y'])

    def write(self, data):
        """
        Writes the gaze data to the file. The data must be a list of 8 elements, where the first 6 elements are the gaze
        vectors of the left and right eyes, and the last 2 elements are the x and y coordinates of the gaze.
        :param data: the gaze data to be written.
        """
        if not self._is_writer_opened:
            self.create_new_file()

        if len(data) != 8:
            raise ValueError("The data must be a list of 8 elements.")

        self._csv_writer.writerow(data)
        self._csv_file.flush()
