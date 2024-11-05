import time

from mne_lsl.stream import StreamLSL as Stream
from IO.FileWriting.AuraDataWriter import AuraDataWriter
from IO.SignalProcessing.AuraTools import rename_aura_channels, is_stream_ready

import threading

finished_data_collection = False

def _data_collection_loop(stream, data_writer):
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

def handle_aura_signal(stream_id, buffer_size_multiplier, output_path='.', file_name='aura_data.csv'):
    stream = Stream(bufsize=buffer_size_multiplier, source_id=stream_id)
    stream.connect(processing_flags='all')
    rename_aura_channels(stream)
    channels = ['timestamp'] + stream.info['ch_names']
    data_writer = AuraDataWriter(output_path, file_name, channels)
    data_writer.create_new_file()

    data_thread = threading.Thread(target=_data_collection_loop, args=(stream, data_writer))
    data_thread.start()


handle_aura_signal('AURA_Power', 1)
print("Hello World")
for i in range(5):
    print(i)
    time.sleep(1)
finished_data_collection = True