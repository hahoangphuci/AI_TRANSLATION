import os
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder='uploads'):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, folder)
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        return file_path
    return None

def get_file_size(file_path):
    return os.path.getsize(file_path) if os.path.exists(file_path) else 0

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)