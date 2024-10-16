from mne_lsl.lsl import resolve_streams
from mne_lsl.lsl.stream_info import StreamInfo
from mne_lsl.stream import StreamLSL as Stream

class AuraLslStreamHandler:
    # Public functions
    def __init__(self, buffer_size_multiplier):
        """
        Creates an LSL signal handler for AURA.
        :param buffer_size_multiplier: The multiplier for the buffer size.
        it is important to consider that the buffer size is determined by the frequency,
        The formula is sampling_frequency_(Hz) * buffer_size_multiplier.
        """
        self.__connected_streams = {}
        self.__buffer_size_multiplier = buffer_size_multiplier

    @staticmethod
    def available_streams() -> list[StreamInfo]:
        """
        Shows the available streams to connect.
        :return: A list of StreamInfo objects.
        """
        return resolve_streams()

    def disconnect_stream(self, stream_name=''):
        """
        Disconnects a specific stream and deletes the object from memory.
        :param stream_name: The name of the stream to be disconnected.
        """
        for _, stream in self.__connected_streams.items():
            if stream.name == stream_name and stream.connected:
                stream.disconnect()
                del stream
                break

    def connect_stream(self, stream_id=''):
        """
        Connects a stream given the stream identifier.
        :param stream_id: The unique ID of the stream to be connected.
        """
        self.__connected_streams[stream_id] = (Stream(bufsize=self.__buffer_size_multiplier, source_id=stream_id))
        self.__connected_streams[stream_id].connect()


    def get_data_from_stream(self, stream_id=''):
        """
        Gets the data from a stream object, this function only gets data when the stream has full new data.
        :param stream_id: The unique ID of the stream to collect data from.
        :return: None if the stream is closed or does not exist or has not being filled with fresh data, returns a tuple when
                 a pack of fresh data is available.
        """
        data_to_return = None

        if self.__connected_streams.get(stream_id) is None:
            data_to_return = -1
        else:
            if (self.__connected_streams[stream_id].connected and
                    self.__connected_streams[stream_id].n_buffer >= self.__connected_streams[stream_id].n_new_samples):
                data = self.__connected_streams[stream_id].get_data()
                data_to_return = data
        return data_to_return

    def rename_aura_channels(self, stream_id='') -> bool:
        """
        Rename the aura channels to the standard name of the electrodes that are being used
        This is supposed to take the stream with 8 channels.
        :param stream_id: The name of the stream with 8 Channels of aura.
        :return: True if the operation is successful. False otherwise.
        """
        named_changed = False
        if self.__connected_streams.get(stream_id) is not None:
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
            self.__connected_streams[stream_id].rename_channels(aura_channels)
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
        self.__disconnect_all_streams()
        for _, stream in self.__connected_streams.items():
            del stream

    def __disconnect_all_streams(self):
        """
        Disconnects all connected streams and deletes the object from memory.
        """
        for _, stream in self.__connected_streams.items():
            if stream.connected:
                stream.disconnect()
