import os
from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))

def _get_env(*names):
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return ""

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or "dev-secret-change-me-12345"
    
    # Get the instance directory
    BASEDIR = BASEDIR
    _is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
    INSTANCE_DIR = os.path.join(("/tmp" if _is_serverless else BASEDIR), "instance")
    try:
        os.makedirs(INSTANCE_DIR, exist_ok=True)
    except OSError:
        INSTANCE_DIR = os.path.join("/tmp", "instance")
        os.makedirs(INSTANCE_DIR, exist_ok=True)
    
    _db_url = os.environ.get("DATABASE_URL", "").strip()
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    if _db_url.startswith("sqlite:///"):
        sqlite_path = _db_url.replace("sqlite:///", "", 1)
        if not os.path.isabs(sqlite_path):
            sqlite_path = os.path.join(BASEDIR, sqlite_path)
        try:
            os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        except OSError:
            sqlite_path = os.path.join(INSTANCE_DIR, os.path.basename(sqlite_path))
        _db_url = "sqlite:///" + sqlite_path.replace("\\", "/")
    SQLALCHEMY_DATABASE_URI = _db_url or f"sqlite:///{os.path.join(INSTANCE_DIR, 'cipherlab.sqlite3')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days

    # OAuth configuration
    OAUTH_GITHUB_CLIENT_ID = _get_env("GITHUB_CLIENT_ID", "GITHUB_OAUTH_CLIENT_ID", "OAUTH_GITHUB_CLIENT_ID")
    OAUTH_GITHUB_CLIENT_SECRET = _get_env("GITHUB_CLIENT_SECRET", "GITHUB_OAUTH_CLIENT_SECRET", "OAUTH_GITHUB_CLIENT_SECRET")
    OAUTH_REDIRECT_BASE = os.environ.get("OAUTH_REDIRECT_BASE", "")

    # High admin key required to authorize new admins
    HIGH_ADMIN_KEY = os.environ.get("HIGH_ADMIN_KEY", "dev-high-admin-key-change-me")

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
