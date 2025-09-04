from functools import wraps
from flask import abort
from flask_login import current_user

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
