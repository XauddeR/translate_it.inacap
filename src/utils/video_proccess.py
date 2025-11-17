import os
from moviepy import VideoFileClip
from flask import current_app

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

def create_thumbnail(video_path, thumbnail_filename, thumbnail_folder):
    try:
        os.makedirs(thumbnail_folder, exist_ok = True)
        thumb_save_path = os.path.join(thumbnail_folder, thumbnail_filename)

        with VideoFileClip(video_path) as clip:
            clip.save_frame(thumb_save_path, t = 1.0)

        rel_path = os.path.relpath(thumb_save_path, current_app.root_path).replace('\\', '/')
        return rel_path

    except Exception as e:
        current_app.logger.error(f'Error al crear miniatura para {thumbnail_filename}: {str(e)}')
        return None
