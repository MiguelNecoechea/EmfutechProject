from IO.FileWriting.Writer import Writer

class PointerWriter(Writer):
    def __init__(self, file_path, file_name):
        """
        Initializes the PointerWriter object with the file path and file name.
        
        :param file_path: The path where the file will be saved.
        :param file_name: The name of the file to store the data.
        """
        super().__init__(file_path, file_name, ['timestamp', 'x', 'y'])

    def write(self, timestamp, x, y):
        """
        Writes the pointer coordinates to the file. The data must consist of two elements: x and y coordinates.
        
        :param x: The x-coordinate of the pointer.
        :param y: The y-coordinate of the pointer.
        :raises ValueError: If the data does not contain exactly two elements.
        """
        if not self._is_writer_opened:
            self.create_new_file()

        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise ValueError("Both x and y coordinates must be numeric values.")

        self._csv_writer.writerow([timestamp] + [x, y])
        self._csv_file.flush()
