import os
import csv


class Writer:
    def __init__(self, output_path, file_name, initial_line):
        """
        Creates a writer object for the specified location and file.
        :param output_path: the folder where the data is going to be written.
        :param file_name: the name of the file to be written.
        :param initial_line: the initial line to be written containing the name of the data channels.
        """
        self.__INITIAL_LINE = initial_line
        self._path = os.path.join(output_path, file_name)
        self._is_writer_opened = False
        self._csv_file = None
        self._csv_writer = None

    def create_new_file(self):
        """
        Creates a new file and file writer, it also writes the name of each of the channels passed by the initial line,
        """
        self._csv_file = open(self._path, 'w')
        self._csv_writer = csv.writer(self._csv_file)
        self._is_writer_opened = True
        self._csv_writer.writerow(self.__INITIAL_LINE)

    def open_existing_file(self):
        """
        Opens a file in append mode so previous stored data is preserved.
        """
        self._csv_file = open(self._path, 'a')
        self._csv_writer = csv.writer(self._csv_file)
        self._is_writer_opened = True

    def close_file(self):
        """
        Closes the file and disables the writer.
        """
        if self._is_writer_opened:
            self._csv_file.close()
            self._is_writer_opened = False

