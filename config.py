"""Settings. Secrets come from environment variables (.env file)."""
import os
import secrets
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass

BASE = Path(__file__).resolve().parent


def _secret_key():
    """Use SECRET_KEY from the environment, else create one once and keep it
    in instance/.secret_key so sessions survive restarts (development only)."""
    key = os.environ.get("SECRET_KEY")
    if key and key != "change-me":
        return key
    path = BASE / "instance" / ".secret_key"
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        path.write_text(secrets.token_hex(32))
    return path.read_text().strip()


class Config:
    SECRET_KEY = _secret_key()
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + str(BASE / "instance" / "medicinefinder.db"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    PER_PAGE = 10


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
