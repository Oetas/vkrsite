from functools import wraps
from flask import abort
from flask_login import current_user
from flask import url_for
import os
from uuid import uuid4
from werkzeug.utils import secure_filename

def roles_required(*roles):
    """
    Декоратор: проверяет, что у юзера есть хотя бы одна из ролей
    """
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(401)  # Неавторизован
            if not any(current_user.has_role(r) for r in roles):
                return abort(403)  # Нет прав
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def make_breadcrumbs(*items):
    """
    items — список кортежей: (label, endpoint_or_url, endpoint_args_dict)
    Для endpoint_or_url можно передать URL напрямую или имя endpoint
    """
    result = []
    for label, endpoint_or_url, args in items:
        if endpoint_or_url is None:
            result.append((label, None))
        else:
            try:
                url = url_for(endpoint_or_url, **(args or {}))
            except Exception:
                url = endpoint_or_url
            result.append((label, url))
    return result

def allowed_file(filename, allowed_set):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed_set

def save_uploaded_file(storage_file, upload_dir, allowed_exts):
    """
    storage_file: werkzeug FileStorage
    upload_dir: папка куда сохранять (полный путь)
    Возвращает: (stored_filename, original_filename, size_bytes, content_type)
    """
    original_name = storage_file.filename
    if not allowed_file(original_name, allowed_exts):
        raise ValueError("Extension not allowed")

    orig_secure = secure_filename(original_name)
    ext = orig_secure.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid4().hex}.{ext}"
    dest_path = os.path.join(upload_dir, unique_name)
    storage_file.save(dest_path)
    size = os.path.getsize(dest_path)
    content_type = storage_file.mimetype or None
    return unique_name, orig_secure, size, content_type