from flask_socketio import join_room, leave_room
from utils.extensions import socketio

@socketio.on("connect")
def handle_connect():
    print("Cliente conectado")

@socketio.on("disconnect")
def handle_disconnect():
    print("Cliente desconectado")

@socketio.on("join_file_room")
def handle_join_file_room(data):
    file_id = str(data.get("file_id"))
    if not file_id:
        return
    join_room(file_id)

@socketio.on("leave_file_room")
def handle_leave_file_room(data):
    file_id = str(data.get("file_id"))
    if not file_id:
        return
    leave_room(file_id)
