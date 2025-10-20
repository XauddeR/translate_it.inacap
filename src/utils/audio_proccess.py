import os
from moviepy import AudioFileClip
from pathlib import Path

def audio_wav(input_path: str, target_sr: int = 16000) -> str:
    input_path = Path(input_path)
    output_path = input_path.with_name(input_path.stem + '_normalized.wav')

    audio = AudioFileClip(str(input_path))

    audio.write_audiofile(
        str(output_path),
        fps = target_sr,
        nbytes = 2,
        codec = 'pcm_s16le',
        ffmpeg_params = ['-ac', '1']
    )
    audio.close()

    try:
        if input_path.suffix.lower() != '.wav' and input_path.exists():
            os.remove(input_path)
    except Exception as e:
        print(f"⚠️ No se pudo eliminar el archivo original: {e}")

    return str(output_path)