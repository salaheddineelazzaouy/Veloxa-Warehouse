import os
from cryptography.fernet import Fernet


def generate_key() -> str:
    return Fernet.generate_key().decode()


def get_fernet(key: str | None = None) -> Fernet:
    if key is None:
        key = os.environ.get("FIELD_ENCRYPTION_KEY", "")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_value(plaintext: str, key: str | None = None) -> str:
    f = get_fernet(key)
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str, key: str | None = None) -> str:
    f = get_fernet(key)
    return f.decrypt(ciphertext.encode()).decode()
