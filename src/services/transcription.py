from openai import OpenAI, APIError, OpenAIError
from flask import current_app

def audio_transcription(audio_path):
    try:
        client = OpenAI(
            api_key = current_app.config['OPENAI_API_KEY'],
            base_url = 'https://api.lemonfox.ai/v1',
        )

        with open(audio_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model = 'whisper-1',
                file = audio_file
            )

        if isinstance(transcript, dict) and 'error' in transcript:
            raise ValueError(f'API error: {transcript['error']}')

        text = getattr(transcript, 'text', None)
        if not text:
            text = transcript.get('text') if isinstance(transcript, dict) else None

        return text.strip()
    
    except (APIError, OpenAIError, Exception) as e:
        raise RuntimeError(f'{e}')


# import assemblyai as aai
# #  AssemblyAI
# def audio_transcription(audio_path):
#   aai.settings.api_key = current_app.config['ASSEMBLYAI_API_KEY']
#   wav_path = audio_wav(audio_path)
#   config = aai.TranscriptionConfig(speech_model = aai.SpeechModel.universal)
#   transcript = aai.Transcriber(config = config).transcribe(wav_path)

#   if transcript.status == 'error':
#     raise RuntimeError(f'Transcription failed: {transcript.error}')

#   return transcript.text