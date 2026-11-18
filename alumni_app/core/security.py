import re
import bcrypt

def hash_password(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())

def check_password(pw: str, hashed) -> bool:
    if hashed is None:
        return False
    if isinstance(hashed, str):
        hashed = hashed.encode("utf-8")
    return bcrypt.checkpw(pw.encode("utf-8"), hashed)

def validate_password(password: str):
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return "Password must have at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return "Password must have at least one lowercase letter"
    if not re.search(r"\d", password):
        return "Password must have at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must have at least one special character"
    return None
