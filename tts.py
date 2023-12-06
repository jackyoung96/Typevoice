from gtts import gTTS
from pydub import AudioSegment
import numpy as np
import io
from scipy.signal import resample

mp3_fp = io.BytesIO()
tts_ko = gTTS(text="안녕하세요", lang='ko')
tts_ko.write_to_fp(mp3_fp)

# MP3 데이터를 NumPy 배열로 변환
mp3_fp.seek(0)
audio = AudioSegment.from_file(mp3_fp, format="mp3")
new_audio = audio.set_frame_rate(16000)
new_audio_array = np.array(new_audio.get_array_of_samples())

audioseg = AudioSegment(new_audio_array.tobytes(), frame_rate=16000, sample_width=2, channels=1)
audioseg.export("new_gtts.mp3", format='mp3')
