import os
import time
import json
import uuid
from flask import Blueprint, render_template, abort, send_from_directory, redirect, url_for, send_file, jsonify, request, current_app, Response, stream_with_context, flash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
from flask_login import current_user, login_required
from utils.extensions import mysql
from io import BytesIO

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user = current_user)

@main_bp.route("/history")
@login_required
def history():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM archivos WHERE usuario_id = %s ORDER BY fecha_subida DESC", (current_user.id,))
    files = cursor.fetchall()
    cursor.close()

    return render_template("history.html", files = files)

@main_bp.route("/file/<file_id>")
@login_required
def file_detail(file_id):
    try:
        uuid_obj = uuid.UUID(file_id)
    except ValueError:
        raise BadRequest("ID inválido")
    
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT 
            a.id,
            a.usuario_id,
            a.filename,
            a.nombre_archivo,
            a.miniatura_archivo,
            a.ruta_video,
            a.ruta_audio,
            a.transcripcion,
            a.traduccion,
            a.idioma_destino,
            a.fecha_subida,
            a.estado_proceso,
            a.error_mensaje,
            a.progreso,
            i.nombre AS idioma_nombre
        FROM archivos a
        LEFT JOIN idiomas i
        ON a.idioma_destino = i.codigo
        WHERE a.id = %s AND a.usuario_id = %s
        LIMIT 1
    """, (str(uuid_obj), current_user.id))
    files = cursor.fetchone()
    cursor.close()

    if not files:
        abort(404)

    if files["usuario_id"] != current_user.id:
        abort(403)

    return render_template("file_detail.html", files = files)


@main_bp.route("/archivo/video/<filename>")
@login_required
def file_video(filename):
    safe_filename = secure_filename(filename)
    upload_folder = os.path.join(current_app.root_path, "uploads", "videos")
    file_path = os.path.join(upload_folder, safe_filename)

    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(upload_folder, safe_filename, as_attachment = False)

@main_bp.route("/file/thumbnail/<filename>")
@login_required
def file_thumbnail(filename):
    safe_filename = secure_filename(filename)
    thumbnail_folder = os.path.join(current_app.root_path, "uploads", "thumbnail")
    file_path = os.path.join(thumbnail_folder, safe_filename)

    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(thumbnail_folder, safe_filename, as_attachment = False)

@main_bp.route("/update_file/<file_id>", methods = ["POST"])
@login_required
def update_file(file_id):
    new_file_name = request.form["filename"].strip()

    if not new_file_name:
        flash("El nombre no puede estar vacío", "upload_error")
        return redirect(url_for("main.history"))
    
    if len(new_file_name) > 255:
        flash("El nombre es demasiado largo.", "upload_error")
        return redirect(url_for("main.history"))

    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        UPDATE archivos 
        SET nombre_archivo = %s 
        WHERE id = %s AND usuario_id = %s
        """,
        (new_file_name, file_id, current_user.id)
    )
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for("main.history"))

@main_bp.route("/delete_file/<file_id>", methods = ["POST"])
@login_required
def delete_file(file_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "DELETE FROM archivos WHERE id = %s AND usuario_id = %s",
        (file_id, current_user.id)
    )
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for("main.history"))

@main_bp.route("/download/<file_id>")
@login_required
def download(file_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT traduccion, nombre_archivo, filename, usuario_id FROM archivos WHERE id = %s
        """,
        (file_id,)
    )
    file = cursor.fetchone()
    cursor.close()

    if not file:
        abort(404, "Archivo no encontrado.")

    if file["usuario_id"] != current_user.id:
        abort(403, "No tienes permiso para descargar este archivo.")

    name = file["nombre_archivo"] or file["filename"]
    name_txt = f"{name.rsplit('.', 1)[0]}.txt"

    buffer = BytesIO()
    buffer.write(file["traduccion"].encode("utf-8"))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment = True,
        download_name = name_txt,
        mimetype = "text/plain"
    )

@main_bp.route("/api/file_status/<file_id>")
@login_required
def file_status(file_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT estado_proceso, progreso
        FROM archivos
        WHERE id = %s AND usuario_id = %s
        """,
        (file_id, current_user.id)
    )
    row = cursor.fetchone()
    cursor.close()

    if not row:
        return jsonify({"error": "not_found"}), 404

    return jsonify({
        "estado": row["estado_proceso"],
        "progreso": int(row["progreso"])
    })

@main_bp.route("/stream/progress/<video_id>")
@login_required
def stream_progress(video_id):
    def generate():
        while True:
            cursor = mysql.connection.cursor()
            cursor.execute(
                """
                SELECT estado_proceso, progreso, error_mensaje
                FROM archivos
                WHERE id = %s AND usuario_id = %s
                """,
                (video_id, current_user.id)
            )
            row = cursor.fetchone()
            cursor.close()

            if not row:
                payload = {"error": "Archivo no encontrado"}
                yield f"data: {json.dumps(payload)}\n\n"
                break

            estado = row["estado_proceso"]
            progreso = row["progreso"]
            error_msg = row.get("error_mensaje")

            payload = {
                "estado": estado,
                "progreso": progreso,
                "error": error_msg
            }

            yield f"data: {json.dumps(payload)}\n\n"

            if estado in ("completado", "error"):
                break

            time.sleep(1)

    return Response(
        stream_with_context(generate()),
        mimetype = "text/event-stream",
        headers = {"Cache-Control": "no-cache"}
    )
