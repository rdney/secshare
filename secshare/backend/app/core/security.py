from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


class SecretEncryption:
    """Handles encryption and decryption of secrets using AES-GCM"""

    @staticmethod
    def generate_key() -> bytes:
        """Generate a random 256-bit key"""
        return os.urandom(32)

    @staticmethod
    def generate_iv() -> bytes:
        """Generate a random 96-bit IV"""
        return os.urandom(12)

    @staticmethod
    def encrypt(plaintext: str, key: bytes, iv: bytes) -> bytes:
        """Encrypt plaintext using AES-GCM"""
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(iv, plaintext.encode(), None)
        return ciphertext

    @staticmethod
    def decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> str:
        """Decrypt ciphertext using AES-GCM"""
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(iv, ciphertext, None)
        return plaintext.decode()

    @staticmethod
    def encrypt_key(key: bytes, master_key: str) -> bytes:
        """Encrypt the secret key using a master key derived from settings"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"secshare",  # In production, use a proper salt
            iterations=100000,
        )
        derived_key = kdf.derive(master_key.encode())

        iv = os.urandom(12)
        aesgcm = AESGCM(derived_key)
        encrypted = aesgcm.encrypt(iv, key, None)
        return iv + encrypted

    @staticmethod
    def decrypt_key(encrypted_key: bytes, master_key: str) -> bytes:
        """Decrypt the secret key using the master key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"secshare",
            iterations=100000,
        )
        derived_key = kdf.derive(master_key.encode())

        iv = encrypted_key[:12]
        ciphertext = encrypted_key[12:]

        aesgcm = AESGCM(derived_key)
        key = aesgcm.decrypt(iv, ciphertext, None)
        return key
