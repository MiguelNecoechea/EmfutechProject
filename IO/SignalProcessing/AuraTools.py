from mne_lsl.stream import StreamLSL as Stream
from mne_lsl.lsl import resolve_streams
def is_stream_ready(stream: Stream) -> bool:
    """
    Check if the streams has enough data to process.
    :return: A boolean indicating whether the stream has enough data to process.
    """
    is_ready = False
    if stream is None:
        raise RuntimeError("The stream is not created yet.")

    if (stream.connected and
            stream.n_new_samples >= stream.n_buffer):
        is_ready = True
    return is_ready

def rename_aura_channels(stream) -> bool:
    """
    Rename the aura channels to the standard name of the electrodes that are being used
    This is supposed to take the stream with 8 channels. However, it is also capable of renaming the other channels.
    :return: True if the operation is successful. False otherwise.
    """
    named_changed = False
    if stream is not None:
        if stream.info['nchan'] == 8:
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
        elif stream.info['nchan'] == 40:
            aura_channels = rename_40_channels()
        else:
            raise RuntimeError("The stream is not supported")

        stream.rename_channels(aura_channels)
        named_changed = True

    return named_changed

def rename_40_channels():
    """
    Creates a mapping for an AURA Power Signal.
    :return: An array with the mapping of the channels.
    """
    waves = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
    channels = ['F3', 'F4', 'Cz', 'C3', 'C4', 'Pz', 'P3', 'P4']
    current_position = 0
    mapping = {}
    for wave in waves:
        for channel in channels:
            mapping[str(current_position)] = wave + '_' + channel
            current_position += 1
    return mapping

def delete_channels(stream: Stream, waves: list[str], channels: list[str]):
    """
    Delete the channels from the stream. It handles both the 8 channel and 40 channel aura signals.
    :param stream: The stream to remove the channels from.
    :param waves: The name of the type of waves to remove.
    :param channels: The name of the electrodes to remove.
    """
    channels_to_dlt = []
    if len(waves) == 0 and len(channels) != 0:
        for channel in channels:
            channels_to_dlt.append(channel)
    else:
        for wave in waves:
            for channel in channels:
                channels_to_dlt.append(wave + '_' + channel)
    stream.drop_channels(channels_to_dlt)

def resolve_aura() -> str:
    """
    Resolve the aura stream.
    :return: The source id of the aura stream that has 40 channels.
    """
    av_streams = resolve_streams()
    for stream in av_streams:
        if stream.n_channels == 40:
            return stream.source_id
    raise ValueError("No aura stream with 40 channels found")
