"""
Flask application with authentication, cipher management, and admin panel
"""

import os
import json
import secrets
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import text
from authlib.integrations.flask_client import OAuth

from config import config
from models import db, User, CipherDefinition, CustomCipher, ActivityLog, AdminLog, CookiePreference
import crypto_core as cc

def create_app(config_name="development"):
    """Application factory"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config.get(config_name, config["development"]))
    
    # Ensure instance directory exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Please log in to access this page."

    if app.debug:
        os.environ.setdefault("AUTHLIB_INSECURE_TRANSPORT", "1")

    oauth = OAuth(app)
    if app.config.get("OAUTH_GITHUB_CLIENT_ID") and app.config.get("OAUTH_GITHUB_CLIENT_SECRET"):
        oauth.register(
            name="github",
            client_id=app.config["OAUTH_GITHUB_CLIENT_ID"],
            client_secret=app.config["OAUTH_GITHUB_CLIENT_SECRET"],
            access_token_url="https://github.com/login/oauth/access_token",
            authorize_url="https://github.com/login/oauth/authorize",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "read:user user:email"},
        )
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.before_request
    def track_presence():
        if current_user.is_authenticated:
            _update_last_seen(current_user)
    
    # ============ DECORATORS & HELPERS (defined first) ============
    
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.is_admin:
                flash("Admin access required.", "error")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated_function

    def _get_client_ip():
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.remote_addr or ""

    def _get_user_agent():
        return (request.headers.get("User-Agent", "") or "")[:300]
    
    def log_activity(action, cipher_name, input_length=0, success=True, error_msg="", meta=None):
        """Log user activity"""
        if current_user.is_authenticated:
            log = ActivityLog(
                user_id=current_user.id,
                action=action,
                cipher_name=cipher_name,
                input_length=input_length,
                success=success,
                error_message=error_msg[:200],
                ip_address=_get_client_ip(),
                user_agent=_get_user_agent(),
                meta=json.dumps(meta)[:2000] if meta else ""
            )
            db.session.add(log)
            db.session.commit()
    
    def log_admin_action(action, target, details=""):
        """Log admin activity"""
        if current_user.is_authenticated and current_user.is_admin:
            log = AdminLog(
                admin_id=current_user.id,
                action=action,
                target=target,
                details=details[:500]
            )
            db.session.add(log)
            db.session.commit()

    def _update_login_metadata(user, provider="password"):
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = _get_client_ip()
        user.last_login_user_agent = _get_user_agent()
        if provider:
            user.oauth_provider = user.oauth_provider or provider
        db.session.add(user)
        db.session.commit()

    def _update_last_seen(user):
        now = datetime.utcnow()
        if user.last_seen_at and (now - user.last_seen_at).total_seconds() < 60:
            return
        user.last_seen_at = now
        user.last_seen_ip = _get_client_ip()
        user.last_seen_user_agent = _get_user_agent()
        db.session.add(user)
        db.session.commit()

    def _unique_username(base_name):
        base = "".join(ch for ch in base_name if ch.isalnum() or ch in ("_", "-")).strip("-_")
        if not base:
            base = "cipheruser"
        candidate = base[:24]
        suffix = 1
        while User.query.filter_by(username=candidate).first():
            suffix += 1
            candidate = f"{base[:20]}{suffix}"
        return candidate

    def _oauth_redirect_uri(provider):
        override = app.config.get("OAUTH_REDIRECT_BASE", "")
        if override:
            return f"{override.rstrip('/')}/auth/{provider}/callback"
        return url_for("oauth_callback", provider=provider, _external=True)

    def _oauth_is_configured(provider):
        if provider != "github":
            return False
        client_id = app.config.get("OAUTH_GITHUB_CLIENT_ID", "")
        client_secret = app.config.get("OAUTH_GITHUB_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            return False
        if "your-" in client_id or "your-" in client_secret:
            return False
        return True

    def _get_oauth_client(provider):
        if not _oauth_is_configured(provider):
            flash("OAuth provider is not configured. Update the client ID/secret in .env.", "error")
            return None
        client = oauth.create_client(provider)
        if not client:
            flash("OAuth provider not configured.", "error")
            return None
        return client

    def _provision_oauth_user(provider, provider_id, email, name, avatar_url):
        user = User.query.filter_by(oauth_provider=provider, oauth_id=str(provider_id)).first()
        if user:
            return user, None
        if email:
            existing = User.query.filter_by(email=email).first()
            if existing:
                if existing.oauth_provider and existing.oauth_provider != provider:
                    return None, "Email already linked to another provider."
                existing.oauth_provider = provider
                existing.oauth_id = str(provider_id)
                if avatar_url:
                    existing.avatar_url = avatar_url
                db.session.commit()
                return existing, None
        username_base = name or (email.split("@")[0] if email else f"{provider}_{provider_id}")
        username = _unique_username(username_base)
        fallback_email = email or f"{provider}_{provider_id}@users.noreply.local"
        user = User(username=username, email=fallback_email)
        user.set_password(secrets.token_urlsafe(24))
        user.oauth_provider = provider
        user.oauth_id = str(provider_id)
        user.avatar_url = avatar_url or ""
        db.session.add(user)
        db.session.commit()
        return user, None
    
    def _ensure_sqlite_schema():
        """Add missing columns for SQLite without migrations."""
        if "sqlite" not in app.config["SQLALCHEMY_DATABASE_URI"]:
            return
        try:
            def has_column(table_name, column_name):
                rows = db.session.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
                return any(row[1] == column_name for row in rows)

            def add_column(table_name, column_def):
                db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_def}"))

            columns = {
                "users": [
                    ("admin_level", "admin_level TEXT DEFAULT 'standard'"),
                    ("oauth_provider", "oauth_provider TEXT DEFAULT ''"),
                    ("oauth_id", "oauth_id TEXT DEFAULT ''"),
                    ("avatar_url", "avatar_url TEXT DEFAULT ''"),
                    ("last_login_at", "last_login_at DATETIME"),
                    ("last_login_ip", "last_login_ip TEXT DEFAULT ''"),
                    ("last_login_user_agent", "last_login_user_agent TEXT DEFAULT ''"),
                    ("last_seen_at", "last_seen_at DATETIME"),
                    ("last_seen_ip", "last_seen_ip TEXT DEFAULT ''"),
                    ("last_seen_user_agent", "last_seen_user_agent TEXT DEFAULT ''"),
                ],
                "cipher_definitions": [
                    ("supported", "supported INTEGER DEFAULT 1"),
                    ("base_slug", "base_slug TEXT DEFAULT ''"),
                    ("default_params", "default_params TEXT DEFAULT ''"),
                ],
                "activity_logs": [
                    ("ip_address", "ip_address TEXT DEFAULT ''"),
                    ("user_agent", "user_agent TEXT DEFAULT ''"),
                    ("meta", "meta TEXT DEFAULT ''"),
                ],
            }

            for table_name, cols in columns.items():
                for column_name, column_def in cols:
                    if not has_column(table_name, column_name):
                        add_column(table_name, column_def)
            db.session.commit()
        except Exception:
            db.session.rollback()

    def _seed_defaults():
        """Seed default ciphers and admin account."""
        existing = {c.slug: c for c in CipherDefinition.query.all()}

        def add_cipher(slug, name, desc, category="classic", supported=True):
            if slug in existing:
                cipher = existing[slug]
                cipher.name = name
                cipher.description = desc
                cipher.category = cipher.category or category
                cipher.supported = supported
                return
            cipher = CipherDefinition(
                slug=slug,
                name=name,
                description=desc,
                category=category,
                supported=supported,
            )
            db.session.add(cipher)
            existing[slug] = cipher

        # Seed all built-in ciphers
        for slug, info in cc.CLASSIC_CIPHERS.items():
            add_cipher(
                slug=slug,
                name=info.get("name", slug.replace("-", " ").title()),
                desc=info.get("description", "Cipher entry."),
                category="classic",
                supported=True,
            )

        # Generate dynamic variants (1000+)
        for shift in range(0, 26):
            add_cipher(
                slug=f"caesar-{shift}",
                name=f"Caesar Shift {shift}",
                desc=f"Fixed Caesar shift of {shift}.",
                category="variant",
                supported=True,
            )
        for shift in range(1, 26):
            add_cipher(
                slug=f"rot-{shift}",
                name=f"ROT-{shift}",
                desc=f"ROT variant with shift {shift}.",
                category="variant",
                supported=True,
            )
        for shift in range(1, 26):
            add_cipher(
                slug=f"shift-{shift}",
                name=f"Shift {shift}",
                desc=f"Simple shift variant with fixed offset {shift}.",
                category="variant",
                supported=True,
            )
        for rails in range(2, 13):
            add_cipher(
                slug=f"rail-fence-{rails}",
                name=f"Rail Fence ({rails} rails)",
                desc=f"Rail fence with {rails} rails.",
                category="variant",
                supported=True,
            )
        for key in range(1, 256):
            add_cipher(
                slug=f"xor-{key}",
                name=f"XOR {key}",
                desc=f"Fixed XOR key {key}.",
                category="variant",
                supported=True,
            )
        for shift in range(0, 26):
            add_cipher(
                slug=f"atbash-shift-{shift}",
                name=f"Atbash + Shift {shift}",
                desc=f"Atbash followed by shift {shift}.",
                category="variant",
                supported=True,
            )

        valid_affine_a = [1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25]
        for a in valid_affine_a:
            for b in range(0, 26):
                add_cipher(
                    slug=f"affine-a{a}-b{b}",
                    name=f"Affine a={a}, b={b}",
                    desc=f"Affine cipher with a={a}, b={b}.",
                    category="variant",
                    supported=True,
                )

        def base26_key(index, length=3):
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            chars = []
            for _ in range(length):
                index, rem = divmod(index, 26)
                chars.append(alphabet[rem])
            return "".join(reversed(chars))

        for i in range(300):
            key = base26_key(i, length=3)
            add_cipher(
                slug=f"vigenere-key-{key.lower()}",
                name=f"Vigenere Key {key}",
                desc=f"Vigenere with fixed key {key}.",
                category="variant",
                supported=True,
            )

        for i in range(200):
            key = base26_key(i, length=4)
            add_cipher(
                slug=f"beaufort-key-{key.lower()}",
                name=f"Beaufort Key {key}",
                desc=f"Beaufort with fixed key {key}.",
                category="variant",
                supported=True,
            )

        # Create default admin user
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        admin = User.query.filter_by(username="The X King").first()
        legacy_admin = User.query.filter_by(username="admin").first()
        if legacy_admin and not admin:
            legacy_admin.username = "The X King"
            legacy_admin.email = "thexking@cipherlab.local"
            admin = legacy_admin
        elif not admin:
            admin = User(username="The X King", email="thexking@cipherlab.local")
            db.session.add(admin)

        if admin:
            admin.set_password(admin_password)
            admin.is_admin = True
            admin.admin_level = "high"
            admin.email = admin.email or "thexking@cipherlab.local"

        if legacy_admin and admin and legacy_admin.id != admin.id:
            legacy_admin.is_admin = False
            legacy_admin.admin_level = "standard"

        db.session.commit()
    # Create tables and seed defaults
    with app.app_context():
        db.create_all()
        _ensure_sqlite_schema()
        _seed_defaults()
    
    # ============ PUBLIC ROUTES ============
    
    @app.get("/")
    def index():
        """Home page"""
        q = request.args.get("q", "").strip()
        show = request.args.get("show", "all").strip()
        category = request.args.get("category", "all").strip()
        page = max(int(request.args.get("page", 1)), 1)
        per_page = 24

        query = CipherDefinition.query
        if q:
            like = f"%{q}%"
            query = query.filter(
                (CipherDefinition.name.ilike(like)) | (CipherDefinition.slug.ilike(like))
            )
        if show == "supported":
            query = query.filter_by(supported=True)
        if category and category != "all":
            query = query.filter_by(category=category)

        total = query.count()
        pages = max((total + per_page - 1) // per_page, 1)
        page = min(page, pages)

        ciphers = (
            query.order_by(CipherDefinition.name)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        supported_total = CipherDefinition.query.filter_by(supported=True).count()
        categories = [
            row[0]
            for row in db.session.query(CipherDefinition.category).distinct().order_by(CipherDefinition.category).all()
            if row[0]
        ]

        return render_template(
            "index.html",
            ciphers=ciphers,
            total=total,
            supported_total=supported_total,
            categories=categories,
            category=category,
            page=page,
            pages=pages,
            q=q,
            show=show,
        )
    
    # ============ AUTHENTICATION ROUTES ============
    
    @app.get("/register")
    def register():
        """Registration page"""
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("register.html")
    
    @app.post("/register")
    def register_post():
        """Handle registration"""
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        password_confirm = request.form.get("password_confirm", "").strip()
        
        # Validation
        if not username or len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
            return redirect(url_for("register"))
        
        if not email or "@" not in email:
            flash("Invalid email address.", "error")
            return redirect(url_for("register"))
        
        if not password or len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("register"))
        
        if password != password_confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return redirect(url_for("register"))
        
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for("register"))
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))
    
    @app.get("/login")
    def login():
        """Login page"""
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("login.html")
    
    @app.post("/login")
    def login_post():
        """Handle login"""
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if not username or not password:
            flash("Username and password required.", "error")
            return redirect(url_for("login"))
        
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))
        
        login_user(user, remember=request.form.get("remember") is not None)
        _update_login_metadata(user, provider="password")
        log_activity("login", "password", success=True, meta={"method": "password"})
        flash(f"Welcome, {user.username}!", "success")
        return redirect(url_for("dashboard"))

    @app.get("/auth/<provider>")
    def oauth_login(provider):
        """Start OAuth login flow"""
        if provider != "github":
            flash("Unsupported OAuth provider.", "error")
            return redirect(url_for("login"))
        client = _get_oauth_client(provider)
        if not client:
            return redirect(url_for("login"))
        redirect_uri = _oauth_redirect_uri(provider)
        return client.authorize_redirect(redirect_uri)

    @app.get("/auth/<provider>/callback")
    def oauth_callback(provider):
        """OAuth callback handler"""
        if provider != "github":
            flash("Unsupported OAuth provider.", "error")
            return redirect(url_for("login"))
        client = _get_oauth_client(provider)
        if not client:
            return redirect(url_for("login"))

        try:
            token = client.authorize_access_token()
        except Exception:
            expected = _oauth_redirect_uri("github")
            flash(f"GitHub OAuth failed (401). Check client ID/secret and callback URL: {expected}", "error")
            return redirect(url_for("login"))
        provider_id = None
        email = None
        name = None
        avatar_url = None

        try:
            profile = client.get("user", token=token).json()
        except Exception:
            flash("GitHub profile fetch failed (401). Check OAuth scopes and credentials.", "error")
            return redirect(url_for("login"))
        provider_id = profile.get("id")
        email = profile.get("email")
        name = profile.get("name") or profile.get("login") or email
        avatar_url = profile.get("avatar_url")
        if not email:
            emails_resp = client.get("user/emails", token=token)
            if emails_resp.status_code == 200:
                emails = emails_resp.json()
                primary = next((e for e in emails if e.get("primary")), None)
                if primary:
                    email = primary.get("email")

        if not provider_id:
            flash("OAuth login failed to retrieve account details.", "error")
            return redirect(url_for("login"))

        user, error = _provision_oauth_user(provider, provider_id, email, name, avatar_url)
        if error:
            flash(error, "error")
            return redirect(url_for("login"))

        login_user(user, remember=True)
        _update_login_metadata(user, provider=provider)
        log_activity("login", provider, success=True, meta={"method": provider})
        flash(f"Welcome, {user.username}!", "success")
        return redirect(url_for("dashboard"))
    
    @app.get("/logout")
    def logout():
        """Logout"""
        if current_user.is_authenticated:
            log_activity("logout", "auth", success=True)
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("index"))
    
    # ============ USER DASHBOARD & CIPHER ROUTES ============
    
    @app.get("/dashboard")
    @login_required
    def dashboard():
        """User dashboard"""
        cipher_defs = (
            CipherDefinition.query.filter_by(supported=True)
            .order_by(CipherDefinition.name)
            .limit(12)
            .all()
        )
        cipher_total = CipherDefinition.query.count()
        custom_ciphers = CustomCipher.query.filter_by(user_id=current_user.id).all()
        recent_logs = ActivityLog.query.filter_by(user_id=current_user.id).order_by(
            ActivityLog.timestamp.desc()
        ).limit(10).all()
        
        return render_template(
            "user_dashboard.html",
            cipher_defs=cipher_defs,
            cipher_total=cipher_total,
            custom_ciphers=custom_ciphers,
            recent_logs=recent_logs
        )
    
    @app.get("/cipher/<slug>")
    def cipher_page(slug):
        """Cipher detail page"""
        cipher = CipherDefinition.query.filter_by(slug=slug).first()
        if not cipher:
            flash("Cipher not found.", "error")
            return redirect(url_for("index"))
        cipher_info = cc.get_cipher_info(slug)
        supported = bool(cipher_info) and cipher.supported
        param_defaults = {
            "shift": 3,
            "rails": 3,
            "size": 5,
            "mod": 26,
            "mult": 5,
            "exp": 2,
            "key": "KEY",
            "key1": "KEYONE",
            "key2": "KEYTWO",
            "shift1": 3,
            "shift2": 5,
        }
        return render_template(
            "cipher.html",
            cipher=cipher,
            cipher_info=cipher_info,
            supported=supported,
            param_defaults=param_defaults,
        )
    
    @app.get("/aes")
    def aes_page():
        """AES-GCM encryption page"""
        return render_template("aes.html")
    
    # ============ CIPHER API ROUTES ============
    
    @app.post("/api/encrypt")
    @login_required
    def api_encrypt():
        """Encrypt with classic cipher"""
        data = request.get_json(force=True)
        slug = data.get("slug", "").strip()
        text = data.get("text", "")
        params = data.get("params", {})
        
        try:
            if not cc.cipher_exists(slug):
                cipher_def = CipherDefinition.query.filter_by(slug=slug).first()
                if cipher_def and not cipher_def.supported:
                    return jsonify({"ok": False, "error": "Cipher is catalog-only and not yet supported."}), 400
                if cipher_def and cipher_def.base_slug:
                    base_params = json.loads(cipher_def.default_params or "{}")
                    merged = {**base_params, **params}
                    result = cc.encrypt_with_cipher(cipher_def.base_slug, text, **merged)
                    log_activity("encrypt", slug, len(text), success=True, meta={"alias": cipher_def.base_slug})
                    return jsonify({"ok": True, "result": result})
                return jsonify({"ok": False, "error": "Unknown cipher."}), 400
            
            result = cc.encrypt_with_cipher(slug, text, **params)
            log_activity("encrypt", slug, len(text), success=True)
            
            return jsonify({"ok": True, "result": result})
        except Exception as e:
            error_msg = str(e)
            log_activity("encrypt", slug, len(text), success=False, error_msg=error_msg)
            return jsonify({"ok": False, "error": error_msg}), 400
    
    @app.post("/api/decrypt")
    @login_required
    def api_decrypt():
        """Decrypt with classic cipher"""
        data = request.get_json(force=True)
        slug = data.get("slug", "").strip()
        text = data.get("text", "")
        params = data.get("params", {})
        
        try:
            if not cc.cipher_exists(slug):
                cipher_def = CipherDefinition.query.filter_by(slug=slug).first()
                if cipher_def and not cipher_def.supported:
                    return jsonify({"ok": False, "error": "Cipher is catalog-only and not yet supported."}), 400
                if cipher_def and cipher_def.base_slug:
                    base_params = json.loads(cipher_def.default_params or "{}")
                    merged = {**base_params, **params}
                    result = cc.decrypt_with_cipher(cipher_def.base_slug, text, **merged)
                    log_activity("decrypt", slug, len(text), success=True, meta={"alias": cipher_def.base_slug})
                    return jsonify({"ok": True, "result": result})
                return jsonify({"ok": False, "error": "Unknown cipher."}), 400
            
            result = cc.decrypt_with_cipher(slug, text, **params)
            log_activity("decrypt", slug, len(text), success=True)
            
            return jsonify({"ok": True, "result": result})
        except Exception as e:
            error_msg = str(e)
            log_activity("decrypt", slug, len(text), success=False, error_msg=error_msg)
            return jsonify({"ok": False, "error": error_msg}), 400
    
    @app.post("/api/aes/encrypt")
    @login_required
    def api_aes_encrypt():
        """AES-GCM encryption"""
        data = request.get_json(force=True)
        text = data.get("text", "")
        password = data.get("password", "")
        
        try:
            bundle = cc.aes_encrypt(text, password)
            log_activity("encrypt", "aes-gcm", len(text), success=True)
            
            return jsonify({"ok": True, "bundle": bundle.__dict__})
        except Exception as e:
            error_msg = str(e)
            log_activity("encrypt", "aes-gcm", len(text), success=False, error_msg=error_msg)
            return jsonify({"ok": False, "error": error_msg}), 400
    
    @app.post("/api/aes/decrypt")
    @login_required
    def api_aes_decrypt():
        """AES-GCM decryption"""
        data = request.get_json(force=True)
        password = data.get("password", "")
        bundle_data = data.get("bundle", {})
        
        try:
            bundle = cc.AESBundle(
                salt_b64=bundle_data.get("salt_b64", ""),
                nonce_b64=bundle_data.get("nonce_b64", ""),
                ciphertext_b64=bundle_data.get("ciphertext_b64", "")
            )
            result = cc.aes_decrypt(bundle, password)
            log_activity("decrypt", "aes-gcm", len(result), success=True)
            
            return jsonify({"ok": True, "result": result})
        except Exception as e:
            error_msg = str(e)
            log_activity("decrypt", "aes-gcm", 0, success=False, error_msg=error_msg)
            return jsonify({"ok": False, "error": error_msg}), 400
    
    @app.post("/api/cookie-consent")
    def api_cookie_consent():
        """Log cookie consent choice"""
        data = request.get_json(force=True)
        choice = data.get("choice", "custom")
        prefs = {
            "essential": bool(data.get("essential", True)),
            "functional": bool(data.get("functional", False)),
            "analytics": bool(data.get("analytics", False)),
            "marketing": bool(data.get("marketing", False)),
        }

        anon_id = request.cookies.get("cipherlab_anon_id")
        if not anon_id:
            anon_id = uuid.uuid4().hex

        record = None
        if current_user.is_authenticated:
            record = CookiePreference.query.filter_by(user_id=current_user.id).order_by(
                CookiePreference.updated_at.desc()
            ).first()
        else:
            record = CookiePreference.query.filter_by(anon_id=anon_id).order_by(
                CookiePreference.updated_at.desc()
            ).first()

        if not record:
            record = CookiePreference(
                user_id=current_user.id if current_user.is_authenticated else None,
                anon_id=anon_id,
            )
            db.session.add(record)

        record.choice = choice
        record.essential = prefs["essential"]
        record.functional = prefs["functional"]
        record.analytics = prefs["analytics"]
        record.marketing = prefs["marketing"]
        record.ip_address = _get_client_ip()
        record.user_agent = _get_user_agent()
        db.session.commit()

        if current_user.is_authenticated:
            log_activity("cookie_consent", "system", 0, success=True, meta=prefs)

        session["cookies_accepted"] = prefs["functional"] or prefs["analytics"] or prefs["marketing"]

        response = jsonify({"ok": True, "message": "Cookie preference saved."})
        max_age = 60 * 60 * 24 * 365
        response.set_cookie(
            "cipherlab_cookie_choice",
            choice,
            max_age=max_age,
            samesite="Lax",
            secure=app.config.get("SESSION_COOKIE_SECURE", False),
        )
        response.set_cookie(
            "cipherlab_cookie_prefs",
            json.dumps(prefs),
            max_age=max_age,
            samesite="Lax",
            secure=app.config.get("SESSION_COOKIE_SECURE", False),
        )
        response.set_cookie(
            "cipherlab_anon_id",
            anon_id,
            max_age=max_age,
            samesite="Lax",
            secure=app.config.get("SESSION_COOKIE_SECURE", False),
            httponly=True,
        )
        return response
    
    # ============ ADMIN ROUTES ============
    
    @app.get("/admin")
    @admin_required
    def admin_dashboard():
        """Admin dashboard"""
        user_q = request.args.get("user_q", "").strip()
        cipher_q = request.args.get("cipher_q", "").strip()
        cipher_page = max(int(request.args.get("cipher_page", 1)), 1)
        cipher_per_page = 12

        user_query = User.query
        if user_q:
            like = f"%{user_q}%"
            user_query = user_query.filter(
                (User.username.ilike(like)) | (User.email.ilike(like))
            )
        all_users = user_query.order_by(User.created_at.desc()).all()

        cipher_query = CipherDefinition.query
        if cipher_q:
            like = f"%{cipher_q}%"
            cipher_query = cipher_query.filter(
                (CipherDefinition.name.ilike(like)) | (CipherDefinition.slug.ilike(like))
            )
        total_ciphers = cipher_query.count()
        cipher_pages = max((total_ciphers + cipher_per_page - 1) // cipher_per_page, 1)
        cipher_page = min(cipher_page, cipher_pages)
        cipher_defs = (
            cipher_query.order_by(CipherDefinition.name)
            .offset((cipher_page - 1) * cipher_per_page)
            .limit(cipher_per_page)
            .all()
        )

        admin_logs = AdminLog.query.order_by(AdminLog.timestamp.desc()).limit(50).all()
        activity_stats = db.session.query(
            ActivityLog.cipher_name,
            db.func.count(ActivityLog.id).label("count")
        ).group_by(ActivityLog.cipher_name).all()
        recent_activity = db.session.query(ActivityLog, User).join(User, User.id == ActivityLog.user_id).order_by(
            ActivityLog.timestamp.desc()
        ).limit(50).all()
        total_users = User.query.count()
        supported_total = CipherDefinition.query.filter_by(supported=True).count()
        catalog_total = CipherDefinition.query.filter_by(supported=False).count()
        admin_users = User.query.filter_by(is_admin=True).order_by(User.username).all()
        standard_admin_count = User.query.filter_by(is_admin=True, admin_level="standard").count()
        cookie_prefs = CookiePreference.query.order_by(CookiePreference.updated_at.desc()).limit(100).all()
        cookie_prefs_by_user = {}
        for pref in cookie_prefs:
            if pref.user_id and pref.user_id not in cookie_prefs_by_user:
                cookie_prefs_by_user[pref.user_id] = pref
        online_since = datetime.utcnow() - timedelta(minutes=15)
        live_users = User.query.filter(User.last_seen_at >= online_since).order_by(User.last_seen_at.desc()).all()

        return render_template(
            "admin_dashboard.html",
            all_users=all_users,
            cipher_defs=cipher_defs,
            admin_logs=admin_logs,
            activity_stats=activity_stats,
            recent_activity=recent_activity,
            total_users=total_users,
            supported_total=supported_total,
            catalog_total=catalog_total,
            cipher_page=cipher_page,
            cipher_pages=cipher_pages,
            cipher_q=cipher_q,
            user_q=user_q,
            admin_users=admin_users,
            standard_admin_count=standard_admin_count,
            high_admin_key_set=bool(app.config.get("HIGH_ADMIN_KEY") and app.config.get("HIGH_ADMIN_KEY") != "dev-high-admin-key-change-me"),
            cookie_prefs_by_user=cookie_prefs_by_user,
            cookie_prefs=cookie_prefs,
            live_users=live_users,
        )
    
    @app.post("/admin/ciphers/create")
    @admin_required
    def admin_create_cipher():
        """Create new cipher definition"""
        slug = request.form.get("slug", "").strip()
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "classic").strip()
        base_slug = request.form.get("base_slug", "").strip()
        default_params = request.form.get("default_params", "").strip()
        
        if not slug or not name:
            flash("Slug and name required.", "error")
            return redirect(url_for("admin_dashboard"))
        
        if CipherDefinition.query.filter_by(slug=slug).first():
            flash("Cipher with this slug already exists.", "error")
            return redirect(url_for("admin_dashboard"))
        
        if base_slug and not cc.cipher_exists(base_slug):
            flash("Base cipher not found in built-in ciphers.", "error")
            return redirect(url_for("admin_dashboard"))

        cipher = CipherDefinition(
            slug=slug,
            name=name,
            description=description,
            category=category,
            supported=True if base_slug else False,
            base_slug=base_slug,
            default_params=default_params,
        )
        db.session.add(cipher)
        db.session.commit()
        
        log_admin_action("create_cipher", slug, f"Created cipher: {name}")
        flash(f"Cipher '{name}' created.", "success")
        return redirect(url_for("admin_dashboard"))
    
    @app.post("/admin/ciphers/delete/<int:cipher_id>")
    @admin_required
    def admin_delete_cipher(cipher_id):
        """Delete cipher definition"""
        cipher = CipherDefinition.query.get_or_404(cipher_id)
        slug = cipher.slug
        db.session.delete(cipher)
        db.session.commit()
        
        log_admin_action("delete_cipher", slug, f"Deleted cipher: {cipher.name}")
        flash(f"Cipher '{cipher.name}' deleted.", "success")
        return redirect(url_for("admin_dashboard"))
    
    @app.post("/admin/users/promote/<int:user_id>")
    @admin_required
    def admin_promote_user(user_id):
        """Promote user to admin"""
        if current_user.admin_level != "high":
            flash("High admin access required to promote admins.", "error")
            return redirect(url_for("admin_dashboard"))

        high_key = request.form.get("high_admin_key", "").strip()
        if not high_key or high_key != app.config.get("HIGH_ADMIN_KEY"):
            flash("Invalid high admin key.", "error")
            return redirect(url_for("admin_dashboard"))

        user = User.query.get_or_404(user_id)
        user.is_admin = True
        user.admin_level = "standard"
        db.session.commit()
        
        log_admin_action("promote_user", user.username, "Promoted to admin")
        flash(f"User '{user.username}' promoted to admin.", "success")
        return redirect(url_for("admin_dashboard"))
    
    @app.post("/admin/users/demote/<int:user_id>")
    @admin_required
    def admin_demote_user(user_id):
        """Demote admin to user"""
        user = User.query.get_or_404(user_id)
        if user.admin_level == "high":
            flash("Cannot demote a high admin.", "error")
            return redirect(url_for("admin_dashboard"))
        if user.id == current_user.id:
            flash("Cannot demote yourself.", "error")
            return redirect(url_for("admin_dashboard"))
        
        user.is_admin = False
        user.admin_level = "standard"
        db.session.commit()
        
        log_admin_action("demote_user", user.username, f"Demoted from admin")
        flash(f"User '{user.username}' demoted.", "success")
        return redirect(url_for("admin_dashboard"))

    
    @app.post("/admin/users/delete/<int:user_id>")
    @admin_required
    def admin_delete_user(user_id):
        """Delete user account"""
        user = User.query.get_or_404(user_id)
        if user.admin_level == "high":
            flash("Cannot delete a high admin.", "error")
            return redirect(url_for("admin_dashboard"))
        if user.id == current_user.id:
            flash("Cannot delete your own account.", "error")
            return redirect(url_for("admin_dashboard"))
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        log_admin_action("delete_user", username, f"User account deleted")
        flash(f"User '{username}' deleted.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.get("/admin/users/<int:user_id>")
    @admin_required
    def admin_user_detail(user_id):
        """User tracking detail page"""
        if current_user.admin_level != "high":
            flash("High admin access required.", "error")
            return redirect(url_for("admin_dashboard"))
        user = User.query.get_or_404(user_id)
        logs = ActivityLog.query.filter_by(user_id=user.id).order_by(
            ActivityLog.timestamp.desc()
        ).limit(100).all()
        cookie_pref = CookiePreference.query.filter_by(user_id=user.id).order_by(
            CookiePreference.updated_at.desc()
        ).first()
        return render_template(
            "admin_user_detail.html",
            user=user,
            logs=logs,
            cookie_pref=cookie_pref,
        )
    
    # ============ ERROR HANDLERS ============
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page not found."), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", code=500, message="Server error."), 500
    
    return app

# Create and run app
_env = os.environ.get("FLASK_ENV", "development").lower()
app = create_app("production" if _env == "production" else "development")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
