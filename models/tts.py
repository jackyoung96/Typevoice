from gtts import gTTS
import io
from pydub import AudioSegment
import numpy as np

def base_tts(input_text):
    tts_ko = gTTS(text=input_text, lang='ko')
    mp3_fp = io.BytesIO()
    tts_ko.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    audio = AudioSegment.from_file(mp3_fp, format="mp3")
    audio = audio.set_frame_rate(16000)
    audio_array = np.array(audio.get_array_of_samples(), dtype=np.float32) / 2**15

    return audio_array