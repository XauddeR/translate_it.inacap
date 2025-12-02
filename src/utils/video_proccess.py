import os
import ffmpeg
from moviepy import VideoFileClip
from flask import current_app

def is_valid_video(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        streams = probe.get("streams", [])
        has_video = any(s.get("codec_type") == "video" for s in streams)

        if not has_video:
            current_app.logger.warning(f"Archivo sin stream de video: {file_path}")

        return has_video

    except ffmpeg.Error as e:
        current_app.logger.warning(f"FFmpeg error al analizar {file_path}: {e}")
        return False

    except Exception as e:
        current_app.logger.warning(f"Error inesperado al analizar {file_path}: {e}")
        return False
    
def audio_extract(video_path, output_folder = "src/uploads/audios"):
    os.makedirs(output_folder, exist_ok = True)
    audio_path = os.path.join(
        output_folder,
        os.path.splitext(os.path.basename(video_path))[0] + ".mp3"
    )
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)
    video.close()

    return audio_path

def convert_mp4(input_path):
    base, _ = os.path.splitext(input_path)
    output_path = f"{base}.mp4"

    base_dir = os.path.dirname(input_path)
    temp_dir = os.path.join(base_dir, "temp")
    os.makedirs(temp_dir, exist_ok = True)

    filename = os.path.basename(input_path)
    temp_audio_path = os.path.join(temp_dir, f"temp_audio_{filename}.m4a")

    try:
        clip = VideoFileClip(input_path)
        clip.write_videofile(
            output_path,
            codec = "libx264",
            audio_codec = "aac",
            temp_audiofile = temp_audio_path,
            remove_temp = True
        )
        clip.close()
    except Exception as e:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        raise e

    return output_path

def create_thumbnail(video_path, thumbnail_filename, thumbnail_folder):
    try:
        os.makedirs(thumbnail_folder, exist_ok = True)
        thumb_save_path = os.path.join(thumbnail_folder, thumbnail_filename)

        with VideoFileClip(video_path) as clip:
            clip.save_frame(thumb_save_path, t = 1.0)

        rel_path = os.path.relpath(thumb_save_path, current_app.root_path).replace("\\", "/")
        return rel_path

    except Exception as e:
        current_app.logger.error(f"Error al crear miniatura para {thumbnail_filename}: {str(e)}")
        return None
