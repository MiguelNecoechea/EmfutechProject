import numpy as np

from IO.FileWriting.Writer import Writer


class AuraDataWriter(Writer):
    def __init__(self, output_path, file_name):
        """
        Creates a writer object for the specified for handling 8 channel aura signals.
        :param output_path: the folder where the data is going to be written.
        :param file_name: the name of the file to be written.
        """
        super().__init__(output_path, file_name, ['Time and date', 'F3', 'F4', 'Cz', 'C3',
                                                  'Pz', 'C4', 'P3', 'P4'])

    def write_data(self, timestamp, data) -> bool:
        """
        Processes the data if it comes in an incorrect format and writes it to the csv file.
        :param timestamp: The timestamp of the data in form of array
        :param data: The matrix of data containing reading from all the channels.
        :exception: A ValueError if the data cannot be matched.
        :return: True if the data was written, False otherwise.
        """
        written = False
        if self._is_writer_opened:
            if len(timestamp) != len(data):
                data = np.transpose(data)
                if len(timestamp) != len(data):
                    raise ValueError('Length of timestamp and data cannot be matched. Hint: the data might be reversed.'
                                     'Expected input format [timestamp, data]')
            for i in range(len(data)):
                if self._is_writer_opened:
                    self._csv_writer.writerow(np.append(timestamp[i], data[i]))
            written = True

        return written
