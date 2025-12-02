import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_valid_email(email: str, max_length: int = 255) -> bool:
    if not email:
        return False
    email = email.strip()
    if len(email) > max_length:
        return False
    if not EMAIL_REGEX.match(email):
        return False
    return True
