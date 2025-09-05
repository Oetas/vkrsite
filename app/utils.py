from functools import wraps
from flask import abort
from flask_login import current_user
from flask import url_for
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
