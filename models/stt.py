from faster_whisper import WhisperModel

model_size = "base"
whisper_model = WhisperModel(model_size, compute_type="int8")

def base_stt(chunk):
    result = []
    segments, info = whisper_model.transcribe(chunk, 
                                        no_speech_threshold=0.6, # TODO
                                        language='ko')
    for segment in segments:
        if segment.no_speech_prob < 0.6:
            result.append(segment.text)
            
    return ' '.join(result).strip()