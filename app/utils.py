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
    items: список кортежей (label, endpoint_or_url_or_none, kwargs_or_none)

    - endpoint_or_url может быть:
      * None            -> текущая (не кликабельная) позиция
      * имя endpoint    -> будет применён url_for(endpoint, **kwargs)
      * строка URL      -> если начинается с '/' или 'http' — используется как есть

    Возвращает: список dict {'label': ..., 'url': ...} (url == None для текущей страницы).
    """
    out = []
    for label, endpoint_or_url, kwargs in items:
        if endpoint_or_url is None:
            url = None
        else:
            # если явно передали путь/ссылку — используем её
            if isinstance(endpoint_or_url, str) and (endpoint_or_url.startswith("/") or endpoint_or_url.startswith("http")):
                url = endpoint_or_url
            else:
                try:
                    url = url_for(endpoint_or_url, **(kwargs or {}))
                except Exception:
                    # если не получилось — безопасно ставим None
                    url = None
        out.append({"label": label, "url": url})
    return out

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

def make_breadcrumbs(*items):
    """
    items: list of tuples (label, endpoint, kwargs)
    returns: list of dicts with 'label' and 'url' (None if endpoint is None)
    """
    out = []
    for label, endpoint, ep_kwargs in items:
        url = None
        if endpoint:
            url = url_for(endpoint, **(ep_kwargs or {}))
        out.append({"label": label, "url": url})
    return out
