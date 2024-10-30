from IO.FileWriting.Writer import Writer

class GazeWriter(Writer):
    def __init__(self, file_path, file_name):
        super().__init__(file_path, file_name, ['l_x', 'l_y', 'l_z', 'r_x', 'r_y', 'r_z', 'x', 'y'])

    def write(self, data, coordinates):
        """
        Writes the gaze data to the file.
        :param data: the gaze data to be written.
        :param coordinates: the coordinates of the gaze.
        """
        if not self._is_writer_opened:
            self.create_new_file()

        self._csv_writer.writerow(data + coordinates)
        self._csv_file.flush()
