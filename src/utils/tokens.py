from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def _get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

def generate_reset_token(email: str) -> str:
    s = _get_serializer()
    return s.dumps(email, salt = current_app.config["SECURITY_PASSWORD_SALT"])

def confirm_reset_token(token: str, max_age: int = 3600) -> str | None:
    s = _get_serializer()
    try:
        email = s.loads(
            token,
            salt = current_app.config["SECURITY_PASSWORD_SALT"],
            max_age = max_age,
        )
    except Exception:
        return None
    return email
