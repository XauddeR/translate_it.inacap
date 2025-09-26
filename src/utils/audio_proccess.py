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

    return str(output_path)