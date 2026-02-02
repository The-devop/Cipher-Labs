from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model with authentication"""
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    admin_level = db.Column(db.String(20), default="standard")  # standard, high
    admin_key = db.Column(db.String(64), default="")
    oauth_provider = db.Column(db.String(30), default="")
    oauth_id = db.Column(db.String(120), default="", index=True)
    avatar_url = db.Column(db.String(300), default="")
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(80), default="")
    last_login_user_agent = db.Column(db.String(300), default="")
    last_seen_at = db.Column(db.DateTime)
    last_seen_ip = db.Column(db.String(80), default="")
    last_seen_user_agent = db.Column(db.String(300), default="")
    
    # Relationships
    custom_ciphers = db.relationship("CustomCipher", backref="creator", lazy=True, cascade="all, delete-orphan")
    activity_logs = db.relationship("ActivityLog", backref="user", lazy=True, cascade="all, delete-orphan")
    cookie_preferences = db.relationship("CookiePreference", backref="user", lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.username}>"

class CipherDefinition(db.Model):
    """Built-in cipher definitions"""
    __tablename__ = "cipher_definitions"
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30), default="classic")  # classic, modern, aes
    supported = db.Column(db.Boolean, default=True)
    base_slug = db.Column(db.String(80), default="")  # optional alias to built-in cipher
    default_params = db.Column(db.Text, default="")  # JSON params for alias ciphers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CipherDefinition {self.name}>"

class CustomCipher(db.Model):
    """User-created custom ciphers"""
    __tablename__ = "custom_ciphers"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, default="")
    cipher_type = db.Column(db.String(30), nullable=False)  # caesar, vigenere, substitution, etc.
    parameters = db.Column(db.Text, default="{}")  # JSON string of cipher parameters
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint("user_id", "slug", name="uq_user_cipher_slug"),)
    
    def __repr__(self):
        return f"<CustomCipher {self.name}>"

class ActivityLog(db.Model):
    """User activity logging"""
    __tablename__ = "activity_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(30), nullable=False)  # encrypt, decrypt
    cipher_name = db.Column(db.String(80), nullable=False)
    input_length = db.Column(db.Integer, default=0)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.String(200), default="")
    ip_address = db.Column(db.String(80), default="")
    user_agent = db.Column(db.String(300), default="")
    meta = db.Column(db.Text, default="")  # JSON string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ActivityLog {self.action} by {self.user_id}>"

class AdminLog(db.Model):
    """Admin activity logging"""
    __tablename__ = "admin_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    target = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, default="")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AdminLog {self.action}>"

class CookiePreference(db.Model):
    """Cookie consent/preferences"""
    __tablename__ = "cookie_preferences"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    anon_id = db.Column(db.String(64), default="", index=True)
    choice = db.Column(db.String(20), default="custom")  # accepted, custom
    essential = db.Column(db.Boolean, default=True)
    functional = db.Column(db.Boolean, default=False)
    analytics = db.Column(db.Boolean, default=False)
    marketing = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(80), default="")
    user_agent = db.Column(db.String(300), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
