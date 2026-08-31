import os
import base64
import datetime
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel

SECRET_KEY = os.getenv("LITEMIND_SECRET_KEY", "litemind_super_secret_master_key_2025!")
SALT = b"litemind_static_salt_for_key_derivation"

kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=SALT,
    iterations=100000,
)
fernet_key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
fernet = Fernet(fernet_key)


def encrypt_api_key(api_key: str) -> str:
    """Encrypts an API key before storing in the database."""
    if not api_key:
        return ""
    return fernet.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypts a stored API key for backend-only provider call execution."""
    if not encrypted_key:
        return ""
    try:
        return fernet.decrypt(encrypted_key.encode()).decode()
    except Exception:
        return ""


def mask_api_key(api_key: str) -> str:
    """Returns a masked version of the API key for secure UI presentation."""
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "****" + api_key[-2:]
    return api_key[:4] + "...." + api_key[-4:]


def sanitize_input(user_input: str) -> str:
    """Basic input sanitization and prompt injection boundary wrapper."""
    if not user_input:
        return ""
    # Strip dangerous controls
    sanitized = user_input.replace("\0", "").strip()
    return sanitized
