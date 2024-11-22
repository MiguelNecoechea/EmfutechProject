from IO.FileWriting.Writer import Writer

class KeyboardWriter(Writer):
    def __init__(self, file_path, file_name):
        """
        Initializes the KeyboardWriter object with the file path and file name.
        
        :param file_path: The path where the file will be saved.
        :param file_name: The name of the file to store the data.
        """
        super().__init__(file_path, file_name, ['timestamp', 'key', 'is_pressed'])

    def write(self, timestamp, key, is_pressed):
        """
        Writes the keyboard event data to the file.
        
        :param timestamp: The timestamp of the key event
        :param key: The key that was pressed/released
        :param is_pressed: Boolean indicating if key is pressed
        """
        if not self._is_writer_opened:
            self.create_new_file()

        if not isinstance(timestamp, (int, float)):
            raise ValueError("Timestamp must be a numeric value.")

        self._csv_writer.writerow([round(timestamp, 3), str(key), int(is_pressed)])
        self._csv_file.flush() 