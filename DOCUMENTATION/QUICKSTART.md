# 🔐 Cipher Lab - Quick Start

## Installation (Windows)

### 1. Navigate to the project directory
```powershell
cd f:\PPP\ciphersite
```

### 2. Install Python dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run the application
```powershell
python app.py
```

You should see:
```
WARNING in app.runserver: This is a development server. Do not use it in production.
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### 4. Open in browser
Navigate to: **http://localhost:5000**

## 🚀 Features

### 7 Classic Ciphers (Educational)
- **Caesar** - Fixed shift cipher
- **ROT13** - Caesar with shift=13
- **Atbash** - Mirror alphabet (A↔Z)
- **Vigenère** - Repeating key polyalphabetic
- **Beaufort** - Reciprocal Vigenère
- **Substitution** - Full alphabet mapping (26!)
- **Rail Fence** - Zigzag transposition

### Modern Encryption
- **AES-256-GCM** - Real authenticated encryption
- **Scrypt KDF** - Password-based key derivation
- **Random salt & nonce** - Each encryption is unique

### User System
- ✅ Registration & login
- ✅ Activity tracking
- ✅ User dashboard
- ✅ Admin panel

### Beautiful Responsive UI
- 📱 Perfect on mobile phones
- 📱 Perfect on tablets
- 💻 Perfect on laptops
- 🖥️ Perfect on monitors
- 🎨 Modern dark theme
- ⚡ Smooth animations

## 🔐 Default Admin Account

```
Username: admin
Password: admin123
```

⚠️ Change these immediately in production!

## 📁 Project Files

- `app.py` - Flask application with all routes
- `models.py` - Database models (User, Cipher, Logs)
- `crypto_core.py` - All cipher implementations
- `config.py` - Configuration (database, sessions)
- `requirements.txt` - Python dependencies
- `templates/` - HTML templates
- `static/` - CSS & JavaScript
- `instance/` - Database directory (auto-created)

## 🔑 Key Features

### For Users
1. **Register** - Create free account
2. **Learn** - Try all classic ciphers
3. **Practice** - Encrypt/decrypt messages
4. **Encrypt** - Use AES for real security
5. **Track** - See your activity log

### For Admins
1. **Manage users** - Promote/demote/delete
2. **Manage ciphers** - Create new cipher definitions
3. **View logs** - Track admin actions
4. **View stats** - See which ciphers are used

## 🛡️ Security Notes

✅ **Implemented:**
- Password hashing (pbkdf2:sha256)
- Secure session cookies
- SQL injection prevention
- CSRF protection via Flask-Login
- AES-GCM authentication

⚠️ **For Production:**
- Change SECRET_KEY
- Change ADMIN_PASSWORD
- Use PostgreSQL (not SQLite)
- Enable HTTPS
- Add rate limiting
- Use production WSGI server (Gunicorn)

## 🎓 Educational Purpose

**Classic ciphers are NOT secure.** They're for:
- Learning cryptography concepts
- Understanding cipher mechanics
- Casual, non-sensitive messages

**For real encryption, use AES-GCM.**

## 💡 Tips

- Character count updates in real-time
- Copy buttons save to clipboard
- Export results as JSON files
- Bundle JSON for AES can be saved/shared
- Admin can create custom cipher "cards"

## 🐛 Troubleshooting

### Port 5000 already in use?
Change in `app.py`:
```python
app.run(debug=True, host="0.0.0.0", port=5001)  # Try 5001, 5002, etc
```

### Database errors?
Delete `instance/cipherlab.sqlite3` and restart app.

### Import errors?
```powershell
pip install -r requirements.txt --upgrade
```

## 📊 Database

SQLite database with tables:
- **users** - User accounts
- **cipher_definitions** - Built-in & custom ciphers
- **custom_ciphers** - User-created ciphers
- **activity_logs** - User encryption/decryption history
- **admin_logs** - Admin actions

Auto-created on first run.

## 🎯 Next Steps

1. ✅ Run the app
2. ✅ Create an account
3. ✅ Try the ciphers
4. ✅ Use AES encryption
5. ✅ Check activity logs
6. ✅ (If admin) Manage users & ciphers

## 📚 Learn More

See **README.md** for:
- Cipher details
- API endpoints
- Security considerations
- Deployment guide

---

**Built with ❤️ for cryptography learners.**

Happy encrypting! 🔐
