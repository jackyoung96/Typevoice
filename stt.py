from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np

model_size = "small"
whisper_model = WhisperModel(model_size, 
                             compute_type="int8")
samplerate = 16000
chunk_length = 1000
buffer_length = int(samplerate * chunk_length / 1000)

class SharedBuf:
    def __init__(self):
        self.buffer = np.array([], dtype='float32')

    def clearbuf(self):
        self.buffer = []

    def addbuf(self, arr):
        self.buffer = np.append(self.buffer, arr)

    def extbuf(self, arr):
        self.buffer = np.append(self.buffer, arr)

    def getlen(self):
        return len(self.buffer)

    def getbuf(self):
        return self.buffer

    def getx(self, x):
        data = self.buffer[0:x]
        self.buffer = self.buffer[x:]
        return data

buff = SharedBuf()

sdstream = sd.Stream(samplerate=samplerate, channels=1, dtype='float32')
sdstream.start()

while True:
    try:
        data = sdstream.read(32)[0]
        buff.extbuf(data)

        if buff.getlen() > samplerate:
            chunk = buff.getx(buff.getlen())
            segments, info = whisper_model.transcribe(chunk, 
                                                      no_speech_threshold=0.6, # TODO
                                                      language='ko')
            for segment in segments:
                if segment.no_speech_prob < 0.6:
                    print(segment.text, sep=' ', flush=True)
    except KeyboardInterrupt:
        break