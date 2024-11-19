from IO.FileWriting.Writer import Writer

class EmotionPredictedWriter(Writer):
    def __init__(self, output_path, file_name):
        """
        Creates a writer object for the specified that focuses on writing the emotion on each second of the experiment.
        :param output_path: the folder where the data is going to be written.
        :param file_name: the name of the file to be written.        """
        super().__init__(output_path, file_name, ['Time', 'Emotion Predicted'])

    def write_data(self, timestamp, data) -> bool:
        """
        Writes the time and the emotion predicted into a csv file.
        :param timestamp: The timestamp of the data in form of array
        :param data: The label containing the predicted emotion.
        :return: True if the data was written, False otherwise.
        """
        written = False
        if self._is_writer_opened and timestamp is not None and data is not None:
            self._csv_writer.writerow([round(timestamp, 3), data])
            written = True

        return written