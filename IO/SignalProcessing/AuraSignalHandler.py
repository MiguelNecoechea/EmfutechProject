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
                self.rename_aura_channels()
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

    def get_data_from_stream(self):
        """
        Gets the data from a stream object, this function only gets data when the stream has full new data.
        :return: None if the stream is closed or does not exist or has not being filled with fresh data, returns a tuple when
                 a pack of fresh data is available. When the stream is not valid returns a tuple of negative ones
        """
        data_to_return = (None, None)

        if self.__stream is None:
            data_to_return = (-1, -1)
        else:
            if self.is_stream_ready():
                data = self.__stream.get_data()
                data_to_return = data
        return data_to_return

    def add_filter(self, low_pass=1.0, high_pass=1.0, picks='eeg'):
        """
        Adds a filter to the stream.
        :param low_pass: A float representing the low pass filter.
        :param high_pass: A float representing the high pass filter.
        :param picks: The channel where the filter will be applied.
        :return:
        """
        if self.__stream is None:
            raise RuntimeError("Stream does not exist.")

        self.__stream.filter(low_pass, high_pass, picks)

    def rename_aura_channels(self) -> bool:
        """
        Rename the aura channels to the standard name of the electrodes that are being used
        This is supposed to take the stream with 8 channels. However it is also capable of renaming the other channels.
        :return: True if the operation is successful. False otherwise.
        """
        named_changed = False
        if self.__stream is not None:
            if self.__stream.info['nchan'] == 8:
                aura_channels = {
                    '0': 'F3',
                    '1': 'F4',
                    '2': 'Cz',
                    '3': 'C3',
                    '4': 'Pz',
                    '5': 'C4',
                    '6': 'P3',
                    '7': 'P4'
                   }
            elif self.__stream.info['nchan'] == 40:
                aura_channels = self.__rename_40_channels()
            else:
                self.disconnect_stream()
                del self.__stream
                raise RuntimeError("The stream is not supported")

            self.__stream.rename_channels(aura_channels)
            named_changed = True

        return named_changed

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

    def __rename_40_channels(self):
        waves = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
        channels = ['F3', 'F4', 'Cz', 'C3', 'C4', 'Pz', 'P3', 'P4']
        current_position = 0
        mapping = {}
        for wave in waves:
            for channel in channels:
                mapping[str(current_position)] = wave +'_' + channel
                current_position += 1
        return mapping