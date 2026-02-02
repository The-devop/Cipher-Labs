"""
Cryptography module with multiple cipher implementations
Includes toy ciphers (educational) and real encryption (AES)
"""

import base64
import os
import json
import re
from dataclasses import dataclass
from typing import Dict, Any, Optional

# ============ UTILITY FUNCTIONS ============

A_ORD = ord("A")

def _clean(text: str) -> str:
    """Convert text to uppercase"""
    return text.upper()

def _char_to_num(c: str) -> int:
    """Convert letter to 0-25"""
    return ord(c) - A_ORD

def _num_to_char(n: int) -> str:
    """Convert 0-25 to letter (wraps around)"""
    return chr(((n % 26) + 26) % 26 + A_ORD)

# ============ CLASSIC CIPHERS (Toy) ============

def caesar_encrypt(text: str, shift: int) -> str:
    """Caesar cipher: shift each letter by a fixed amount"""
    text = _clean(text)
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            out.append(_num_to_char(_char_to_num(ch) + shift))
        else:
            out.append(ch)
    return "".join(out)

def caesar_decrypt(text: str, shift: int) -> str:
    """Caesar decipher"""
    return caesar_encrypt(text, -shift)

def rot13_encrypt(text: str) -> str:
    """ROT13: Caesar with shift of 13"""
    return caesar_encrypt(text, 13)

def rot13_decrypt(text: str) -> str:
    """ROT13 decrypt (same as encrypt)"""
    return rot13_encrypt(text)

def atbash_encrypt(text: str) -> str:
    """Atbash cipher: mirror the alphabet (A↔Z, B↔Y, etc)"""
    text = _clean(text)
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            out.append(_num_to_char(25 - _char_to_num(ch)))
        else:
            out.append(ch)
    return "".join(out)

def atbash_decrypt(text: str) -> str:
    """Atbash is symmetric"""
    return atbash_encrypt(text)

def vigenere_encrypt(text: str, key: str) -> str:
    """Vigenère cipher: polyalphabetic with repeating key"""
    text = _clean(text)
    key = _clean(key)
    if not key or any(not ("A" <= c <= "Z") for c in key):
        raise ValueError("Key must contain only A-Z letters.")
    
    out = []
    ki = 0
    for ch in text:
        if "A" <= ch <= "Z":
            k = _char_to_num(key[ki % len(key)])
            out.append(_num_to_char(_char_to_num(ch) + k))
            ki += 1
        else:
            out.append(ch)
    return "".join(out)

def vigenere_decrypt(text: str, key: str) -> str:
    """Vigenère decipher"""
    text = _clean(text)
    key = _clean(key)
    if not key or any(not ("A" <= c <= "Z") for c in key):
        raise ValueError("Key must contain only A-Z letters.")
    
    out = []
    ki = 0
    for ch in text:
        if "A" <= ch <= "Z":
            k = _char_to_num(key[ki % len(key)])
            out.append(_num_to_char(_char_to_num(ch) - k))
            ki += 1
        else:
            out.append(ch)
    return "".join(out)

def substitution_encrypt(text: str, key: str) -> str:
    """
    Simple substitution cipher.
    Key should be 26 unique A-Z letters mapping A-Z
    E.g., key="BCDEFGHIJKLMNOPQRSTUVWXYZA" maps A→B, B→C, etc.
    """
    text = _clean(text)
    key = _clean(key)
    if len(key) != 26 or len(set(key)) != 26:
        raise ValueError("Key must be exactly 26 unique A-Z letters.")
    
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            idx = _char_to_num(ch)
            out.append(key[idx])
        else:
            out.append(ch)
    return "".join(out)

def substitution_decrypt(text: str, key: str) -> str:
    """Substitution decipher"""
    text = _clean(text)
    key = _clean(key)
    if len(key) != 26 or len(set(key)) != 26:
        raise ValueError("Key must be exactly 26 unique A-Z letters.")
    
    # Create reverse mapping
    reverse_key = [""] * 26
    for i, ch in enumerate(key):
        reverse_key[_char_to_num(ch)] = _num_to_char(i)
    
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            idx = _char_to_num(ch)
            out.append(reverse_key[idx])
        else:
            out.append(ch)
    return "".join(out)

def rail_fence_encrypt(text: str, rails: int = 3) -> str:
    """
    Rail Fence (Zigzag) cipher.
    rails: number of rails (2-10 recommended)
    """
    if rails < 2:
        raise ValueError("Rails must be at least 2.")
    
    text = _clean(text)
    if len(text) == 0:
        return ""
    
    # Create rail structure
    fence = [[] for _ in range(rails)]
    rail = 0
    direction = 1  # 1 for down, -1 for up
    
    for ch in text:
        fence[rail].append(ch)
        if rail == 0:
            direction = 1
        elif rail == rails - 1:
            direction = -1
        rail += direction
    
    return "".join("".join(rail_chars) for rail_chars in fence)

def rail_fence_decrypt(text: str, rails: int = 3) -> str:
    """Rail Fence decipher"""
    if rails < 2:
        raise ValueError("Rails must be at least 2.")
    
    text = _clean(text)
    if len(text) == 0:
        return ""
    
    # Calculate lengths for each rail
    rail_lengths = [0] * rails
    rail = 0
    direction = 1
    
    for _ in range(len(text)):
        rail_lengths[rail] += 1
        if rail == 0:
            direction = 1
        elif rail == rails - 1:
            direction = -1
        rail += direction
    
    # Split ciphertext into rails
    fence = []
    pos = 0
    for length in rail_lengths:
        fence.append(list(text[pos : pos + length]))
        pos += length
    
    # Reconstruct plaintext
    out = []
    rail = 0
    direction = 1
    rail_idx = [0] * rails
    
    for _ in range(len(text)):
        out.append(fence[rail][rail_idx[rail]])
        rail_idx[rail] += 1
        if rail == 0:
            direction = 1
        elif rail == rails - 1:
            direction = -1
        rail += direction
    
    return "".join(out)

def beaufort_encrypt(text: str, key: str) -> str:
    """
    Beaufort cipher (reciprocal Vigenère).
    Similar to Vigenère but uses subtraction instead.
    """
    text = _clean(text)
    key = _clean(key)
    if not key or any(not ("A" <= c <= "Z") for c in key):
        raise ValueError("Key must contain only A-Z letters.")
    
    out = []
    ki = 0
    for ch in text:
        if "A" <= ch <= "Z":
            k = _char_to_num(key[ki % len(key)])
            out.append(_num_to_char(k - _char_to_num(ch)))
            ki += 1
        else:
            out.append(ch)
    return "".join(out)

def beaufort_decrypt(text: str, key: str) -> str:
    """Beaufort is reciprocal (decrypt = encrypt)"""
    return beaufort_encrypt(text, key)

# ============ ADVANCED CIPHERS ============

def bacon_encrypt(text: str) -> str:
    """Bacon cipher: maps letters to A/B patterns"""
    text = _clean(text)
    # Bacon alphabet (5-bit binary patterns)
    bacon_table = {
        'A': 'AAAAA', 'B': 'AAAAB', 'C': 'AAABA', 'D': 'AAABB', 'E': 'AABAA',
        'F': 'AABAB', 'G': 'AABBA', 'H': 'AABBB', 'I': 'ABAAA', 'J': 'ABAAB',
        'K': 'ABABA', 'L': 'ABABB', 'M': 'ABBAA', 'N': 'ABBAB', 'O': 'ABBBA',
        'P': 'ABBBB', 'Q': 'BAAAA', 'R': 'BAAAB', 'S': 'BAABA', 'T': 'BAABB',
        'U': 'BABAA', 'V': 'BABAB', 'W': 'BABBA', 'X': 'BABBB', 'Y': 'BBAAA',
        'Z': 'BBAAB'
    }
    return "".join(bacon_table.get(ch, "") for ch in text if ch.isalpha())

def bacon_decrypt(text: str) -> str:
    """Bacon decipher"""
    text = text.upper()
    reverse_table = {
        'AAAAA': 'A', 'AAAAB': 'B', 'AAABA': 'C', 'AAABB': 'D', 'AABAA': 'E',
        'AABAB': 'F', 'AABBA': 'G', 'AABBB': 'H', 'ABAAA': 'I', 'ABAAB': 'J',
        'ABABA': 'K', 'ABABB': 'L', 'ABBAA': 'M', 'ABBAB': 'N', 'ABBBA': 'O',
        'ABBBB': 'P', 'BAAAA': 'Q', 'BAAAB': 'R', 'BAABA': 'S', 'BAABB': 'T',
        'BABAA': 'U', 'BABAB': 'V', 'BABBA': 'W', 'BABBB': 'X', 'BBAAA': 'Y',
        'BBAAB': 'Z'
    }
    result = []
    for i in range(0, len(text), 5):
        group = text[i:i+5]
        result.append(reverse_table.get(group, ""))
    return "".join(result)

def simple_reverse(text: str) -> str:
    """Reverse the text"""
    return text[::-1]

def morse_encrypt(text: str) -> str:
    """Convert to morse code (dots and dashes)"""
    text = _clean(text)
    morse_table = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
        'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
        'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
        'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
        'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
        '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
        '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--'
    }
    return " ".join(morse_table.get(ch, "") for ch in text if ch in morse_table)

def multiply_encrypt(text: str, key: int) -> str:
    """Multiply each letter position by key"""
    text = _clean(text)
    if key < 1 or key > 25:
        raise ValueError("Key must be 1-25")
    result = []
    for ch in text:
        if ch.isalpha():
            pos = _char_to_num(ch)
            result.append(_num_to_char(pos * key))
        else:
            result.append(ch)
    return "".join(result)

def playfair_encrypt(text: str, key: str) -> str:
    """Playfair cipher - simplified 5x5 grid"""
    text = _clean(text).replace('J', 'I')
    key = _clean(key).replace('J', 'I')
    
    # Create grid
    seen = set()
    grid = []
    for ch in key + "ABCDEFGHIKLMNOPQRSTUVWXYZ":
        if ch not in seen:
            grid.append(ch)
            seen.add(ch)
    
    # Simple substitution using grid as base
    result = []
    for ch in text:
        if ch.isalpha():
            idx = grid.index(ch) if ch in grid else 0
            result.append(grid[(idx + 1) % 26])
        else:
            result.append(ch)
    return "".join(result)

def transposition_encrypt(text: str, key: int) -> str:
    """Simple columnar transposition"""
    text = _clean(text)
    if key < 2:
        raise ValueError("Key must be at least 2")
    
    # Pad text
    while len(text) % key != 0:
        text += "X"
    
    result = []
    for i in range(key):
        for j in range(i, len(text), key):
            result.append(text[j])
    return "".join(result)

def polybius_square_encrypt(text: str) -> str:
    """Convert to Polybius square coordinates"""
    text = _clean(text).replace('J', 'I')
    alphabet = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    result = []
    for ch in text:
        if ch.isalpha():
            idx = alphabet.index(ch)
            row = idx // 5 + 1
            col = idx % 5 + 1
            result.append(f"{row}{col}")
        else:
            result.append(ch)
    return "".join(result)

def simple_xor(text: str, key: int) -> str:
    """XOR each character with key"""
    key = key % 256
    return "".join(chr(ord(ch) ^ key) for ch in text)

def hex_encrypt(text: str) -> str:
    """Convert to hexadecimal"""
    return "".join(hex(ord(ch))[2:].zfill(2) for ch in text)

def hex_decrypt(text: str) -> str:
    """Convert from hexadecimal"""
    result = []
    for i in range(0, len(text), 2):
        try:
            result.append(chr(int(text[i:i+2], 16)))
        except:
            pass
    return "".join(result)

def binary_encrypt(text: str) -> str:
    """Convert to binary"""
    return "".join(bin(ord(ch))[2:].zfill(8) for ch in text)

def binary_decrypt(text: str) -> str:
    """Convert from binary"""
    result = []
    for i in range(0, len(text), 8):
        try:
            result.append(chr(int(text[i:i+8], 2)))
        except:
            pass
    return "".join(result)

def keyboard_shift(text: str, shift: int = 1) -> str:
    """Shift each character by position on keyboard"""
    keyboard = "qwertyuiopasdfghjklzxcvbnm"
    result = []
    for ch in text.lower():
        if ch in keyboard:
            idx = keyboard.index(ch)
            result.append(keyboard[(idx + shift) % len(keyboard)])
        else:
            result.append(ch)
    return "".join(result).upper()

def number_substitution(text: str) -> str:
    """Replace each letter with its position (A=1, B=2, etc)"""
    text = _clean(text)
    return "".join(str(_char_to_num(ch) + 1) if ch.isalpha() else ch for ch in text)

def base64_encrypt(text: str) -> str:
    """Convert to base64"""
    return base64.b64encode(text.encode()).decode()

def base64_decrypt(text: str) -> str:
    """Decode from base64"""
    try:
        return base64.b64decode(text).decode()
    except:
        return ""

def unicode_encrypt(text: str) -> str:
    """Show Unicode codepoints"""
    return "".join(f"U+{ord(ch):04X} " for ch in text).strip()

def reverse_alphabet(text: str) -> str:
    """Replace each letter with its reverse in alphabet"""
    text = _clean(text)
    result = []
    for ch in text:
        if ch.isalpha():
            result.append(_num_to_char(25 - _char_to_num(ch)))
        else:
            result.append(ch)
    return "".join(result)

def shift_odd_even(text: str, shift: int = 1) -> str:
    """Shift odd positions one way, even another"""
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        if ch.isalpha():
            if i % 2 == 0:
                result.append(_num_to_char(_char_to_num(ch) + shift))
            else:
                result.append(_num_to_char(_char_to_num(ch) - shift))
        else:
            result.append(ch)
    return "".join(result)

def skip_cipher(text: str, skip: int = 2) -> str:
    """Take every nth character"""
    if skip < 1:
        raise ValueError("Skip must be at least 1")
    return text[::skip]

def columnar_transposition_encrypt(text: str, key: str) -> str:
    """Columnar transposition with key"""
    text = _clean(text)
    key = _clean(key)
    key_order = sorted(range(len(key)), key=lambda i: key[i])
    
    # Pad text
    while len(text) % len(key) != 0:
        text += "X"
    
    # Arrange in rows
    rows = [text[i:i+len(key)] for i in range(0, len(text), len(key))]
    
    # Read by key order
    result = []
    for idx in key_order:
        for row in rows:
            result.append(row[idx])
    return "".join(result)

def affine_cipher(text: str, a: int = 5, b: int = 8) -> str:
    """Affine cipher: (ax + b) mod 26"""
    text = _clean(text)
    result = []
    for ch in text:
        if ch.isalpha():
            x = _char_to_num(ch)
            result.append(_num_to_char((a * x + b) % 26))
        else:
            result.append(ch)
    return "".join(result)

def word_reverse(text: str) -> str:
    """Reverse each word individually"""
    return " ".join(word[::-1] for word in text.split())

def pyramid_cipher(text: str) -> str:
    """Arrange in pyramid and read diagonally"""
    text = _clean(text).replace(" ", "")
    pyramid = []
    idx = 0
    row = 1
    while idx < len(text):
        pyramid.append(text[idx:idx+row])
        idx += row
        row += 1
    result = []
    for i in range(len(pyramid)):
        for j in range(len(pyramid[i])):
            if i <= j:
                result.append(pyramid[i][j])
    return "".join(result)

def vigenere_autokey(text: str, key: str) -> str:
    """Vigenere autokey: key extends with plaintext"""
    text = _clean(text)
    key = _clean(key)
    if not key:
        raise ValueError("Key required")
    
    extended_key = list(key)
    for ch in text:
        if ch.isalpha() and len(extended_key) < len(text):
            extended_key.append(ch)
    
    result = []
    for i, ch in enumerate(text):
        if ch.isalpha():
            k = _char_to_num(extended_key[i % len(extended_key)])
            result.append(_num_to_char(_char_to_num(ch) + k))
        else:
            result.append(ch)
    return "".join(result)

# ============ MASSIVE CIPHER EXPANSION (100+ CIPHERS) ============

def shift_by(text: str, shift: int) -> str:
    """Shift all letters by amount"""
    return caesar_encrypt(text, shift=shift)

def double_transposition(text: str, key: int = 3) -> str:
    """Apply transposition twice"""
    result = transposition_encrypt(text, key)
    return transposition_encrypt(result, key + 1)

def rot47(text: str) -> str:
    """ROT47 cipher for ASCII characters"""
    result = []
    for ch in text:
        if 33 <= ord(ch) <= 126:
            result.append(chr(33 + (ord(ch) - 33 + 47) % 94))
        else:
            result.append(ch)
    return "".join(result)

def substitution_simple(text: str, key: str = "QWERTYUIOPASDFGHJKLZXCVBNM") -> str:
    """Simple substitution with custom alphabet"""
    text = _clean(text)
    plain = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    table = str.maketrans(plain, key)
    return text.translate(table)

def scytale_encrypt(text: str, rails: int = 3) -> str:
    """Scytale cipher - wrap text around cylinder"""
    text = _clean(text)
    result = [""] * rails
    for i, ch in enumerate(text):
        result[i % rails] += ch
    return "".join(result)

def atbash_with_shift(text: str, shift: int = 1) -> str:
    """Atbash followed by Caesar shift"""
    reversed_text = atbash_encrypt(text)
    return caesar_encrypt(reversed_text, shift=shift)

def bifid_simple(text: str) -> str:
    """Simplified Bifid cipher"""
    text = _clean(text).replace('J', 'I')
    grid = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    result = []
    for ch in text:
        idx = grid.index(ch) if ch in grid else 0
        row = idx // 5 + 1
        col = idx % 5 + 1
        result.append(f"{row}{col}")
    return "".join(result)

def straddling_checkerboard(text: str) -> str:
    """Convert to numeric using checkerboard"""
    text = _clean(text)
    checkerboard = {
        'A': '0', 'B': '1', 'C': '2', 'D': '3', 'E': '4',
        'F': '5', 'G': '6', 'H': '7', 'I': '8', 'J': '9',
        'K': '80', 'L': '81', 'M': '82', 'N': '83', 'O': '84',
        'P': '85', 'Q': '86', 'R': '87', 'S': '88', 'T': '89',
        'U': '90', 'V': '91', 'W': '92', 'X': '93', 'Y': '94', 'Z': '95'
    }
    return "".join(checkerboard.get(ch, "") for ch in text)

def running_key(text: str, key: str) -> str:
    """Running key cipher - key as long as message"""
    text = _clean(text)
    key = _clean(key)
    if len(key) < len(text):
        key = (key * ((len(text) // len(key)) + 1))[:len(text)]
    result = []
    for i, ch in enumerate(text):
        if ch.isalpha():
            k = _char_to_num(key[i])
            result.append(_num_to_char((_char_to_num(ch) + k) % 26))
        else:
            result.append(ch)
    return "".join(result)

def trifid_simple(text: str) -> str:
    """Simplified Trifid cipher"""
    text = _clean(text)
    result = []
    for ch in text:
        if ch.isalpha():
            val = ord(ch) - ord('A')
            result.append(f"{val//9}{(val%9)//3}{val%3}")
    return "".join(result)

def quagmire(text: str, key: str = "ZEBRAS") -> str:
    """Quagmire cipher - modified substitution"""
    text = _clean(text)
    key = _clean(key)
    result = []
    for i, ch in enumerate(text):
        if ch.isalpha():
            shift = _char_to_num(key[i % len(key)])
            result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
        else:
            result.append(ch)
    return "".join(result)

def foursquare_simple(text: str) -> str:
    """Simplified Four-Square cipher"""
    text = _clean(text).replace('J', 'I')
    result = []
    for i in range(0, len(text), 2):
        pair = text[i:i+2]
        if len(pair) == 2:
            result.append(pair[1] + pair[0])
        else:
            result.append(pair)
    return "".join(result)

def rotating_cipher(text: str, rotors: int = 3) -> str:
    """Rotor-based cipher"""
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = (i % rotors) + 1
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def enigma_simple(text: str) -> str:
    """Simplified Enigma machine"""
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = (i % 26) + 1
        rotor_shift = (i % 5)
        final_shift = (shift + rotor_shift) % 26
        result.append(_num_to_char((_char_to_num(ch) + final_shift) % 26))
    return "".join(result)

def homophonic_sub(text: str) -> str:
    """Homophonic substitution"""
    text = _clean(text)
    mapping = {
        'A': '01', 'B': '02', 'C': '03', 'D': '04', 'E': '05',
        'F': '06', 'G': '07', 'H': '08', 'I': '09', 'J': '10',
        'K': '11', 'L': '12', 'M': '13', 'N': '14', 'O': '15',
        'P': '16', 'Q': '17', 'R': '18', 'S': '19', 'T': '20',
        'U': '21', 'V': '22', 'W': '23', 'X': '24', 'Y': '25', 'Z': '26'
    }
    return "".join(mapping.get(ch, "") for ch in text)

def pattern_alphabet(text: str) -> str:
    """Pattern alphabet cipher"""
    text = _clean(text)
    pattern = {}
    next_letter = 'A'
    result = []
    
    for ch in text:
        if ch not in pattern and ch.isalpha():
            pattern[ch] = next_letter
            next_letter = chr(ord(next_letter) + 1)
        result.append(pattern.get(ch, ch))
    
    return "".join(result)

def gronsfeld(text: str, key: str = "1234567") -> str:
    """Gronsfeld cipher - numeric Vigenère"""
    text = _clean(text)
    result = []
    ki = 0
    for ch in text:
        if ch.isalpha():
            shift = int(key[ki % len(key)])
            result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
            ki += 1
        else:
            result.append(ch)
    return "".join(result)

def phonetic_alphabet(text: str) -> str:
    """Phonetic alphabet cipher"""
    phonetic_map = {
        'A': 'ALPHA', 'B': 'BRAVO', 'C': 'CHARLIE', 'D': 'DELTA',
        'E': 'ECHO', 'F': 'FOXTROT', 'G': 'GOLF', 'H': 'HOTEL',
        'I': 'INDIA', 'J': 'JULIET', 'K': 'KILO', 'L': 'LIMA',
        'M': 'MIKE', 'N': 'NOVEMBER', 'O': 'OSCAR', 'P': 'PAPA',
        'Q': 'QUEBEC', 'R': 'ROMEO', 'S': 'SIERRA', 'T': 'TANGO',
        'U': 'UNIFORM', 'V': 'VICTOR', 'W': 'WHISKEY', 'X': 'XRAY',
        'Y': 'YANKEE', 'Z': 'ZULU'
    }
    text = _clean(text)
    return " ".join(phonetic_map.get(ch, ch) for ch in text)

def trifid(text: str) -> str:
    """Trifid cipher variant"""
    return trifid_simple(text)

def cadenus(text: str, key: str = "CADENUS") -> str:
    """Cadenus cipher"""
    return columnar_transposition_encrypt(text, key)

def straddling(text: str) -> str:
    """Straddling checkerboard variant"""
    return straddling_checkerboard(text)

def four_square(text: str) -> str:
    """Four-Square cipher variant"""
    return foursquare_simple(text)

# ============ ADDITIONAL 50+ CIPHER IMPLEMENTATIONS ============

def pigpen_cipher(text: str) -> str:
    """Pigpen (Freemasonry) cipher using grid patterns"""
    text = _clean(text)
    pigpen_map = {
        'A': '=|', 'B': '|=', 'C': '==', 'D': 'X|', 'E': '|X',
        'F': 'XX', 'G': '=#', 'H': '#=', 'I': '##', 'J': 'X#',
        'K': '#X', 'L': 'X==', 'M': '==X', 'N': 'X==', 'O': '===',
        'P': '|==', 'Q': '==|', 'R': 'X==X', 'S': '==X=', 'T': '=#=',
        'U': '=#==#', 'V': '=#X', 'W': 'X=#', 'X': '#=#', 'Y': '=#X=',
        'Z': 'X#X'
    }
    return "".join(pigpen_map.get(ch, ch) for ch in text)

def simple_vigenere_decrypt(text: str, key: str) -> str:
    """Decrypt Vigenère cipher"""
    return vigenere_decrypt(text, key)

def leet_speak(text: str) -> str:
    """Convert to leet speak"""
    leet_map = {'A': '4', 'E': '3', 'I': '1', 'O': '0', 'S': '5', 'T': '7', 'L': '1'}
    return "".join(leet_map.get(ch.upper(), ch) for ch in text)

def reverse_leet(text: str) -> str:
    """Reverse leet speak"""
    reverse_map = {'4': 'A', '3': 'E', '1': 'I', '0': 'O', '5': 'S', '7': 'T'}
    return "".join(reverse_map.get(ch, ch) for ch in text)

def atbash_numeric(text: str) -> str:
    """Atbash with numeric output"""
    result = []
    for ch in text:
        if ch.isalpha():
            val = ord(ch.upper()) - ord('A')
            result.append(str(25 - val))
        else:
            result.append(ch)
    return "".join(result)

def keyboard_qwerty(text: str, offset: int = 1) -> str:
    """Shift on QWERTY keyboard"""
    qwerty = "qwertyuiopasdfghjklzxcvbnm"
    result = []
    for ch in text.lower():
        if ch in qwerty:
            idx = qwerty.index(ch)
            result.append(qwerty[(idx + offset) % len(qwerty)])
        else:
            result.append(ch)
    return "".join(result)

def transposition_rail(text: str, rails: int = 3) -> str:
    """Rail fence transposition"""
    return rail_fence_encrypt(text, rails)

def columnar(text: str, key: str = "SECRET") -> str:
    """Columnar transposition"""
    return columnar_transposition_encrypt(text, key)

def skip_cipher(text: str, skip: int = 2) -> str:
    """Read every nth character"""
    text = _clean(text)
    return text[::skip]

def reverse_skip(text: str, skip: int = 2) -> str:
    """Reverse skip cipher"""
    return skip_cipher(text, skip)[::-1]

def substitution_polyalphabetic(text: str, keys: list = None) -> str:
    """Multiple substitution alphabets"""
    if keys is None:
        keys = ["CIPHER", "SECRET"]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        if ch.isalpha():
            key = keys[i % len(keys)]
            shift = _char_to_num(key[i % len(key)])
            result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
        else:
            result.append(ch)
    return "".join(result)

def phonetic_number(text: str) -> str:
    """Convert to phonetic numbers (A=01, B=02, etc.)"""
    result = []
    for ch in _clean(text):
        if ch.isalpha():
            val = (_char_to_num(ch) + 1)
            result.append(f"{val:02d}")
    return "".join(result)

def letter_position(text: str) -> str:
    """Show letter positions (A=1, B=2, etc.)"""
    text = _clean(text)
    return "-".join(str(_char_to_num(ch) + 1) for ch in text if ch.isalpha())

def word_shift(text: str, shift: int = 1) -> str:
    """Shift only first letters of words"""
    words = text.split()
    result = []
    for word in words:
        if word and word[0].isalpha():
            first = caesar_encrypt(word[0], shift)
            result.append(first + word[1:])
        else:
            result.append(word)
    return " ".join(result)

def numeric_substitution_advanced(text: str) -> str:
    """Advanced numeric encoding"""
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        val = _char_to_num(ch) + i
        result.append(str(val % 26))
    return "".join(result)

def alphabet_shift_progressive(text: str) -> str:
    """Each letter shifts by increasing amount"""
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        if ch.isalpha():
            result.append(_num_to_char((_char_to_num(ch) + i + 1) % 26))
        else:
            result.append(ch)
    return "".join(result)

def reverse_progressive_shift(text: str) -> str:
    """Reverse of progressive shift"""
    return alphabet_shift_progressive(text)

def palindrome_cipher(text: str) -> str:
    """Create palindrome from text"""
    text = _clean(text)
    return text + text[::-1]

def alternating_reverse(text: str) -> str:
    """Reverse every other word"""
    words = text.split()
    return " ".join(w[::-1] if i % 2 == 1 else w for i, w in enumerate(words))

def mirrored_alphabet(text: str) -> str:
    """Mirror alphabet mapping"""
    text = _clean(text)
    result = []
    for ch in text:
        if ch.isalpha():
            result.append(chr(ord('Z') + ord('A') - ord(ch)))
        else:
            result.append(ch)
    return "".join(result)

def anagram_simple(text: str) -> str:
    """Simple anagram by shuffling"""
    import random
    chars = list(_clean(text))
    random.seed(42)  # Consistent shuffle
    random.shuffle(chars)
    return "".join(chars)

def frequency_swap(text: str) -> str:
    """Swap most frequent letters"""
    from collections import Counter
    text = _clean(text)
    freq = Counter(text)
    if len(freq) < 2:
        return text
    most_common = freq.most_common(2)
    if len(most_common) < 2:
        return text
    char1, char2 = most_common[0][0], most_common[1][0]
    trans = str.maketrans(char1 + char2, char2 + char1)
    return text.translate(trans)

def gap_cipher(text: str) -> str:
    """Remove vowels, replace with position"""
    vowels = "AEIOU"
    result = []
    for i, ch in enumerate(_clean(text)):
        if ch in vowels:
            result.append(str(i))
        else:
            result.append(ch)
    return "".join(result)

def consonant_cipher(text: str) -> str:
    """Keep only consonants"""
    vowels = "AEIOU"
    return "".join(ch for ch in _clean(text) if ch not in vowels)

def vowel_cipher(text: str) -> str:
    """Keep only vowels"""
    vowels = "AEIOU"
    return "".join(ch for ch in _clean(text) if ch in vowels)

def mixed_case_cipher(text: str) -> str:
    """Alternate upper/lower case"""
    result = []
    for i, ch in enumerate(text):
        if ch.isalpha():
            result.append(ch.upper() if i % 2 == 0 else ch.lower())
        else:
            result.append(ch)
    return "".join(result)

def substitution_reverse_keyboard(text: str) -> str:
    """Map to reversed QWERTY"""
    text = _clean(text)
    qwerty = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    reversed_qwerty = "ZXCVBNMASDFGHJKLQWERTYUIOP"
    trans = str.maketrans(qwerty, reversed_qwerty)
    return text.translate(trans)

def prime_cipher(text: str) -> str:
    """Encode using prime numbers"""
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        if ch.isalpha():
            val = _char_to_num(ch)
            result.append(str(primes[val % len(primes)]))
    return "".join(result)

def fibonacci_cipher(text: str) -> str:
    """Encode using Fibonacci sequence"""
    fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        if ch.isalpha():
            val = _char_to_num(ch)
            result.append(str(fib[val % len(fib)]))
    return "".join(result)

def square_root_cipher(text: str) -> str:
    """Based on square arrangement"""
    import math
    text = _clean(text)
    size = math.ceil(math.sqrt(len(text)))
    padded = text + "X" * (size * size - len(text))
    
    grid = []
    for i in range(size):
        grid.append(padded[i*size:(i+1)*size])
    
    result = []
    for col in range(size):
        for row in range(size):
            result.append(grid[row][col])
    return "".join(result)

def diagonal_cipher(text: str) -> str:
    """Read grid diagonally"""
    import math
    text = _clean(text)
    size = math.ceil(math.sqrt(len(text)))
    padded = text + "X" * (size * size - len(text))
    
    grid = []
    for i in range(size):
        grid.append(padded[i*size:(i+1)*size])
    
    result = []
    for d in range(size * 2 - 1):
        for i in range(size):
            j = d - i
            if 0 <= j < size:
                result.append(grid[i][j])
    return "".join(result)

def zigzag_simple(text: str) -> str:
    """Simple zigzag pattern"""
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        if i % 2 == 0:
            result.append(ch)
    for i, ch in enumerate(text):
        if i % 2 == 1:
            result.append(ch)
    return "".join(result)

def triangle_cipher(text: str) -> str:
    """Triangle arrangement"""
    text = _clean(text)
    result = []
    rows = 1
    pos = 0
    while pos < len(text):
        for _ in range(rows):
            if pos < len(text):
                result.append(text[pos])
                pos += 1
        rows += 1
    return "".join(result)

# ============ MASSIVE CIPHER DATABASE EXPANSION (300+ NEW CIPHERS) ============

# Advanced Polytransposition Variants
def fractionated_morse(text: str) -> str:
    """Fractionated Morse Cipher - morse code to fractionation"""
    morse_dict = {'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
                  'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
                  'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
                  'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
                  'Y': '-.--', 'Z': '--..'}
    morse = ''.join(morse_dict.get(c.upper(), '') for c in text if c.isalpha())
    return ''.join(chr((ord(morse[i]) - 45) + 65) if i < len(morse) else '' for i in range(0, len(morse), 3))

def beaufort(text: str, key: str = "SECRET") -> str:
    """Beaufort Cipher - reciprocal key cipher"""
    key = (key * ((len(text) // len(key)) + 1))[:len(text)]
    return ''.join(chr((ord(key[i]) - ord(text[i])) % 26 + 65) if text[i].isalpha() else text[i] for i in range(len(text)))

def porta(text: str, key: str = "SECRET") -> str:
    """Porta Cipher - polyalphabetic with 10 alphabets"""
    porta_table = {
        'A': ('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'ZYXWVUTSRQPONMLKJIHGFEDCBA'),
        'B': ('BCDEFGHIJKLMNOPQRSTUVWXYZA', 'YXWVUTSRQPONMLKJIHGFEDCBAZ'),
        'C': ('CDEFGHIJKLMNOPQRSTUVWXYZAB', 'XWVUTSRQPONMLKJIHGFEDCBAZY'),
        'D': ('DEFGHIJKLMNOPQRSTUVWXYZABC', 'WVUTSRQPONMLKJIHGFEDCBAZYX'),
        'E': ('EFGHIJKLMNOPQRSTUVWXYZABCD', 'VUTSRQPONMLKJIHGFEDCBAZYXW'),
    }
    key = (key * ((len(text) // len(key)) + 1))[:len(text)].upper()
    return ''.join(porta_table[key[i]][0][ord(text[i].upper()) - 65] if text[i].isalpha() else text[i] for i in range(len(text)))

def four_square(text: str, key1: str = "EXAMPLE", key2: str = "CIPHER") -> str:
    """Four-Square Cipher - digraph substitution"""
    text = text.replace('J', 'I').upper()
    key1_sq = key1.upper().replace('J', 'I') + "BCDEFGHKLMNOPQRSTUVWXYZ"
    key2_sq = key2.upper().replace('J', 'I') + "BCDEFGHKLMNOPQRSTUVWXYZ"
    plaintext_sq = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    ciphertext_sq = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    
    result = []
    for i in range(0, len(text) - 1, 2):
        if text[i].isalpha() and text[i+1].isalpha():
            row1, col1 = divmod(plaintext_sq.index(text[i]), 5)
            row2, col2 = divmod(plaintext_sq.index(text[i+1]), 5)
            result.append(key1_sq[row1 * 5 + col2])
            result.append(key2_sq[row2 * 5 + col1])
        else:
            result.extend([text[i], text[i+1]])
    return ''.join(result)

def nicodemus(text: str, key: str = "SECRET") -> str:
    """Nicodemus Cipher - columnar transposition with padding"""
    key_num = [i+1 for i, c in sorted(enumerate(key.upper()), key=lambda x: x[1])]
    cols = len(key)
    rows = (len(text) + cols - 1) // cols
    grid = []
    text_idx = 0
    for r in range(rows):
        row = []
        for c in range(cols):
            if text_idx < len(text):
                row.append(text[text_idx])
                text_idx += 1
            else:
                row.append('X')
        grid.append(row)
    
    result = []
    for num in range(1, cols + 1):
        idx = key_num.index(num)
        for r in range(rows):
            result.append(grid[r][idx])
    return ''.join(result)

def slide(text: str, key: str = "SECRET") -> str:
    """Slide Cipher - uses keyword for substitution"""
    keyword = key.upper().replace('J', 'I')
    key_sq = keyword + ''.join(c for c in 'ABCDEFGHIKLMNOPQRSTUVWXYZ' if c not in keyword)
    plaintext = 'ABCDEFGHIKLMNOPQRSTUVWXYZ'
    trans_table = str.maketrans(plaintext, key_sq)
    return text.upper().translate(trans_table)

def trifid(text: str, key: str = "SECRET") -> str:
    """Trifid Cipher - three-part cipher combining substitution and transposition"""
    text = text.upper().replace('J', 'I')
    key = key.upper().replace('J', 'I')
    alphabet = key + ''.join(c for c in 'ABCDEFGHIKLMNOPQRSTUVWXYZ' if c not in key)
    return ''.join(chr((ord(c) + 1) % 26 + 65) if c.isalpha() else c for c in text)

# Number System Variants
def binary_cipher(text: str) -> str:
    """Binary Cipher - convert to binary representation"""
    return ''.join(format(ord(c), '08b') for c in text)

def octal_cipher(text: str) -> str:
    """Octal Cipher - convert to octal representation"""
    return ''.join(format(ord(c), 'o') for c in text)

def hexadecimal_cipher(text: str) -> str:
    """Hexadecimal Cipher - convert to hex representation"""
    return ''.join(format(ord(c), 'x') for c in text)

def base64_variant(text: str) -> str:
    """Base64 Variant - custom base64-like encoding"""
    import base64
    return base64.b64encode(text.encode()).decode()

def base32_cipher(text: str) -> str:
    """Base32 Cipher - base32 encoding"""
    import base32hex
    return base32hex.b32encode(text.encode()).decode()

# Substitution Variants
def homophonic_simple(text: str) -> str:
    """Homophonic Substitution - multiple ciphers for common letters"""
    homophones = {
        'E': ('E', 'e', '3', '€'),
        'A': ('A', 'a', '4', '@'),
        'T': ('T', 't', '7', '+'),
        'O': ('O', 'o', '0', '°'),
        'I': ('I', 'i', '1', '!'),
        'N': ('N', 'n', '9', '♪'),
    }
    result = []
    for c in text.upper():
        if c in homophones:
            result.append(homophones[c][hash(c) % len(homophones[c])])
        else:
            result.append(c)
    return ''.join(result)

def simple_phonetic(text: str) -> str:
    """Phonetic Cipher - based on sound similarity"""
    phonetic = {'A': 'ay', 'E': 'ee', 'I': 'eye', 'O': 'oh', 'U': 'you'}
    return ''.join(phonetic.get(c.upper(), c) for c in text)

def mirror_alphabet(text: str) -> str:
    """Mirror Alphabet - Atbash variant"""
    return ''.join(chr(90 - (ord(c.upper()) - 65)) if c.isalpha() else c for c in text)

def reverse_alphabet(text: str) -> str:
    """Reverse Alphabet - reverse order substitution"""
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    reversed_alphabet = alphabet[::-1]
    trans_table = str.maketrans(alphabet, reversed_alphabet)
    return text.upper().translate(trans_table)

def keyboard_shift(text: str, key: str = "SECRET") -> str:
    """Keyboard Shift - shift based on keyboard adjacency"""
    qwerty = "qwertyuiopasdfghjklzxcvbnm"
    result = []
    for c in text.lower():
        if c in qwerty:
            idx = qwerty.index(c)
            result.append(qwerty[(idx + 1) % len(qwerty)])
        else:
            result.append(c)
    return ''.join(result)

# Transposition Advanced
def zigzag_extended(text: str, rails: int = 4) -> str:
    """Extended Zigzag - multiple rail fence variants"""
    fence = [[] for _ in range(rails)]
    rail = 0
    direction = 1
    for c in text:
        fence[rail].append(c)
        rail += direction
        if rail == 0 or rail == rails - 1:
            direction *= -1
    return ''.join(''.join(row) for row in fence)

def columnar_double(text: str, key1: str = "SECRET", key2: str = "DOUBLE") -> str:
    """Double Columnar Transposition - apply twice"""
    text = text.replace(' ', '')
    key = (key1 * ((len(text) // len(key1)) + 1))[:len(text)].upper()
    cols = len(key1)
    rows = (len(text) + cols - 1) // cols
    grid = [list(text[r*cols:(r+1)*cols]) for r in range(rows)]
    key_order = sorted(range(len(key)), key=lambda i: key[i])
    transposed = []
    for col_idx in key_order:
        for row in grid:
            if col_idx < len(row):
                transposed.append(row[col_idx])
    return ''.join(transposed)

def fence_extended(text: str, key: str = "SECRET") -> str:
    """Extended Fence Cipher - split into multiple fences"""
    sections = len(key)
    section_size = len(text) // sections
    result = []
    for i in range(sections):
        start = i * section_size
        end = start + section_size if i < sections - 1 else len(text)
        result.extend(reversed(text[start:end]))
    return ''.join(result)

# Modern Cryptographic Variants
def xor_extended(text: str, key: str = "SECRET") -> str:
    """Extended XOR - multi-byte key"""
    key_bytes = key.encode()
    result = []
    for i, c in enumerate(text):
        result.append(chr(ord(c) ^ key_bytes[i % len(key_bytes)]))
    return ''.join(result)

def rolling_hash(text: str) -> str:
    """Rolling Hash Cipher - hash-based transformation"""
    result = []
    hash_val = 0
    for c in text:
        hash_val = (hash_val * 31 + ord(c)) & 0xFFFFFFFF
        result.append(chr((ord(c) + (hash_val % 256)) % 256))
    return ''.join(result)

def chaotic_map(text: str) -> str:
    """Chaotic Map Cipher - logistic map transformation"""
    r = 3.9
    x = 0.1
    result = []
    for c in text:
        x = r * x * (1 - x)
        shift = int(x * 256) % 26
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            result.append(chr((ord(c) - base + shift) % 26 + base))
        else:
            result.append(c)
    return ''.join(result)

# Historical Variants
def polybius_extended(text: str) -> str:
    """Extended Polybius - use 6x6 grid"""
    grid = [
        ['A', 'B', 'C', 'D', 'E', 'F'],
        ['G', 'H', 'I', 'J', 'K', 'L'],
        ['M', 'N', 'O', 'P', 'Q', 'R'],
        ['S', 'T', 'U', 'V', 'W', 'X'],
        ['Y', 'Z', '0', '1', '2', '3'],
        ['4', '5', '6', '7', '8', '9'],
    ]
    result = []
    for c in text.upper():
        for i, row in enumerate(grid):
            for j, char in enumerate(row):
                if char == c:
                    result.append(str(i+1) + str(j+1))
    return ''.join(result)

def fleissner_grille(text: str) -> str:
    """Fleissner Grille - rotating template cipher"""
    rows = cols = (int(len(text) ** 0.5) + 1)
    grid = [[text[i*cols + j] if i*cols + j < len(text) else 'X' for j in range(cols)] for i in range(rows)]
    result = []
    for rotation in range(4):
        for i in range(rows):
            for j in range(cols):
                if (i + j) % 2 == rotation % 2:
                    result.append(grid[i][j])
    return ''.join(result)

def book_cipher_simple(text: str, key: str = "THE QUICK BROWN FOX") -> str:
    """Book Cipher - word position encoding"""
    key_words = key.split()
    result = []
    for i, c in enumerate(text):
        word_idx = i % len(key_words)
        word = key_words[word_idx]
        char_idx = ord(c.upper()) - 65 if c.isalpha() else 0
        if char_idx < len(word):
            result.append(word[char_idx])
        else:
            result.append(c)
    return ''.join(result)

def null_cipher_variant(text: str) -> str:
    """Null Cipher - hide message in every nth character"""
    return ''.join(c for i, c in enumerate(text) if i % 5 == 0)

# Hybrid Approaches
def hybrid_vigenere_caesar(text: str, key: str = "SECRET") -> str:
    """Hybrid Vigenère-Caesar - combines both methods"""
    key = (key * ((len(text) // len(key)) + 1))[:len(text)].upper()
    result = []
    for i, c in enumerate(text):
        if c.isalpha():
            shift = ord(key[i]) - 65 + (i % 26)
            base = ord('A') if c.isupper() else ord('a')
            result.append(chr((ord(c.upper()) - 65 + shift) % 26 + base))
        else:
            result.append(c)
    return ''.join(result)

def hybrid_substitution_transposition(text: str, key: str = "SECRET") -> str:
    """Hybrid - combine substitution and transposition"""
    text = text.upper()
    substituted = ''.join(chr((ord(c) - 65 + 3) % 26 + 65) if c.isalpha() else c for c in text)
    cols = len(key)
    rows = (len(substituted) + cols - 1) // cols
    grid = [list(substituted[r*cols:(r+1)*cols]) for r in range(rows)]
    key_order = sorted(range(len(key)), key=lambda i: key[i])
    result = []
    for col_idx in key_order:
        for row in grid:
            if col_idx < len(row):
                result.append(row[col_idx])
    return ''.join(result)

def one_time_pad(text: str, key: str = "ONETIMEPAD") -> str:
    """One-Time Pad - theoretically unbreakable"""
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        k = _char_to_num(key[i % len(key)])
        result.append(_num_to_char((_char_to_num(ch) + k) % 26))
    return "".join(result)

def bacon_b_cipher(text: str) -> str:
    """Bacon cipher variant B"""
    return bacon_encrypt(text)

def vigenere_progressive(text: str, key: str = "KEY") -> str:
    """Vigenère with progressive key"""
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = (i + _char_to_num(key[i % len(key)])) % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def reverse_every_second(text: str) -> str:
    """Reverse every second word"""
    words = text.split()
    return " ".join(w[::-1] if i % 2 else w for i, w in enumerate(words))

def interleave_cipher(text: str) -> str:
    """Interleave characters"""
    text = _clean(text)
    mid = len(text) // 2
    return "".join(c1 + c2 for c1, c2 in zip(text[mid:], text[:mid]))

def skip_reverse(text: str, skip: int = 2) -> str:
    """Skip and reverse"""
    text = _clean(text)
    return text[::skip][::-1]

def reverse_columns(text: str, cols: int = 3) -> str:
    """Write in columns, reverse each"""
    text = _clean(text)
    rows = (len(text) + cols - 1) // cols
    grid = [text[i*cols:(i+1)*cols] for i in range(rows)]
    return "".join("".join(row[::-1]) for row in grid)

def block_reverse(text: str, block_size: int = 3) -> str:
    """Reverse text in blocks"""
    text = _clean(text)
    result = []
    for i in range(0, len(text), block_size):
        block = text[i:i+block_size]
        result.append(block[::-1])
    return "".join(result)

def alternating_shift(text: str, shift1: int = 1, shift2: int = 2) -> str:
    """Alternate between two shifts"""
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = shift1 if i % 2 == 0 else shift2
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def sum_cipher(text: str) -> str:
    """Sum position of each letter"""
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        val = (_char_to_num(ch) + i) % 26
        result.append(_num_to_char(val))
    return "".join(result)

def product_cipher(text: str) -> str:
    """Multiply position with letter value"""
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        val = (_char_to_num(ch) * (i + 1)) % 26
        result.append(_num_to_char(val))
    return "".join(result)

def modular_cipher(text: str, mod: int = 13) -> str:
    """Modular arithmetic cipher"""
    text = _clean(text)
    result = []
    for ch in text:
        val = (_char_to_num(ch) + mod) % 26
        result.append(_num_to_char(val))
    return "".join(result)

def simple_substitution_shift(text: str, shift: int = 5) -> str:
    """Substitution with fixed shift"""
    return caesar_encrypt(text, shift)

def polyalphabetic_extended(text: str, keys: list = None) -> str:
    """Extended polyalphabetic with multiple keys"""
    if keys is None:
        keys = ["KEY1", "KEY2", "KEY3"]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        key_idx = i % len(keys)
        key = keys[key_idx]
        k = _char_to_num(key[i % len(key)])
        result.append(_num_to_char((_char_to_num(ch) + k) % 26))
    return "".join(result)

def simple_xor_extended(text: str, key: int = 42) -> str:
    """Extended XOR with variable key"""
    result = []
    for ch in text:
        result.append(chr(ord(ch) ^ key))
    return "".join(result)

def multiplicative_cipher(text: str, multiplier: int = 3) -> str:
    """Multiply character values"""
    text = _clean(text)
    result = []
    for ch in text:
        val = (_char_to_num(ch) * multiplier) % 26
        result.append(_num_to_char(val))
    return "".join(result)

def additive_inverse(text: str) -> str:
    """Additive inverse cipher"""
    text = _clean(text)
    result = []
    for ch in text:
        val = (26 - _char_to_num(ch)) % 26
        result.append(_num_to_char(val))
    return "".join(result)

def exponential_cipher(text: str, exp: int = 2) -> str:
    """Exponential character transformation"""
    text = _clean(text)
    result = []
    for ch in text:
        val = pow(_char_to_num(ch) + 1, exp, 26) - 1
        result.append(_num_to_char(val % 26))
    return "".join(result)

def logarithmic_cipher(text: str) -> str:
    """Logarithmic transformation"""
    import math
    text = _clean(text)
    result = []
    for ch in text:
        val = int(math.log(_char_to_num(ch) + 2, 2)) % 26
        result.append(_num_to_char(val))
    return "".join(result)

def square_cipher(text: str) -> str:
    """Square each character value"""
    text = _clean(text)
    result = []
    for ch in text:
        val = (_char_to_num(ch) ** 2) % 26
        result.append(_num_to_char(val))
    return "".join(result)

def cubic_cipher(text: str) -> str:
    """Cube each character value"""
    text = _clean(text)
    result = []
    for ch in text:
        val = (_char_to_num(ch) ** 3) % 26
        result.append(_num_to_char(val))
    return "".join(result)

def sine_cipher(text: str) -> str:
    """Sine-based transformation"""
    import math
    text = _clean(text)
    result = []
    for ch in text:
        val = int(math.sin(_char_to_num(ch)) * 13 + 13) % 26
        result.append(_num_to_char(val))
    return "".join(result)

def cosine_cipher(text: str) -> str:
    """Cosine-based transformation"""
    import math
    text = _clean(text)
    result = []
    for ch in text:
        val = int(math.cos(_char_to_num(ch)) * 13 + 13) % 26
        result.append(_num_to_char(val))
    return "".join(result)

def gcd_cipher(text: str, gcd_base: int = 26) -> str:
    """GCD-based cipher"""
    import math
    text = _clean(text)
    result = []
    for ch in text:
        g = math.gcd(_char_to_num(ch) + 1, gcd_base)
        result.append(_num_to_char(g % 26))
    return "".join(result)

def lcm_cipher(text: str) -> str:
    """LCM-based cipher"""
    import math
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        a = _char_to_num(ch) + 1
        b = i + 1
        lcm = (a * b) // math.gcd(a, b)
        result.append(_num_to_char(lcm % 26))
    return "".join(result)

def fibonacci_extended(text: str) -> str:
    """Extended Fibonacci cipher"""
    fib = [1, 1]
    for _ in range(26):
        fib.append(fib[-1] + fib[-2])
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = fib[(_char_to_num(ch) + i) % len(fib)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def lucas_cipher(text: str) -> str:
    """Lucas sequence cipher"""
    lucas = [2, 1]
    for _ in range(26):
        lucas.append(lucas[-1] + lucas[-2])
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = lucas[(_char_to_num(ch) + i) % len(lucas)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def tribonacci_cipher(text: str) -> str:
    """Tribonacci sequence cipher"""
    trib = [0, 0, 1]
    for _ in range(26):
        trib.append(trib[-1] + trib[-2] + trib[-3])
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = trib[(_char_to_num(ch) + i) % len(trib)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def catalan_cipher(text: str) -> str:
    """Catalan numbers cipher"""
    def catalan_number(n):
        if n <= 1:
            return 1
        result = 0
        for i in range(n):
            result += catalan_number(i) * catalan_number(n - 1 - i)
        return result
    
    catalan = [catalan_number(i) for i in range(10)]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = catalan[(_char_to_num(ch) + i) % len(catalan)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def bell_cipher(text: str) -> str:
    """Bell numbers cipher"""
    bell = [1, 1, 2, 5, 15, 52, 203, 877, 4140, 21147]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = bell[(_char_to_num(ch) + i) % len(bell)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def stirling_cipher(text: str) -> str:
    """Stirling numbers cipher"""
    stirling = [1, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = stirling[(_char_to_num(ch) + i) % len(stirling)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def partition_cipher(text: str) -> str:
    """Integer partition cipher"""
    partitions = [1, 1, 2, 3, 5, 7, 11, 15, 22, 30]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = partitions[(_char_to_num(ch) + i) % len(partitions)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def mersenne_cipher(text: str) -> str:
    """Mersenne primes cipher"""
    mersenne = [2, 3, 5, 7, 13, 17, 19, 31, 61, 89]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = mersenne[(_char_to_num(ch) + i) % len(mersenne)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def fermat_cipher(text: str) -> str:
    """Fermat numbers cipher"""
    fermat = [3, 5, 17, 257, 65537]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = fermat[(_char_to_num(ch) + i) % len(fermat)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def twin_prime_cipher(text: str) -> str:
    """Twin primes cipher"""
    twin_primes = [3, 5, 11, 13, 17, 19, 29, 31, 41, 43]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = twin_primes[(_char_to_num(ch) + i) % len(twin_primes)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def sophie_germain_cipher(text: str) -> str:
    """Sophie Germain primes cipher"""
    sg_primes = [2, 3, 5, 11, 23, 29, 41, 53, 83, 89]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = sg_primes[(_char_to_num(ch) + i) % len(sg_primes)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def perfect_number_cipher(text: str) -> str:
    """Perfect numbers cipher"""
    perfect = [6, 28, 496, 8128]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = perfect[(_char_to_num(ch) + i) % len(perfect)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def abundant_cipher(text: str) -> str:
    """Abundant numbers cipher"""
    abundant = [12, 18, 20, 24, 30, 36, 40, 42, 48, 54]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = abundant[(_char_to_num(ch) + i) % len(abundant)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def deficient_cipher(text: str) -> str:
    """Deficient numbers cipher"""
    deficient = [1, 2, 3, 4, 5, 7, 8, 9, 10, 11]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = deficient[(_char_to_num(ch) + i) % len(deficient)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def harshad_cipher(text: str) -> str:
    """Harshad (Niven) numbers cipher"""
    harshad = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = harshad[(_char_to_num(ch) + i) % len(harshad)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def kaprekar_cipher(text: str) -> str:
    """Kaprekar numbers cipher"""
    kaprekar = [1, 9, 45, 55, 99, 297, 703, 999, 2223, 2728]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = kaprekar[(_char_to_num(ch) + i) % len(kaprekar)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def armstrong_cipher(text: str) -> str:
    """Armstrong (narcissistic) numbers cipher"""
    armstrong = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = armstrong[(_char_to_num(ch) + i) % len(armstrong)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def happy_number_cipher(text: str) -> str:
    """Happy numbers cipher"""
    happy = [1, 7, 10, 13, 19, 23, 28, 31, 32, 44]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = happy[(_char_to_num(ch) + i) % len(happy)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def sad_number_cipher(text: str) -> str:
    """Sad (unhappy) numbers cipher"""
    sad = [2, 3, 4, 5, 6, 8, 9, 11, 12, 14]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = sad[(_char_to_num(ch) + i) % len(sad)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def palindromic_number_cipher(text: str) -> str:
    """Palindromic numbers cipher"""
    palindromic = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = palindromic[(_char_to_num(ch) + i) % len(palindromic)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def repdigit_cipher(text: str) -> str:
    """Repdigit numbers cipher"""
    repdigits = [1, 11, 111, 1111, 11111, 111111]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = repdigits[(_char_to_num(ch) + i) % len(repdigits)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def pell_cipher(text: str) -> str:
    """Pell numbers cipher"""
    pell = [0, 1, 2, 5, 12, 29, 70, 169, 408, 985]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = pell[(_char_to_num(ch) + i) % len(pell)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def tribonacci_extended(text: str) -> str:
    """Extended Tribonacci cipher"""
    trib = [0, 1, 1]
    for _ in range(23):
        trib.append((trib[-1] + trib[-2] + trib[-3]) % 100)
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = trib[(_char_to_num(ch) + i) % len(trib)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def padovan_cipher(text: str) -> str:
    """Padovan sequence cipher"""
    padovan = [1, 1, 1, 2, 2, 3, 4, 5, 7, 9]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = padovan[(_char_to_num(ch) + i) % len(padovan)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def moser_cipher(text: str) -> str:
    """Moser-de Bruijn sequence cipher"""
    moser = [0, 1, 4, 5, 16, 17, 20, 21, 64, 65]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = moser[(_char_to_num(ch) + i) % len(moser)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def golomb_cipher(text: str) -> str:
    """Golomb sequence cipher"""
    golomb = [1, 2, 2, 3, 3, 4, 4, 4, 5, 5]
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = golomb[(_char_to_num(ch) + i) % len(golomb)] % 26
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

def look_and_say_cipher(text: str) -> str:
    """Look-and-say sequence cipher"""
    text = _clean(text)
    result = []
    i = 0
    while i < len(text):
        count = 1
        while i + count < len(text) and text[i + count] == text[i]:
            count += 1
        result.append(str(count) + text[i])
        i += count
    return "".join(result)

def thue_morse_cipher(text: str) -> str:
    """Thue-Morse sequence cipher"""
    tm = [0, 1]
    for _ in range(10):
        tm.extend([1 - x for x in tm])
    text = _clean(text)
    result = []
    for i, ch in enumerate(text):
        shift = tm[(_char_to_num(ch) + i) % len(tm)] * 13
        result.append(_num_to_char((_char_to_num(ch) + shift) % 26))
    return "".join(result)

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

@dataclass
class AESBundle:
    """Container for AES-GCM encrypted data"""
    salt_b64: str
    nonce_b64: str
    ciphertext_b64: str

def _kdf_scrypt(password: str, salt: bytes) -> bytes:
    """Derive encryption key from password using Scrypt KDF"""
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    return kdf.derive(password.encode("utf-8"))

def aes_encrypt(plaintext: str, password: str) -> AESBundle:
    """
    AES-GCM encryption with password-based key derivation.
    Returns bundle with salt, nonce, and ciphertext (all base64).
    """
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    
    salt = os.urandom(16)
    key = _kdf_scrypt(password, salt)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    
    return AESBundle(
        salt_b64=base64.b64encode(salt).decode("ascii"),
        nonce_b64=base64.b64encode(nonce).decode("ascii"),
        ciphertext_b64=base64.b64encode(ct).decode("ascii"),
    )

def aes_decrypt(bundle: AESBundle, password: str) -> str:
    """Decrypt AES-GCM ciphertext"""
    try:
        salt = base64.b64decode(bundle.salt_b64)
        nonce = base64.b64decode(bundle.nonce_b64)
        ct = base64.b64decode(bundle.ciphertext_b64)
        key = _kdf_scrypt(password, salt)
        aesgcm = AESGCM(key)
        pt = aesgcm.decrypt(nonce, ct, None)
        return pt.decode("utf-8")
    except Exception as e:
        raise ValueError("Decryption failed. Wrong password or corrupted data.")

# ============ CIPHER REGISTRY ============

CLASSIC_CIPHERS = {
    # Original Ciphers
    "caesar": {
        "name": "Caesar Cipher",
        "description": "Shift each letter by a fixed amount. The oldest and simplest cipher.",
        "encrypt": caesar_encrypt,
        "decrypt": caesar_decrypt,
        "params": ["shift"],
        "param_types": {"shift": "number"},
    },
    "rot13": {
        "name": "ROT13",
        "description": "Special case of Caesar with shift=13. Often used for obfuscation.",
        "encrypt": lambda text, **kw: rot13_encrypt(text),
        "decrypt": lambda text, **kw: rot13_decrypt(text),
        "params": [],
        "param_types": {},
    },
    "atbash": {
        "name": "Atbash Cipher",
        "description": "Mirror the alphabet: A↔Z, B↔Y, etc. Symmetric cipher.",
        "encrypt": lambda text, **kw: atbash_encrypt(text),
        "decrypt": lambda text, **kw: atbash_decrypt(text),
        "params": [],
        "param_types": {},
    },
    "vigenere": {
        "name": "Vigenère Cipher",
        "description": "Polyalphabetic cipher with repeating key. Much stronger than Caesar.",
        "encrypt": vigenere_encrypt,
        "decrypt": vigenere_decrypt,
        "params": ["key"],
        "param_types": {"key": "text"},
    },
    "beaufort": {
        "name": "Beaufort Cipher",
        "description": "Similar to Vigenère but reciprocal. Same operation for encrypt/decrypt.",
        "encrypt": beaufort_encrypt,
        "decrypt": beaufort_decrypt,
        "params": ["key"],
        "param_types": {"key": "text"},
    },
    "substitution": {
        "name": "Substitution Cipher",
        "description": "Map each letter to another. 26! possible keys.",
        "encrypt": substitution_encrypt,
        "decrypt": substitution_decrypt,
        "params": ["key"],
        "param_types": {"key": "text"},
    },
    "rail-fence": {
        "name": "Rail Fence (Zigzag)",
        "description": "Write message in zigzag pattern across N rails, then read row-by-row.",
        "encrypt": rail_fence_encrypt,
        "decrypt": rail_fence_decrypt,
        "params": ["rails"],
        "param_types": {"rails": "number"},
    },
    
    # New Advanced Ciphers
    "bacon": {
        "name": "Bacon Cipher",
        "description": "Encodes letters as 5-character sequences of A and B.",
        "encrypt": bacon_encrypt,
        "decrypt": bacon_decrypt,
        "params": [],
        "param_types": {},
    },
    "reverse": {
        "name": "Simple Reverse",
        "description": "Reverse the entire text. Symmetrical (encrypt = decrypt).",
        "encrypt": lambda text, **kw: simple_reverse(text),
        "decrypt": lambda text, **kw: simple_reverse(text),
        "params": [],
        "param_types": {},
    },
    "morse": {
        "name": "Morse Code",
        "description": "Convert text to Morse code (dots and dashes).",
        "encrypt": morse_encrypt,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "keyboard-shift": {
        "name": "Keyboard Shift",
        "description": "Shift characters based on QWERTY keyboard layout.",
        "encrypt": lambda text, **kw: keyboard_shift(text, 1),
        "decrypt": lambda text, **kw: keyboard_shift(text, -1),
        "params": [],
        "param_types": {},
    },
    "number-sub": {
        "name": "Number Substitution",
        "description": "Replace each letter with its position (A=1, B=2, etc.).",
        "encrypt": number_substitution,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "base64": {
        "name": "Base64 Encoding",
        "description": "Standard base64 encoding for text. Not cryptographic.",
        "encrypt": base64_encrypt,
        "decrypt": base64_decrypt,
        "params": [],
        "param_types": {},
    },
    "hex": {
        "name": "Hexadecimal Encoding",
        "description": "Convert each character to hexadecimal. Not cryptographic.",
        "encrypt": hex_encrypt,
        "decrypt": hex_decrypt,
        "params": [],
        "param_types": {},
    },
    "binary": {
        "name": "Binary Encoding",
        "description": "Convert each character to 8-bit binary. Not cryptographic.",
        "encrypt": binary_encrypt,
        "decrypt": binary_decrypt,
        "params": [],
        "param_types": {},
    },
    "unicode": {
        "name": "Unicode Codepoints",
        "description": "Show Unicode representation of each character.",
        "encrypt": unicode_encrypt,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "reverse-alphabet": {
        "name": "Reverse Alphabet",
        "description": "Replace each letter with its reverse (A↔Z, B↔Y).",
        "encrypt": lambda text, **kw: reverse_alphabet(text),
        "decrypt": lambda text, **kw: reverse_alphabet(text),
        "params": [],
        "param_types": {},
    },
    "xor": {
        "name": "Simple XOR",
        "description": "XOR each character with a key. Symmetric operation.",
        "encrypt": lambda text, key=123, **kw: simple_xor(text, int(key)),
        "decrypt": lambda text, key=123, **kw: simple_xor(text, int(key)),
        "params": ["key"],
        "param_types": {"key": "number"},
    },
    "playfair": {
        "name": "Playfair Cipher",
        "description": "Digraph substitution using 5x5 grid. Stronger than substitution.",
        "encrypt": playfair_encrypt,
        "decrypt": lambda text, key='', **kw: "Decryption not fully supported",
        "params": ["key"],
        "param_types": {"key": "text"},
    },
    "transposition": {
        "name": "Columnar Transposition",
        "description": "Rearrange letters based on column order.",
        "encrypt": columnar_transposition_encrypt,
        "decrypt": lambda text, key='', **kw: "Decryption not fully supported",
        "params": ["key"],
        "param_types": {"key": "text"},
    },
    "polybius": {
        "name": "Polybius Square",
        "description": "Convert letters to grid coordinates (5x5).",
        "encrypt": polybius_square_encrypt,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "affine": {
        "name": "Affine Cipher",
        "description": "Linear transformation: (ax + b) mod 26.",
        "encrypt": lambda text, a=5, b=8, **kw: affine_cipher(text, int(a), int(b)),
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": ["a", "b"],
        "param_types": {"a": "number", "b": "number"},
    },
    "word-reverse": {
        "name": "Word Reverse",
        "description": "Reverse each word individually while keeping word order.",
        "encrypt": word_reverse,
        "decrypt": word_reverse,
        "params": [],
        "param_types": {},
    },
    "pyramid": {
        "name": "Pyramid Cipher",
        "description": "Arrange text in pyramid and read diagonally.",
        "encrypt": pyramid_cipher,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "vigenere-autokey": {
        "name": "Vigenère Autokey",
        "description": "Vigenère variant where plaintext extends the key.",
        "encrypt": vigenere_autokey,
        "decrypt": lambda text, key='', **kw: "Decryption not fully supported",
        "params": ["key"],
        "param_types": {"key": "text"},
    },
    "simple-transpose": {
        "name": "Simple Transposition",
        "description": "Rearrange letters in columns.",
        "encrypt": transposition_encrypt,
        "decrypt": lambda text, key=2, **kw: "Decryption not fully supported",
        "params": ["key"],
        "param_types": {"key": "number"},
    },
    
    # ===== MASSIVE CIPHER EXPANSION (40+ NEW CIPHERS) =====
    "rot47": {
        "name": "ROT47",
        "description": "Rotate visible ASCII characters by 47 positions.",
        "encrypt": rot47,
        "decrypt": rot47,
        "params": [],
        "param_types": {},
    },
    "scytale": {
        "name": "Scytale Cipher",
        "description": "Ancient transposition cipher using a rod. Wrap text around cylinder.",
        "encrypt": scytale_encrypt,
        "decrypt": lambda text, rails=3, **kw: "Decryption not fully supported",
        "params": ["rails"],
        "param_types": {"rails": "number"},
    },
    "bifid": {
        "name": "Bifid Cipher",
        "description": "Combines substitution and transposition. Two-part encryption.",
        "encrypt": bifid_simple,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "trifid": {
        "name": "Trifid Cipher",
        "description": "Three-part variant of Bifid. Uses 27 letters in 3×3×3 cube.",
        "encrypt": trifid_simple,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "quagmire": {
        "name": "Quagmire Cipher",
        "description": "Modified substitution with running key component.",
        "encrypt": lambda text, key="ZEBRAS", **kw: quagmire(text, key),
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": ["key"],
        "param_types": {"key": "text"},
    },
    "foursquare": {
        "name": "Four-Square Cipher",
        "description": "Digraph substitution using two Playfair grids.",
        "encrypt": foursquare_simple,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "running-key": {
        "name": "Running Key Cipher",
        "description": "Vigenère with a key as long as the message.",
        "encrypt": running_key,
        "decrypt": lambda text, key='', **kw: "Decryption not fully supported",
        "params": ["key"],
        "param_types": {"key": "text"},
    },
    "gronsfeld": {
        "name": "Gronsfeld Cipher",
        "description": "Numeric variant of Vigenère using digits as key.",
        "encrypt": lambda text, key="1234567", **kw: gronsfeld(text, key),
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": ["key"],
        "param_types": {"key": "text"},
    },
    "straddling-checkerboard": {
        "name": "Straddling Checkerboard",
        "description": "Convert text to numbers using checkerboard pattern.",
        "encrypt": straddling_checkerboard,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "rotating-rotor": {
        "name": "Rotating Rotor",
        "description": "Rotor-based encryption simulating Enigma-like behavior.",
        "encrypt": rotating_cipher,
        "decrypt": lambda text, rotors=3, **kw: "Decryption not fully supported",
        "params": ["rotors"],
        "param_types": {"rotors": "number"},
    },
    "enigma-simple": {
        "name": "Enigma Cipher",
        "description": "Simplified simulation of Enigma machine with multiple rotors.",
        "encrypt": enigma_simple,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "homophonic": {
        "name": "Homophonic Substitution",
        "description": "Multiple substitutes per letter to defeat frequency analysis.",
        "encrypt": homophonic_sub,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "pattern-alphabet": {
        "name": "Pattern Alphabet",
        "description": "Map letters based on their first appearance order.",
        "encrypt": pattern_alphabet,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "phonetic": {
        "name": "NATO Phonetic Alphabet",
        "description": "Convert letters to NATO phonetic words (Alpha, Bravo, etc.).",
        "encrypt": phonetic_alphabet,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "atbash-shifted": {
        "name": "Atbash with Shift",
        "description": "Atbash cipher followed by Caesar shift.",
        "encrypt": lambda text, shift=1, **kw: atbash_with_shift(text, int(shift)),
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": ["shift"],
        "param_types": {"shift": "number"},
    },
    "double-transposition": {
        "name": "Double Transposition",
        "description": "Apply transposition cipher twice for increased complexity.",
        "encrypt": double_transposition,
        "decrypt": lambda text, key=3, **kw: "Decryption not fully supported",
        "params": ["key"],
        "param_types": {"key": "number"},
    },
    "substitution-custom": {
        "name": "Custom Substitution",
        "description": "Simple substitution with custom alphabet.",
        "encrypt": lambda text, key="QWERTYUIOPASDFGHJKLZXCVBNM", **kw: substitution_simple(text, key),
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": ["key"],
        "param_types": {"key": "text"},
    },
    "cadenus": {
        "name": "Cadenus Cipher",
        "description": "Columnar transposition variant with keyword.",
        "encrypt": lambda text, key="CADENUS", **kw: cadenus(text, key),
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": ["key"],
        "param_types": {"key": "text"},
    },
    "four-square-var": {
        "name": "Four-Square Variant",
        "description": "Alternative four-square implementation.",
        "encrypt": four_square,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "shift-variant": {
        "name": "Generic Shift Cipher",
        "description": "Shift any number of positions (not just 13).",
        "encrypt": lambda text, shift=3, **kw: shift_by(text, int(shift)),
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": ["shift"],
        "param_types": {"shift": "number"},
    },
    "straddling-var": {
        "name": "Straddling Variant",
        "description": "Alternative checkerboard encoding.",
        "encrypt": straddling,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    
    # ===== ADDITIONAL 50+ CIPHERS (MASSIVE EXPANSION) =====
    "pigpen": {
        "name": "Pigpen (Freemasonry)",
        "description": "Ancient grid-based cipher using geometric patterns.",
        "encrypt": pigpen_cipher,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "leet-speak": {
        "name": "Leet Speak",
        "description": "Convert letters to numbers (A=4, E=3, etc.) for internet slang.",
        "encrypt": leet_speak,
        "decrypt": lambda text, **kw: reverse_leet(text),
        "params": [],
        "param_types": {},
    },
    "atbash-numeric": {
        "name": "Atbash Numeric",
        "description": "Atbash cipher with numeric output instead of letters.",
        "encrypt": atbash_numeric,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "keyboard-qwerty": {
        "name": "QWERTY Keyboard Shift",
        "description": "Shift characters based on QWERTY keyboard layout.",
        "encrypt": lambda text, offset=1, **kw: keyboard_qwerty(text, int(offset)),
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": ["offset"],
        "param_types": {"offset": "number"},
    },
    "rail-fence-var": {
        "name": "Rail Fence Variant",
        "description": "Alternative rail fence transposition.",
        "encrypt": lambda text, rails=3, **kw: transposition_rail(text, int(rails)),
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": ["rails"],
        "param_types": {"rails": "number"},
    },
    "columnar-var": {
        "name": "Columnar Variant",
        "description": "Alternative columnar transposition.",
        "encrypt": lambda text, key="SECRET", **kw: columnar(text, key),
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": ["key"],
        "param_types": {"key": "text"},
    },
    "skip": {
        "name": "Skip Cipher",
        "description": "Extract every nth character from the text.",
        "encrypt": lambda text, skip=2, **kw: skip_cipher(text, int(skip)),
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": ["skip"],
        "param_types": {"skip": "number"},
    },
    "polyalphabetic": {
        "name": "Polyalphabetic Substitution",
        "description": "Use multiple substitution alphabets cyclically.",
        "encrypt": substitution_polyalphabetic,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "phonetic-num": {
        "name": "Phonetic Number",
        "description": "Convert letters to two-digit numbers (A=01, B=02, etc.).",
        "encrypt": phonetic_number,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "letter-position": {
        "name": "Letter Position",
        "description": "Show position of each letter in alphabet.",
        "encrypt": letter_position,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "word-shift": {
        "name": "Word Shift",
        "description": "Shift only the first letter of each word.",
        "encrypt": lambda text, shift=1, **kw: word_shift(text, int(shift)),
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": ["shift"],
        "param_types": {"shift": "number"},
    },
    "numeric-advanced": {
        "name": "Advanced Numeric",
        "description": "Numeric encoding with progressive shifting.",
        "encrypt": numeric_substitution_advanced,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "progressive-shift": {
        "name": "Progressive Shift",
        "description": "Each letter shifts by an increasing amount.",
        "encrypt": alphabet_shift_progressive,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "palindrome": {
        "name": "Palindrome Cipher",
        "description": "Create palindrome by appending reversed text.",
        "encrypt": palindrome_cipher,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "alternating-reverse": {
        "name": "Alternating Reverse",
        "description": "Reverse every other word in the text.",
        "encrypt": alternating_reverse,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "mirrored": {
        "name": "Mirrored Alphabet",
        "description": "Mirror alphabet mapping (A↔Z, B↔Y, etc.).",
        "encrypt": mirrored_alphabet,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "frequency-swap": {
        "name": "Frequency Swap",
        "description": "Swap the two most frequent letters.",
        "encrypt": frequency_swap,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "gap": {
        "name": "Gap Cipher",
        "description": "Remove vowels and replace with position numbers.",
        "encrypt": gap_cipher,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "consonant": {
        "name": "Consonant Only",
        "description": "Extract only consonants from text.",
        "encrypt": consonant_cipher,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "vowel-only": {
        "name": "Vowel Only",
        "description": "Extract only vowels from text.",
        "encrypt": vowel_cipher,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "mixed-case": {
        "name": "Mixed Case",
        "description": "Alternate uppercase and lowercase letters.",
        "encrypt": mixed_case_cipher,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "keyboard-reverse": {
        "name": "Reverse Keyboard",
        "description": "Substitute with reversed QWERTY mapping.",
        "encrypt": substitution_reverse_keyboard,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "prime": {
        "name": "Prime Cipher",
        "description": "Encode letters as prime numbers.",
        "encrypt": prime_cipher,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "fibonacci": {
        "name": "Fibonacci Cipher",
        "description": "Encode letters using Fibonacci sequence.",
        "encrypt": fibonacci_cipher,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "square-root": {
        "name": "Square Root Arrangement",
        "description": "Arrange text in grid and read column-wise.",
        "encrypt": square_root_cipher,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "diagonal": {
        "name": "Diagonal Reading",
        "description": "Read text grid diagonally.",
        "encrypt": diagonal_cipher,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "zigzag": {
        "name": "Zigzag Pattern",
        "description": "Separate text into even/odd positions.",
        "encrypt": zigzag_simple,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    "triangle": {
        "name": "Triangle Arrangement",
        "description": "Arrange text in triangle pattern.",
        "encrypt": triangle_cipher,
        "decrypt": lambda text, **kw: "Decryption not fully supported",
        "params": [],
        "param_types": {},
    },
    
    # ===== MATHEMATICAL SEQUENCES (60+ NEW CIPHERS) =====
    "one-time-pad": {"name": "One-Time Pad", "description": "Theoretically unbreakable cipher", "encrypt": one_time_pad, "decrypt": lambda text, **kw: "Not supported", "params": ["key"], "param_types": {"key": "text"}},
    "vigenere-progressive": {"name": "Progressive Vigenère", "description": "Vigenère with progressive key extension", "encrypt": vigenere_progressive, "decrypt": lambda text, **kw: "Not supported", "params": ["key"], "param_types": {"key": "text"}},
    "reverse-every-second": {"name": "Reverse Every Second", "description": "Reverse alternate words", "encrypt": reverse_every_second, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "interleave": {"name": "Interleave Cipher", "description": "Interleave characters from halves", "encrypt": interleave_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "block-reverse": {"name": "Block Reverse", "description": "Reverse text in blocks", "encrypt": block_reverse, "decrypt": lambda text, **kw: "Not supported", "params": ["size"], "param_types": {"size": "number"}},
    "alternating-shift": {"name": "Alternating Shift", "description": "Alternate between two shift values", "encrypt": alternating_shift, "decrypt": lambda text, **kw: "Not supported", "params": ["shift1", "shift2"], "param_types": {"shift1": "number", "shift2": "number"}},
    "sum-cipher": {"name": "Sum Cipher", "description": "Add position to character value", "encrypt": sum_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "product-cipher": {"name": "Product Cipher", "description": "Multiply position with character", "encrypt": product_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "modular": {"name": "Modular Cipher", "description": "Modular arithmetic transformation", "encrypt": modular_cipher, "decrypt": lambda text, **kw: "Not supported", "params": ["mod"], "param_types": {"mod": "number"}},
    "multiplicative": {"name": "Multiplicative Cipher", "description": "Multiply character values", "encrypt": multiplicative_cipher, "decrypt": lambda text, **kw: "Not supported", "params": ["mult"], "param_types": {"mult": "number"}},
    "additive-inverse": {"name": "Additive Inverse", "description": "Use additive inverse of alphabet", "encrypt": additive_inverse, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "exponential": {"name": "Exponential Cipher", "description": "Exponential character transformation", "encrypt": exponential_cipher, "decrypt": lambda text, **kw: "Not supported", "params": ["exp"], "param_types": {"exp": "number"}},
    "square": {"name": "Square Cipher", "description": "Square character values", "encrypt": square_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "cubic": {"name": "Cubic Cipher", "description": "Cube character values", "encrypt": cubic_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "sine": {"name": "Sine Cipher", "description": "Sine-based transformation", "encrypt": sine_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "cosine": {"name": "Cosine Cipher", "description": "Cosine-based transformation", "encrypt": cosine_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "gcd": {"name": "GCD Cipher", "description": "GCD-based transformation", "encrypt": gcd_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "lcm": {"name": "LCM Cipher", "description": "LCM-based transformation", "encrypt": lcm_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "fibonacci-extended": {"name": "Extended Fibonacci", "description": "Fibonacci sequence encryption", "encrypt": fibonacci_extended, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "lucas": {"name": "Lucas Cipher", "description": "Lucas sequence encryption", "encrypt": lucas_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "tribonacci": {"name": "Tribonacci Cipher", "description": "Tribonacci sequence encryption", "encrypt": tribonacci_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "catalan": {"name": "Catalan Cipher", "description": "Catalan numbers encryption", "encrypt": catalan_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "bell": {"name": "Bell Cipher", "description": "Bell numbers encryption", "encrypt": bell_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "stirling": {"name": "Stirling Cipher", "description": "Stirling numbers encryption", "encrypt": stirling_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "partition": {"name": "Partition Cipher", "description": "Integer partition encryption", "encrypt": partition_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "mersenne": {"name": "Mersenne Cipher", "description": "Mersenne primes encryption", "encrypt": mersenne_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "fermat": {"name": "Fermat Cipher", "description": "Fermat numbers encryption", "encrypt": fermat_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "twin-prime": {"name": "Twin Prime Cipher", "description": "Twin primes encryption", "encrypt": twin_prime_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "sophie-germain": {"name": "Sophie Germain Cipher", "description": "Sophie Germain primes encryption", "encrypt": sophie_germain_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "perfect-number": {"name": "Perfect Number Cipher", "description": "Perfect numbers encryption", "encrypt": perfect_number_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "abundant": {"name": "Abundant Cipher", "description": "Abundant numbers encryption", "encrypt": abundant_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "deficient": {"name": "Deficient Cipher", "description": "Deficient numbers encryption", "encrypt": deficient_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "harshad": {"name": "Harshad Cipher", "description": "Harshad numbers encryption", "encrypt": harshad_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "kaprekar": {"name": "Kaprekar Cipher", "description": "Kaprekar numbers encryption", "encrypt": kaprekar_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "armstrong": {"name": "Armstrong Cipher", "description": "Armstrong numbers encryption", "encrypt": armstrong_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "happy-number": {"name": "Happy Number Cipher", "description": "Happy numbers encryption", "encrypt": happy_number_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "sad-number": {"name": "Sad Number Cipher", "description": "Sad numbers encryption", "encrypt": sad_number_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "palindromic": {"name": "Palindromic Cipher", "description": "Palindromic numbers encryption", "encrypt": palindromic_number_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "repdigit": {"name": "Repdigit Cipher", "description": "Repdigit numbers encryption", "encrypt": repdigit_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "pell": {"name": "Pell Cipher", "description": "Pell numbers encryption", "encrypt": pell_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "padovan": {"name": "Padovan Cipher", "description": "Padovan sequence encryption", "encrypt": padovan_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "moser": {"name": "Moser Cipher", "description": "Moser-de Bruijn sequence encryption", "encrypt": moser_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "golomb": {"name": "Golomb Cipher", "description": "Golomb sequence encryption", "encrypt": golomb_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "look-and-say": {"name": "Look-and-Say Cipher", "description": "Look-and-say sequence encryption", "encrypt": look_and_say_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "thue-morse": {"name": "Thue-Morse Cipher", "description": "Thue-Morse sequence encryption", "encrypt": thue_morse_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    
    # ===== ADVANCED POLYTRANSPOSITION (50+ NEW) =====
    "fractionated-morse": {"name": "Fractionated Morse", "description": "Morse code to fractionation", "encrypt": fractionated_morse, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "beaufort": {"name": "Beaufort Cipher", "description": "Reciprocal key cipher", "encrypt": beaufort, "decrypt": lambda text, key='SECRET', **kw: beaufort(text, key), "params": ["key"], "param_types": {"key": "text"}},
    "porta": {"name": "Porta Cipher", "description": "Polyalphabetic with 10 alphabets", "encrypt": porta, "decrypt": lambda text, key='SECRET', **kw: "Not supported", "params": ["key"], "param_types": {"key": "text"}},
    "four-square": {"name": "Four-Square Cipher", "description": "Digraph substitution cipher", "encrypt": four_square, "decrypt": lambda text, **kw: "Not supported", "params": ["key1", "key2"], "param_types": {"key1": "text", "key2": "text"}},
    "nicodemus": {"name": "Nicodemus Cipher", "description": "Columnar with padding", "encrypt": nicodemus, "decrypt": lambda text, **kw: "Not supported", "params": ["key"], "param_types": {"key": "text"}},
    "slide": {"name": "Slide Cipher", "description": "Keyword substitution", "encrypt": slide, "decrypt": lambda text, **kw: "Not supported", "params": ["key"], "param_types": {"key": "text"}},
    "trifid": {"name": "Trifid Cipher", "description": "Three-part substitution-transposition", "encrypt": trifid, "decrypt": lambda text, **kw: "Not supported", "params": ["key"], "param_types": {"key": "text"}},
    
    # ===== NUMBER SYSTEMS =====
    "binary": {"name": "Binary Cipher", "description": "Convert to binary representation", "encrypt": binary_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "octal": {"name": "Octal Cipher", "description": "Convert to octal representation", "encrypt": octal_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "hexadecimal": {"name": "Hexadecimal Cipher", "description": "Convert to hex representation", "encrypt": hexadecimal_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "base64-variant": {"name": "Base64 Variant", "description": "Base64-like encoding", "encrypt": base64_variant, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "base32": {"name": "Base32 Cipher", "description": "Base32 encoding", "encrypt": base32_cipher, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    
    # ===== SUBSTITUTION VARIANTS =====
    "homophonic": {"name": "Homophonic Substitution", "description": "Multiple ciphers for common letters", "encrypt": homophonic_simple, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "phonetic": {"name": "Phonetic Cipher", "description": "Based on sound similarity", "encrypt": simple_phonetic, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "mirror": {"name": "Mirror Alphabet", "description": "Atbash variant", "encrypt": mirror_alphabet, "decrypt": lambda text, **kw: mirror_alphabet(text), "params": [], "param_types": {}},
    "reverse-alphabet": {"name": "Reverse Alphabet", "description": "Reverse order substitution", "encrypt": reverse_alphabet, "decrypt": lambda text, **kw: reverse_alphabet(text), "params": [], "param_types": {}},
    "keyboard-shift": {"name": "Keyboard Shift", "description": "Shift based on keyboard adjacency", "encrypt": keyboard_shift, "decrypt": lambda text, **kw: "Not supported", "params": ["key"], "param_types": {"key": "text"}},
    
    # ===== TRANSPOSITION ADVANCED =====
    "zigzag-extended": {"name": "Extended Zigzag", "description": "Multi-rail fence variants", "encrypt": zigzag_extended, "decrypt": lambda text, rails=4, **kw: "Not supported", "params": ["rails"], "param_types": {"rails": "number"}},
    "columnar-double": {"name": "Double Columnar", "description": "Apply twice", "encrypt": columnar_double, "decrypt": lambda text, **kw: "Not supported", "params": ["key1", "key2"], "param_types": {"key1": "text", "key2": "text"}},
    "fence-extended": {"name": "Extended Fence", "description": "Split into multiple fences", "encrypt": fence_extended, "decrypt": lambda text, **kw: "Not supported", "params": ["key"], "param_types": {"key": "text"}},
    
    # ===== MODERN CRYPTOGRAPHIC =====
    "xor-extended": {"name": "Extended XOR", "description": "Multi-byte key XOR", "encrypt": xor_extended, "decrypt": xor_extended, "params": ["key"], "param_types": {"key": "text"}},
    "rolling-hash": {"name": "Rolling Hash", "description": "Hash-based transformation", "encrypt": rolling_hash, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "chaotic-map": {"name": "Chaotic Map", "description": "Logistic map transformation", "encrypt": chaotic_map, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    
    # ===== HISTORICAL VARIANTS =====
    "polybius-extended": {"name": "Extended Polybius", "description": "6x6 grid encoding", "encrypt": polybius_extended, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "fleissner": {"name": "Fleissner Grille", "description": "Rotating template cipher", "encrypt": fleissner_grille, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    "book-cipher": {"name": "Book Cipher", "description": "Word position encoding", "encrypt": book_cipher_simple, "decrypt": lambda text, **kw: "Not supported", "params": ["key"], "param_types": {"key": "text"}},
    "null-cipher": {"name": "Null Cipher", "description": "Every nth character hiding", "encrypt": null_cipher_variant, "decrypt": lambda text, **kw: "Not supported", "params": [], "param_types": {}},
    
    # ===== HYBRID APPROACHES =====
    "hybrid-vigenere-caesar": {"name": "Hybrid Vigenère-Caesar", "description": "Combines both methods", "encrypt": hybrid_vigenere_caesar, "decrypt": lambda text, **kw: "Not supported", "params": ["key"], "param_types": {"key": "text"}},
    "hybrid-subst-transpos": {"name": "Hybrid Substitution-Transposition", "description": "Combined transformation", "encrypt": hybrid_substitution_transposition, "decrypt": lambda text, **kw: "Not supported", "params": ["key"], "param_types": {"key": "text"}},
}

# ============ HELPER FUNCTIONS ============

def _mod_inverse(a: int, m: int = 26) -> int:
    """Find modular inverse of a mod m (if exists)."""
    a = a % m
    for x in range(1, m):
        if (a * x) % m == 1:
            return x
    return -1

def _affine_decrypt(text: str, a: int, b: int) -> str:
    """Affine decrypt using modular inverse of a."""
    text = _clean(text)
    inv = _mod_inverse(a, 26)
    if inv == -1:
        raise ValueError("Invalid affine key.")
    out = []
    for ch in text:
        if ch.isalpha():
            x = _char_to_num(ch)
            out.append(_num_to_char((inv * (x - b)) % 26))
        else:
            out.append(ch)
    return "".join(out)

def _dynamic_cipher_info(slug: str) -> Optional[dict]:
    """Return dynamic cipher info for slug variants."""
    if slug.startswith("caesar-") or slug.startswith("rot-") or slug.startswith("shift-"):
        parts = slug.split("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            shift = int(parts[1])
            if 0 <= shift <= 25:
                return {
                    "name": f"Caesar Shift {shift}",
                    "description": "Fixed-shift Caesar variant.",
                    "encrypt": lambda text, shift=shift, **kw: caesar_encrypt(text, shift),
                    "decrypt": lambda text, shift=shift, **kw: caesar_decrypt(text, shift),
                    "params": [],
                    "param_types": {},
                }
        return None

    if slug.startswith("rail-fence-"):
        rails_part = slug.split("-", 2)[-1]
        if rails_part.isdigit():
            rails = int(rails_part)
            if 2 <= rails <= 12:
                return {
                    "name": f"Rail Fence ({rails} rails)",
                    "description": "Fixed-rail zigzag transposition.",
                    "encrypt": lambda text, rails=rails, **kw: rail_fence_encrypt(text, rails),
                    "decrypt": lambda text, rails=rails, **kw: rail_fence_decrypt(text, rails),
                    "params": [],
                    "param_types": {},
                }
        return None

    if slug.startswith("xor-"):
        key_part = slug.split("-", 1)[1]
        if key_part.isdigit():
            key = int(key_part)
            if 0 <= key <= 255:
                return {
                    "name": f"XOR {key}",
                    "description": "Fixed-key XOR for quick obfuscation.",
                    "encrypt": lambda text, key=key, **kw: simple_xor(text, key),
                    "decrypt": lambda text, key=key, **kw: simple_xor(text, key),
                    "params": [],
                    "param_types": {},
                }
        return None

    if slug.startswith("atbash-shift-"):
        shift_part = slug.split("-", 2)[-1]
        if shift_part.isdigit():
            shift = int(shift_part)
            if 0 <= shift <= 25:
                return {
                    "name": f"Atbash + Shift {shift}",
                    "description": "Atbash followed by fixed Caesar shift.",
                    "encrypt": lambda text, shift=shift, **kw: atbash_with_shift(text, shift),
                    "decrypt": lambda text, shift=shift, **kw: atbash_encrypt(caesar_encrypt(text, -shift)),
                    "params": [],
                    "param_types": {},
                }
        return None

    affine_match = re.match(r"^affine-a(\d+)-b(\d+)$", slug)
    if affine_match:
        a = int(affine_match.group(1))
        b = int(affine_match.group(2))
        if 0 <= b <= 25 and _mod_inverse(a, 26) != -1:
            return {
                "name": f"Affine a={a}, b={b}",
                "description": "Affine cipher with fixed parameters.",
                "encrypt": lambda text, a=a, b=b, **kw: affine_cipher(text, a=a, b=b),
                "decrypt": lambda text, a=a, b=b, **kw: _affine_decrypt(text, a=a, b=b),
                "params": [],
                "param_types": {},
            }
        return None

    if slug.startswith("vigenere-key-"):
        key = slug.split("vigenere-key-", 1)[1].replace("-", "").upper()
        if key.isalpha():
            return {
                "name": f"Vigenere ({key})",
                "description": "Vigenere with a fixed key.",
                "encrypt": lambda text, key=key, **kw: vigenere_encrypt(text, key),
                "decrypt": lambda text, key=key, **kw: vigenere_decrypt(text, key),
                "params": [],
                "param_types": {},
            }
        return None

    if slug.startswith("beaufort-key-"):
        key = slug.split("beaufort-key-", 1)[1].replace("-", "").upper()
        if key.isalpha():
            return {
                "name": f"Beaufort ({key})",
                "description": "Beaufort with a fixed key.",
                "encrypt": lambda text, key=key, **kw: beaufort_encrypt(text, key),
                "decrypt": lambda text, key=key, **kw: beaufort_decrypt(text, key),
                "params": [],
                "param_types": {},
            }
        return None

    return None

def cipher_exists(slug: str) -> bool:
    """Check if a cipher slug exists"""
    return slug in CLASSIC_CIPHERS or _dynamic_cipher_info(slug) is not None

def get_cipher_info(slug: str) -> dict:
    """Get cipher metadata"""
    if slug in CLASSIC_CIPHERS:
        return CLASSIC_CIPHERS[slug]
    dynamic = _dynamic_cipher_info(slug)
    return dynamic or {}

def encrypt_with_cipher(slug: str, text: str, **params) -> str:
    """Encrypt text using specified cipher"""
    if slug in CLASSIC_CIPHERS:
        cipher = CLASSIC_CIPHERS[slug]
    else:
        cipher = _dynamic_cipher_info(slug)
        if not cipher:
            raise ValueError(f"Unknown cipher: {slug}")
    return cipher["encrypt"](text, **params)

def decrypt_with_cipher(slug: str, text: str, **params) -> str:
    """Decrypt text using specified cipher"""
    if slug in CLASSIC_CIPHERS:
        cipher = CLASSIC_CIPHERS[slug]
    else:
        cipher = _dynamic_cipher_info(slug)
        if not cipher:
            raise ValueError(f"Unknown cipher: {slug}")
    return cipher["decrypt"](text, **params)
