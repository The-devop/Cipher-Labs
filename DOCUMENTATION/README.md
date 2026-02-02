# 🔐 Cipher Lab

A beautiful, modern web application for learning and experimenting with cryptography. Features multiple cipher implementations (Caesar, Vigenère, ROT13, Atbash, Substitution, Rail Fence) plus real AES-GCM encryption.

## Features

✨ **7 Classic Ciphers**
- Caesar (with configurable shift)
- ROT13 (Caesar variant)
- Atbash (mirror alphabet)
- Vigenère (polyalphabetic)
- Beaufort (reciprocal Vigenère)
- Substitution (full mapping)
- Rail Fence (zigzag)

🔒 **Real Encryption**
- AES-256-GCM (authenticated encryption)
- Scrypt key derivation
- Random salt & nonce per encryption

👥 **User Management**
- User registration & login
- Activity tracking
- User dashboard
- Admin panel

🎨 **Beautiful UI**
- Modern dark theme with gradients
- Fully responsive (mobile, tablet, laptop, monitor)
- Smooth animations and transitions
- Professional design

## Quick Start

### 1. Install Dependencies

```bash
cd f:/PPP/ciphersite
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The app will be available at `http://localhost:5000`

### 3. Default Admin Account

- **Username:** `admin`
- **Password:** `admin123`

⚠️ Change these in production!

## Project Structure

```
ciphersite/
├── app.py                    # Flask application & routes
├── models.py                 # Database models (SQLAlchemy)
├── crypto_core.py            # Cipher implementations
├── config.py                 # Configuration
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
├── instance/
│   └── cipherlab.sqlite3    # SQLite database (auto-created)
├── templates/
│   ├── layout.html          # Base template
│   ├── index.html           # Home page
│   ├── cipher.html          # Cipher interface
│   ├── aes.html             # AES encryption page
│   ├── register.html        # Registration page
│   ├── login.html           # Login page
│   ├── user_dashboard.html  # User dashboard
│   ├── admin_dashboard.html # Admin panel
│   └── error.html           # Error pages
└── static/
    ├── style.css            # Responsive CSS
    └── app.js               # Client-side JavaScript
```

## Using the Application

### For Users

1. **Register** - Create a new account
2. **Login** - Sign in with your credentials
3. **Choose a cipher:**
   - Classic ciphers for learning
   - AES-GCM for real encryption
4. **Encrypt/Decrypt** - Enter text and press buttons
5. **Copy or Export** - Save your results

### For Admins

1. **Login** with admin account
2. **Manage Users** - Promote/demote/delete users
3. **Manage Ciphers** - Create or delete cipher definitions
4. **View Logs** - Track admin and user activity

## Cipher Details

### Classic Ciphers (Educational)
These are for learning and casual use only. They are **not secure** against modern cryptanalysis.

- **Caesar:** Simple shift cipher. Shift = 3 is ROT-3.
- **ROT13:** Caesar with shift = 13 (same forward and backward).
- **Atbash:** Mirror the alphabet (A→Z, B→Y, etc).
- **Vigenère:** Repeating key polyalphabetic cipher.
- **Beaufort:** Reciprocal variant of Vigenère.
- **Substitution:** Map each letter to another (26! possible keys).
- **Rail Fence:** Write in zigzag pattern, read row by row.

### AES-GCM (Real Encryption)
**This is actual, cryptographically secure encryption.**

- **Algorithm:** AES-256-GCM (Galois/Counter Mode)
- **Key derivation:** Scrypt (memory-hard, resistant to brute force)
- **Authentication:** Detects tampering automatically
- **Random elements:** New salt and nonce for each encryption
- **Security depends on:** Password strength (use 12+ characters)

## Environment Variables

See `.env` file:

```
FLASK_ENV=development
FLASK_SECRET_KEY=your-secret-key-change-this-in-production
ADMIN_PASSWORD=admin123
DATABASE_URL=sqlite:///instance/cipherlab.sqlite3
```

Change these in production!

## Database Schema

### Users Table
- id, username, email, password_hash, created_at, is_admin

### CipherDefinition Table
- id, slug, name, description, category, created_at

### CustomCipher Table
- id, user_id, slug, name, description, cipher_type, parameters, created_at

### ActivityLog Table
- id, user_id, action, cipher_name, input_length, success, error_message, timestamp

### AdminLog Table
- id, admin_id, action, target, details, timestamp

## Responsive Design

The UI is optimized for:
- 📱 Mobile phones (320px+)
- 📱 Tablets (768px+)
- 💻 Laptops (1024px+)
- 🖥️ Desktop monitors (1200px+)

All layouts adapt smoothly with CSS Grid and Flexbox.

## Security Considerations

✅ **Done:**
- Password hashing with Werkzeug (pbkdf2:sha256)
- Session management with secure cookies
- CSRF protection via Flask forms
- SQL injection prevention via SQLAlchemy ORM
- AES-GCM authenticated encryption

⚠️ **For Production:**
- Change SECRET_KEY and ADMIN_PASSWORD
- Enable HTTPS (set SESSION_COOKIE_SECURE=True)
- Use a real database (PostgreSQL instead of SQLite)
- Add rate limiting
- Enable CORS carefully
- Use a production WSGI server (Gunicorn)
- Add email verification for registrations
- Implement password reset functionality
- Add 2FA support

## Troubleshooting

**Port 5000 already in use?**
```bash
python app.py  # Will try port 5001, 5002, etc.
```

**Database issues?**
```bash
# Delete the database and recreate it
rm instance/cipherlab.sqlite3
python app.py
```

**Import errors?**
```bash
# Make sure all dependencies are installed
pip install -r requirements.txt --upgrade
```

## Technologies

- **Backend:** Flask, SQLAlchemy, Flask-Login
- **Encryption:** cryptography (Scrypt, AES-GCM)
- **Database:** SQLite (development)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Styling:** Modern dark theme with CSS variables

## License

Educational use. Not for production security-critical applications without review.

## Educational Disclaimer

This tool is for learning cryptography concepts. Classic ciphers are **not secure**. For real security, use AES-GCM or consult security professionals.

---

🔐 **Encrypt. Learn. Experiment.**

Built with ❤️ for cryptography enthusiasts.
