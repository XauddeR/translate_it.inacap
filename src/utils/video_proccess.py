import os
from moviepy import VideoFileClip

def audio_extract(video_path, output_folder = 'src/uploads/audios'):
    os.makedirs(output_folder, exist_ok = True)
    audio_path = os.path.join(output_folder, os.path.splitext(os.path.basename(video_path))[0] + '.mp3')
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)

    return audio_path

def convert_mp4(input_path):
    base, _ = os.path.splitext(input_path)
    output_path = f'{base}.mp4'

    clip = VideoFileClip(input_path)
    clip.write_videofile(
        output_path,
        codec = 'libx264',
        audio_codec = 'aac'
    )
    clip.close()

    return output_path