from mne_lsl.stream import StreamLSL as Stream

from IO.FileWriting.AuraDataWriter import AuraDataWriter
from IO.SignalProcessing.AuraTools import rename_aura_channels, is_stream_ready

finished_data_collection = False

def handle_aura_signal(stream_id, buffer_size_multiplier):
    stream = Stream(bufsize=buffer_size_multiplier, source_id=stream_id)
    stream.connect(processing_flags='all')
    rename_aura_channels(stream)
    data_writer = AuraDataWriter('test', 'test.csv')
    data_writer.create_new_file()
    while True:
        if is_stream_ready(stream):
           data, ts = stream.get_data()
           data_writer.write_data(ts, data)

        if finished_data_collection:
            break

    data_writer.close_file()
    stream.disconnect()
    del data_writer
    del stream

handle_aura_signal('filtered', 1)