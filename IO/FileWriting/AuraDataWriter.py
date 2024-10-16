import os
import csv
import numpy as np

class AuraDataWriter:
    def __init__(self, output_path, file_name):
        """
        Creates a writer object for the specified location and file.
        :param output_path: the folder where the data is going to be written.
        :param file_name: the name of the file to be written.
        """
        self.__path = os.path.join(output_path, file_name)
        self.__is_writer_opened = False
        self.__INITIAL_LINE = ['Time and date', 'F3', 'F4', 'Cz', 'C3', 'Pz', 'C4', 'P3', 'P4']
        self.__csv_file = None
        self.__csv_writer = None

    def create_new_file(self):
        """
        Creates a new file and file writer, it also writes the name of each of the channels,
        """
        self.__csv_file = open(self.__path, 'w')
        self.__csv_writer = csv.writer(self.__csv_file)
        self.__is_writer_opened = True
        self.__csv_writer.writerow(self.__INITIAL_LINE)

    def write_data(self, timestamp, data) -> bool:
        """
        Processes the data and writes it to the csv file.
        :param timestamp: The timestamp of the data in form of array
        :param data: The matrix of data containing reading from all the channels.
        :return: True if the data was written, False otherwise.
        """
        written = False
        if self.__is_writer_opened:
            if len(timestamp) != len(data):
                data = np.transpose(data)
                if len(timestamp) != len(data):
                    raise ValueError('Length of timestamp and data cannot be matched')
            else:
                for i in range(len(data)):
                    if self.__is_writer_opened:
                        self.__csv_writer.writerow(np.append(timestamp[i], data[i]))
                written = True

        return written

    def open_existing_file(self):
        """
        This opens a file in append mode so previous stored data is preserved.
        """
        self.__csv_file = open(self.__path, 'a')
        self.__csv_writer = csv.writer(self.__csv_file)
        self.__is_writer_opened = True

    def close_file(self):
        """
        Closes the file and disables the writer.
        """
        if self.__is_writer_opened:
            self.__csv_file.close()
            self.__is_writer_opened = False
