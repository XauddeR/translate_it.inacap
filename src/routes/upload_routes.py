import os 
import time
import uuid
from flask import Blueprint, request, redirect, url_for, flash, render_template, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from services.deepl_api import translate_text, TranslationError
from services.transcription import audio_transcription
from utils.video_proccess import audio_extract, convert_mp4, create_thumbnail
from utils.languages_dao import get_lang
from utils.extensions import mysql, socketio
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

        valid_codes = {i['codigo'].upper() for i in get_lang(active_only = True)}
        if language is None or language.upper() not in valid_codes:
            flash('El idioma seleccionado no está disponible.', 'upload_error')
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

            try:
                cursor = mysql.connection.cursor()
                cursor.execute(
                    '''
                    INSERT INTO archivos (
                        id, usuario_id, filename, ruta_video, ruta_audio,
                        transcripcion, traduccion, miniatura_archivo,
                        idioma_destino, estado_proceso, progreso
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''',
                    (
                        unique_id,
                        current_user.id,
                        original_filename,
                        '',
                        '',
                        '',
                        '',
                        '',
                        language.upper(),
                        'procesando',
                        0
                    )
                )
                mysql.connection.commit()
                cursor.close()
            except Exception as e:
                flash(f'Error al guardar en la base de datos: {str(e)}', 'upload_error')
                return redirect(request.url)

            app = current_app._get_current_object()

            socketio.start_background_task(
                _process_video_async,
                app,
                unique_id,
                temp_path,
                original_filename,
                language.upper()
            )

            flash('Se inició el procesamiento del video. Puedes continuar navegando.', 'upload_success')
            return redirect(url_for('main.history'))

        else:
            flash('Formato no permitido. Carga archivos MP4, MKV, AVI o MOV.', 'upload_error')
            return redirect(request.url)

    return render_template('upload.html', langs = langs)

def _update_video_status(video_id, estado = None, progreso = None, error_mensaje = None):
    try:
        cursor = mysql.connection.cursor()
        campos = []
        valores = []

        if estado is not None:
            campos.append('estado_proceso = %s')
            valores.append(estado)

        if progreso is not None:
            campos.append('progreso = %s')
            valores.append(progreso)

        if error_mensaje is not None:
            campos.append('error_mensaje = %s')
            valores.append(error_mensaje)

        if campos:
            query = f"UPDATE archivos SET {', '.join(campos)} WHERE id = %s"
            valores.append(video_id)
            cursor.execute(query, tuple(valores))
            mysql.connection.commit()
        
        cursor.close()
    except Exception as e:
        print(f'Error actualizando DB: {e}')

    socketio.emit(
        'status_update',
        {
            'id': video_id,
            'progreso': progreso,
            'estado': estado,
            'error': error_mensaje
        },
        room = video_id
    )

def _process_video_async(app, video_id, temp_path, original_filename, language):
    with app.app_context():
        try:
            _update_video_status(video_id, estado = 'procesando', progreso = 1)

            final_path = convert_mp4(temp_path)
            _update_video_status(video_id, progreso = 15)

            try:
                if temp_path != final_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError as e:
                print(f'No se pudo eliminar el archivo original {temp_path}: {e}')

            audio_path = audio_extract(final_path)
            _update_video_status(video_id, progreso = 35)

            transcription = audio_transcription(audio_path)
            _update_video_status(video_id, progreso = 70)

            try:
                translation = translate_text(transcription, language)
            except TranslationError as te:
                _update_video_status(
                    video_id,
                    estado = 'error',
                    progreso = 0,
                    error_mensaje = str(te)
                )
                return

            _update_video_status(video_id, progreso = 90)

            thumbnail_name = f'{video_id}.jpg'
            db_thumbnail = create_thumbnail(
                video_path = final_path,
                thumbnail_filename = thumbnail_name,
                thumbnail_folder = current_app.config['THUMBNAIL_FOLDER']
            )

            db_video_path = Path(final_path).as_posix()
            db_audio_path = Path(audio_path).as_posix()

            cursor = mysql.connection.cursor()
            cursor.execute(
                '''
                UPDATE archivos
                SET ruta_video = %s,
                    ruta_audio = %s,
                    miniatura_archivo = %s,
                    transcripcion = %s,
                    traduccion = %s,
                    estado_proceso = 'completado',
                    progreso = 100,
                    error_mensaje = NULL
                WHERE id = %s
                ''',
                (db_video_path, db_audio_path, db_thumbnail, transcription, translation, video_id)
            )
            mysql.connection.commit()
            cursor.close()

            _update_video_status(video_id, estado = 'completado', progreso = 100)

        except Exception as e:
            print(f'Falla en el procesamiento: {e}')
            _update_video_status(
                video_id,
                estado = 'error',
                progreso = 0,
                error_mensaje = str(e)
            )