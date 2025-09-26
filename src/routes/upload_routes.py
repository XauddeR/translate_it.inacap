import os 
from flask import Blueprint, request, redirect, url_for, flash, render_template, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from services.deepl_api import translate_text
from services.transcription import audio_transcription
from utils.video_proccess import audio_extract, convert_mp4
from utils.extensions import mysql
from pathlib import Path

upload_bp = Blueprint('upload', __name__)
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/', methods = ['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No se encontró ningún archivo', 'upload_error')
            return redirect(request.url)
        
        language = request.form.get('language')
        file = request.files['video']

        if file.filename == '':
            flash('No seleccionaste ningún archivo', 'upload_error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)

            final_path = convert_mp4(temp_path)

            if final_path != temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

            filename = Path(final_path).name

            try:
                rel = Path(final_path).relative_to(current_app.root_path)
                db_ruta_video = rel.as_posix()
            except Exception:
                db_ruta_video = Path(final_path).as_posix()

            audio_path = audio_extract(final_path)
            db_ruta_audio = Path(audio_path).as_posix()
            transcription = audio_transcription(audio_path)
            translation = translate_text(transcription, language.upper())

            try:
                cursor = mysql.connection.cursor()
                cursor.execute(
                    '''
                    INSERT INTO archivos (usuario_id, filename, ruta_video, ruta_audio, transcripcion, traduccion, idioma_destino)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''',
                    (
                        current_user.id, 
                        filename, 
                        db_ruta_video, 
                        db_ruta_audio, 
                        transcription, 
                        translation, 
                        language
                    )
                )
                mysql.connection.commit()
                cursor.close()

                flash(f'Video subido exitosamente.', 'upload_success')
                return redirect(url_for('main.history'))
            
            except Exception as e:
                flash(f'Error al guardar en la base de datos: {str(e)}', 'upload_error')
                return redirect(request.url)
        else:
            flash('Formato no permitido. Usa mp4, avi, mov o mkv.', 'upload_error')
            return redirect(request.url)

    return render_template('upload.html')