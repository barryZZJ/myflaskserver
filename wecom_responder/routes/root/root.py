import socket

from flask import Blueprint, request

# Create a Blueprint object for the main section
bp_root = Blueprint('root', __name__)

@bp_root.route('/test')
def welcome():
    return 'Welcome to wecom_responder!'

@bp_root.route('/')
def root():
    sock = request.environ.get('werkzeug.socket')
    if sock:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
    return '', 500  # This line will not be reached

# @bp_root.route('/<path:filename>')
# def serve_files(filename):
#     files_dir = str(FILES)
#     return send_from_directory(files_dir, filename)
