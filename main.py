import time

import matplotlib.pyplot as plt

from IO.ScreenRecording.WindowsScreenRecorder import WindowsScreenRecorder
from IO.SignalProcessing.AuraSignalHandler import AuraLslStreamHandler

# handler = VideoHandler()
# processor = EmotionRecognizer('opencv')
# data_handler = AuraLslStreamHandler(1)
# lsl_writer = AuraDataWriter('/Users/mnecoea/PycharmProjects/AuraSignalProcessing', 'test.csv')
# emotion_writer = EmotionPredictedWriter('/Users/mnecoea/PycharmProjects/AuraSignalProcessing', 'test1.csv')
# channel = 'filtered'
# time = 1
# data_handler.connect_stream(channel)
#
# lsl_writer.create_new_file()
# emotion_writer.create_new_file()
#
# while True:
#     frame = handler.get_frame()
#     winsize = data_handler.get_stream_new_samples(channel) / data_handler.get_stream_frequency(channel)
#     if winsize >= 1:
#         data, ts = data_handler.get_data_from_stream(channel)
#         emotion = processor.recognize_emotion(frame)[0]['dominant_emotion']
#         emotion_writer.write_data(time, emotion)
#         lsl_writer.write_data(ts, data)
#         time += 1
#
#     cv2.imshow('Emotion detection', frame)
#
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# handler.close_camera()
# cv2.destroyAllWindows()
# emotion_writer.close_file()
# lsl_writer.close_file()
#
# del lsl_writer
# del emotion_writer
name = 'AURA'
lowbp = 1.0
highbp = 50.0
channel = 'AuraLSL-20241025-12;10;20'
stream = AuraLslStreamHandler(1, channel)
print(stream.available_streams())
stream.drop_channels(['P4', 'P3', 'C4', 'Pz', 'C3'])

stream.add_notch_filter()
stream.add_filter(lowbp, highbp)

stream.clear_buffer()
f, ax = plt.subplots(3, 1, sharex=True, constrained_layout=True)
for _ in range(3):  # acquire 3 separate window
    # figure how many new samples are available, in seconds
    winsize = stream.get_stream_new_samples() / stream.get_stream_frequency()
    # retrieve and plot data
    while not stream.is_stream_ready():
        pass
    else:
        data, ts = stream.get_data_from_stream()
        print(data)
        for k, data_channel in enumerate(data):
            if k >= 3:
                break
            ax[k].plot(ts, data_channel)
ax[-1].set_xlabel("Timestamp (LSL time)")
plt.show()
print(stream.get_stream_info())

recorder = WindowsScreenRecorder('tast', "test")
recorder.start_recording()
for i in range(10):
    time.sleep(1)

recorder.stop_recording()
# from screeninfo import screeninfo, Monitor
#
# monitors = screeninfo.get_monitors()
#
# print(monitors)