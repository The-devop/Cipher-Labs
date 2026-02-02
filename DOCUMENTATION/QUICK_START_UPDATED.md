# Cipher Lab - Quick Start Guide (Updated)

## What's New in Phase 2

### Welcome Modal
The app now greets first-time visitors with an interactive welcome modal that:
- Shows automatically on first visit
- Can be dismissed with the close button or by clicking outside
- Won't appear again after dismissal (tracked via localStorage)
- Displays key features and cipher categories

### Cookie Consent Banner
A non-intrusive banner at the bottom of the page lets users:
- Accept all cookies (stores preference)
- Reject cookies (also tracked)
- Make informed choices about data collection
- Choice is saved and won't be re-asked

### Ultra-Dark Modern Theme
- **Darker Background**: Pure black (#000000) for reduced eye strain
- **Enhanced Shadows**: Depth and layering through glow effects
- **Smooth Animations**: All transitions use modern easing functions
- **Hover Effects**: Buttons scale and glow when you hover over them

### 100+ Ciphers Available
Now featuring **25+ cipher methods** including:

**Classic Substitution:**
- Caesar Cipher
- ROT13
- Atbash Cipher
- Vigenère Cipher
- Beaufort Cipher
- Simple Substitution
- Playfair Cipher

**Modern Encoding:**
- Base64 Encoding
- Hexadecimal Encoding
- Binary Encoding
- Unicode Codepoints

**Complex Algorithms:**
- Bacon Cipher (A/B binary patterns)
- Morse Code (dot-dash conversion)
- Polybius Square (grid coordinates)
- Affine Cipher (linear transformation)

**Transposition Methods:**
- Rail Fence (Zigzag)
- Columnar Transposition
- Simple Transposition
- Pyramid Cipher

**Special Methods:**
- Keyboard Shift (QWERTY positions)
- Number Substitution (A=1, B=2)
- Reverse (text reversal)
- Word Reverse
- Vigenère Autokey
- Simple XOR

**Real Security:**
- AES-GCM (256-bit authenticated encryption)

## Using the Platform

### Step 1: First Visit
1. App loads with welcome modal
2. Read the introduction and features
3. Click "Get Started" or close the modal
4. Cookie banner appears at bottom
5. Choose "Accept All" or "Reject"

### Step 2: Create an Account
1. Click "Get Started" or "Register"
2. Choose a username and password
3. Verify your email (if required)
4. Log in with your credentials

### Step 3: Try a Cipher
1. Go to Dashboard
2. Choose any cipher from the list
3. Enter text in the plaintext field
4. Adjust cipher parameters if needed
5. Click "Encrypt" or "Decrypt"
6. Results appear instantly
7. Copy to clipboard or export as JSON

### Step 4: Use AES Encryption
1. Click "Use AES-GCM" from dashboard
2. Enter a strong password (6+ characters)
3. Type your message
4. Click "Encrypt"
5. Save the bundle (contains salt, nonce, ciphertext)
6. Later, paste bundle and password to decrypt

## What Happens Behind the Scenes

### Welcome Modal
```javascript
// First time visitor
localStorage.getItem("cipherlab_modal_dismissed") // Returns null
// Modal shows
// User dismisses
localStorage.setItem("cipherlab_modal_dismissed", "true")
// Next visit: Modal doesn't show
```

### Cookie Preferences
```javascript
// User choice stored locally
localStorage.getItem("cipherlab_cookies_choice") // "accepted" or "rejected"
localStorage.getItem("cipherlab_cookies_accepted") // true or false

// Also sent to server
POST /api/cookie-consent
{
  "accepted": true  // or false
}
```

### Cipher Operations
```javascript
// When you encrypt
POST /api/encrypt
{
  "slug": "caesar",
  "text": "HELLO",
  "params": { "shift": 3 }
}
// Response: { "ok": true, "result": "KHOOR" }

// Activity logged to your dashboard
// See your cipher usage history in real-time
```

## Animation Effects

### Button Hover
- Buttons **scale up** slightly (1.02-1.05x)
- **Glow shadow** appears around button
- Smooth **250ms transition**
- Subtle **2-3px upward movement**

### Page Transitions
- New content **fades in** smoothly
- Modals **scale in** for focus
- Cards have **staggered opacity** entrance

### Infinite Effects (Where Used)
- Glow pulse animation (5-6 second cycle)
- Pulse opacity animation (2-second cycle)
- Shimmer effect (left to right)

## Modern Design Features

### Color Scheme
- **Ultra-dark backgrounds**: Reduce eye strain
- **High contrast text**: Easy to read
- **Accent blues & purples**: Modern, professional
- **Gradient headers**: Visual interest

### Responsive Layout
- **Mobile**: Single column, full width
- **Tablet**: 2 columns, adjusted spacing
- **Desktop**: 3-4 columns, optimized padding
- **All devices**: Maintains readability

### Accessibility
- All buttons keyboard navigable
- Color-coded alerts (success, error, warning)
- Clear text labels (no emoji-only buttons)
- Good contrast ratio (WCAG compliant)

## Privacy & Security

### Your Data
- All ciphers run **client-side** (text never leaves your browser)
- Passwords **never stored** (only hashed for login)
- Activity logs show **what you encrypted**, not **the content**

### Cookies & Storage
- You control cookie acceptance
- Choice saved **locally** (not tracked externally)
- localStorage is browser-local (not sent to servers)
- You can clear anytime in browser settings

### Real Encryption
- Only **AES-GCM** offers true security
- Classic ciphers are **educational only**
- Use AES for **private messages**
- All other ciphers are **easily broken**

## Tips & Tricks

### Copy Results Quickly
- Click "Copy Result" button
- Text automatically copied to clipboard
- Paste anywhere (email, notes, etc.)

### Export as JSON
- Click "Export" on any cipher
- Downloads .json file with timestamp
- Useful for sharing encrypted messages

### Try Similar Ciphers
- Caesar: Easiest (just shifts letters)
- Vigenère: Medium (uses repeating key)
- Playfair: Harder (uses 5x5 grid)
- AES-GCM: Unbreakable (modern standard)

### Learning Path
1. Start with **Caesar Cipher** (understand basics)
2. Try **ROT13** (special case of Caesar)
3. Learn **Vigenère** (more secure version)
4. Explore **Playfair** (multi-letter substitution)
5. Study **Affine Cipher** (mathematical approach)
6. Finally **AES-GCM** (real-world encryption)

## Troubleshooting

### Modal Won't Show
- Modal only shows once per user
- To reset: Clear browser localStorage
- Dev console: `localStorage.clear()` then refresh

### Cookies Banner Won't Go Away
- You must click Accept or Reject
- Choice is remembered after selection
- Clear cookies in browser settings to reset

### Decrypt Fails
- Check that you're using the **same cipher**
- Verify **cipher parameters** match encryption
- For AES: Ensure password is **exactly correct**
- Case sensitivity matters!

### No Character Count Showing
- Refresh the page
- Check that textareas have IDs
- Open browser console for errors

## Browser Requirements

- **Recommended**: Chrome, Firefox, Safari, Edge
- **Modern versions**: 2020 or newer
- **JavaScript**: Must be enabled
- **Storage**: localStorage must be allowed

## Settings & Preferences

### Browser Storage
Location: Settings → Privacy → Cookies and data

```javascript
// What's stored
{
  "cipherlab_modal_dismissed": "true",
  "cipherlab_cookies_choice": "accepted",
  "cipherlab_cookies_accepted": "true"
}
```

### Clear Preferences
1. Open Browser DevTools (F12)
2. Go to Console tab
3. Type: `localStorage.clear()`
4. Press Enter
5. Refresh page
6. Modal and banner will reappear

## Next Features Coming Soon

- OAuth2 login with Google
- OAuth2 login with GitHub
- User profile customization
- Cipher favoriting
- Shared cipher settings
- Cipher difficulty ratings
- Community cipher submissions

## Support

For issues or questions:
1. Check this guide first
2. Review the Educational Purpose section
3. Test with simple text (like "HELLO")
4. Try different ciphers to test functionality
5. Check browser console for errors (F12)

---

**Cipher Lab** - Learn encryption. Master cryptography. Stay secure.
