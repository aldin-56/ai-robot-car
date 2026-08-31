import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Get secret key from env or default
_SECRET_KEY = os.getenv("LITEMIND_SECRET_KEY", "litemind-super-secret-production-encryption-key-2025")

def _get_fernet():
    salt = b"litemind_salt_key_2025"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(_SECRET_KEY.encode()))
    return Fernet(key)

def encrypt_secret(plain_text: str) -> str:
    if not plain_text:
        return ""
    f = _get_fernet()
    return f.encrypt(plain_text.encode()).decode()

def decrypt_secret(cipher_text: str) -> str:
    if not cipher_text:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(cipher_text.encode()).decode()
    except Exception:
        return ""
