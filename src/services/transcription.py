from openai import OpenAI, APIError, OpenAIError
import re
from flask import current_app

OPENAI_TIMEOUT_SECONDS = 60

def audio_transcription(audio_path):
    try:
        client = OpenAI(
            api_key = current_app.config["OPENAI_API_KEY"],
            base_url = "https://api.lemonfox.ai/v1",
            timeout = OPENAI_TIMEOUT_SECONDS,
            max_retries = 2
        )

        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model = "whisper-1",
                file = audio_file,
            )

        if isinstance(transcript, dict) and "error" in transcript:
            raise ValueError(f"API error: {transcript['error']}")

        text = getattr(transcript, "text", None)
        if not text:
            text = transcript.get("text") if isinstance(transcript, dict) else None

        return text.strip()
    
    except (APIError, OpenAIError, TimeoutError) as e:
        raise RuntimeError(f"Error al transcribir audio (API): {e}")
    except Exception as e:
        raise RuntimeError(f"Erro al transcribir audio: {e}")
    
def format_transcript(text: str, sentences_per_paragraph: int = 3) -> str:
    text = text.strip()

    sentences = re.split(r'(?<=[.!?])\s+', text)

    sentences = [s.strip() for s in sentences if s.strip()]

    paragraphs = []
    for i in range(0, len(sentences), sentences_per_paragraph):
        chunk = sentences[i:i + sentences_per_paragraph]
        paragraph = " ".join(chunk)
        paragraphs.append(paragraph)

    return "\n\n".join(paragraphs)


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