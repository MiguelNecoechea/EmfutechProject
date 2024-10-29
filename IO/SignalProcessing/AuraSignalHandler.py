from mne_lsl.lsl import resolve_streams
from mne_lsl.lsl.stream_info import StreamInfo
from mne_lsl.stream import StreamLSL as Stream

class AuraLslStreamHandler:
    # Public functions

    def __init__(self, buffer_size_multiplier, stream_id=''):
        """
        Creates an LSL signal handler for AURA.
        :param buffer_size_multiplier: The multiplier for the buffer size.
        The formula is sampling_frequency_(Hz) * buffer_size_multiplier.
        it is important to consider that the buffer size is determined by the frequency,
        :param stream_id: The stream ID that will be handled.
        """
        self.__buffer_size_multiplier = buffer_size_multiplier
        self.__stream = None
        if stream_id != '':
            self.connect_stream(stream_id)

    # Getters

    def get_stream_info(self):
        if self.__stream is None:
            raise RuntimeError("Stream handler has not been initialized.")

        return self.__stream.info

    def get_stream_new_samples(self):
        """
        Return the number of new samples available in the stream.
        :return: None if the stream is not found, and Int containing the number of new samples available.
        """
        if self.__stream is None:
            raise RuntimeError("The stream is not created yet.")
        return self.__stream.n_new_samples

    def get_stream_frequency(self):
        """
        Return the sampling frequency of the stream.
        :return: None if the stream is not found, and Int containing the sampling frequency of the stream.
        """
        if self.__stream is None:
            raise RuntimeError("The stream is not created yet.")
        return self.__stream.info["sfreq"]


    @staticmethod
    def available_streams() -> list[StreamInfo]:
        """
        Shows the available streams to connect.
        :return: A list of StreamInfo objects.
        """
        return resolve_streams()

    def disconnect_stream(self):
        """
        Disconnects a specific stream and deletes the object from memory.
        """
        self.__stream.disconnect()
        del self.__stream

    def connect_stream(self, stream_id=''):
        """
        Connects a stream given the stream identifier.
        :param stream_id: The unique ID of the stream to be connected.
        """
        was_able_to_connect = True
        if self.__stream is None:
            try:
                self.__stream = Stream(bufsize=self.__buffer_size_multiplier, source_id=stream_id)
                self.__stream.connect(processing_flags='all')
            except RuntimeError:
                was_able_to_connect = False
        return was_able_to_connect

    def is_stream_ready(self) -> bool:
        """
        Check if the streams has enough data to process.
        :return: A boolean indicating whether the stream has enough data to process.
        """
        is_ready = False
        if self.__stream is None:
            raise RuntimeError("The stream is not created yet.")

        if (self.__stream.connected and
                self.__stream.n_new_samples >= self.__stream.n_buffer):
            is_ready = True

        return is_ready

    def remove_stream_filters(self):
        """
        Removes all previous applied filters to the stream.
        :return:
        """
        if self.__stream is None:
            raise RuntimeError("The stream is not created yet.")
        if len(self.__stream.filters) != 0:
            self.__stream.del_filter()

    def get_data_from_stream(self, picks=None):
        """
        Gets the data from a stream object, this function only gets data when the stream has full new data.
        :param picks: A list containing the names of the channels to be retrieve data from.
        :return: None if the stream is closed or does not exist or has not being filled with fresh data, returns a tuple when
                 a pack of fresh data is available. When the stream is not valid returns a tuple of negative ones
        """
        if self.__stream is None:
            raise RuntimeError("The stream is not created or connected yet.")

        return self.__stream.get_data(picks=picks)

    def clear_buffer(self):
        """
        Clears the buffer of the stream. This can be used if some anomalies occur with the data, given that it takes
        to build the object.
        :return:
        """
        if self.__stream is None:
            raise RuntimeError("The stream is not created yet.")
        self.__stream.get_data()

    def add_notch_filter(self, freq_hz=50):
        """
        Adds a notch filter to the stream.
        :param freq_hz: Specifies the frequency to filter out
        """
        if self.__stream is None:
            raise RuntimeError("The stream is not created yet.")
        self.__stream.notch_filter(freqs=freq_hz)
    def add_filter(self, low_pass=1.0, high_pass=1.0, picks=None):
        """
        Adds a filter to the stream.
        :param low_pass: A float representing the low pass filter.
        :param high_pass: A float representing the high pass filter.
        :param picks: The channel where the filter will be applied.
        :return:
        """
        if self.__stream is None:
            raise RuntimeError("Stream does not exist.")

        self.__stream.filter(low_pass, high_pass, picks=picks)

    def drop_channels(self, channels_to_drop:list[str]):
        """
        Tries to remove channels that will not be needed.
        :param channels_to_drop: The names of the channels to be removed.
        :return: A boolean indicating whether the channels were removed or not.
        """
        try:
            self.__stream.drop_channels(channels_to_drop)
            dropped = True
        except ValueError:
            dropped = False

        return dropped

    def __del__(self):
        """
        Removes and closes all possible open streams.
        """
        self.__delete_streams()

    # Private Functions
    def __delete_streams(self):
        """
        Deletes all connected streams in order to free memory resources.
        """
        if self.__stream is not None:
            self.__stream.disconnect()
            del self.__stream
