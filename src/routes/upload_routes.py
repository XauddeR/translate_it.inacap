import os 
import uuid
from flask import Blueprint, request, redirect, url_for, flash, render_template, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from services.deepl_api import translate_text
from services.transcription import audio_transcription
from utils.video_proccess import audio_extract, convert_mp4, create_thumbnail
from utils.languages_dao import get_lang
from utils.extensions import mysql
from pathlib import Path

upload_bp = Blueprint('upload', __name__)
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/', methods = ['GET', 'POST'])
@login_required
def upload_file():
    langs = get_lang(active_only = True)

    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No se encontró ningún archivo', 'upload_error')
            return redirect(request.url)
        
        language = request.form.get('language')
        file = request.files['video']

        valid_codes = {i['codigo'].upper() for i in get_lang(activos_only = True)}

        if language is None or language.upper() not in valid_codes:
            flash("El idioma seleccionado no está disponible.", "upload_error")
            return redirect(request.url)
        
        if file.filename == '':
            flash('No seleccionaste ningún archivo', 'upload_error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            unique_id = str(uuid.uuid4())
            original_filename = secure_filename(file.filename)
            extension = Path(original_filename).suffix

            unique_filename = f'{unique_id}{extension}'
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(temp_path)

            final_path = convert_mp4(temp_path)
            if final_path != temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

            try:
                rel = Path(final_path).relative_to(current_app.root_path)
                db_video_path = rel.as_posix()
            except Exception:
                db_video_path = Path(final_path).as_posix()

            audio_path = audio_extract(final_path)
            db_audio_path = Path(audio_path).as_posix()

            transcription = audio_transcription(audio_path)
            translation = translate_text(transcription, language.upper())

            thumbnail_name = f'{unique_id}.jpg'
            db_thumbnail = create_thumbnail(video_path = final_path, thumbnail_filename = thumbnail_name, thumbnail_folder = current_app.config['THUMBNAIL_FOLDER'])

            try:
                cursor = mysql.connection.cursor()
                cursor.execute(
                    '''
                    INSERT INTO archivos (id, usuario_id, filename, miniatura_archivo, ruta_video, ruta_audio, transcripcion, traduccion, idioma_destino)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''',
                    (
                        unique_id,
                        current_user.id, 
                        original_filename,
                        db_thumbnail,
                        db_video_path, 
                        db_audio_path, 
                        transcription, 
                        translation, 
                        language
                    )
                )
                mysql.connection.commit()
                cursor.close()

                return redirect(url_for('main.history'))
            
            except Exception as e:
                flash(f'Error al guardar en la base de datos: {str(e)}', 'upload_error')
                return redirect(request.url)
        else:
            flash('Formato no permitido. Usa mp4, avi, mov o mkv.', 'upload_error')
            return redirect(request.url)

    return render_template('upload.html', langs = langs)