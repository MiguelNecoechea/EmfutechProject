from IO.FileWriting.Writer import Writer

class PointerWriter(Writer):
    def __init__(self, file_path, file_name):
        """
        Initializes the PointerWriter object with the file path and file name.
        
        :param file_path: The path where the file will be saved.
        :param file_name: The name of the file to store the data.
        """
        super().__init__(file_path, file_name, ['timestamp', 'x', 'y', 'clicked'])

    def write(self, timestamp, x, y, clicked=False):
        """
        Writes the pointer coordinates and click state to the file.
        
        :param timestamp: The timestamp of the pointer position
        :param x: The x-coordinate of the pointer
        :param y: The y-coordinate of the pointer
        :param clicked: Boolean indicating if mouse is clicked
        """
        if not self._is_writer_opened:
            self.create_new_file()

        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise ValueError("Both x and y coordinates must be numeric values.")

        self._csv_writer.writerow([round(timestamp, 3), x, y, int(clicked)])
        self._csv_file.flush()
