from openai import OpenAI
from flask import current_app
from utils.audio_proccess import audio_wav
import os

def audio_transcription(audio_path):
  client = OpenAI(
    api_key = current_app.config['OPENAI_API_KEY'],
    base_url = "https://api.lemonfox.ai/v1",
  )

  wav_path = audio_wav(audio_path)

  with open(wav_path, 'rb') as audio_file:
    transcript = client.audio.transcriptions.create(
      model = 'whisper-1',
      file = audio_file
    )

  return transcript.text