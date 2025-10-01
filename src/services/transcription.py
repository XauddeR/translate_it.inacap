import os
import assemblyai as aai
from openai import OpenAI

from flask import current_app
from utils.audio_proccess import audio_wav

# def audio_transcription(audio_path):
#   client = OpenAI(
#     api_key = current_app.config['OPENAI_API_KEY'],
#     base_url = "https://api.lemonfox.ai/v1",
#   )

#   wav_path = audio_wav(audio_path)

#   with open(wav_path, 'rb') as audio_file:
#     transcript = client.audio.transcriptions.create(
#       model = 'whisper-1',
#       file = audio_file
#     )

#   return transcript.text

def audio_transcription(audio_path):
  aai.settings.api_key = current_app.config['ASSEMBLYAI_API_KEY']

  wav_path = audio_wav(audio_path)

  config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.universal)

  transcript = aai.Transcriber(config=config).transcribe(wav_path)

  if transcript.status == "error":
    raise RuntimeError(f"Transcription failed: {transcript.error}")

  return transcript.text