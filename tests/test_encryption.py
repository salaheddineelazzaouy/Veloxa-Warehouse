"""Tests for encryption utilities — AES-256-GCM."""
import pytest
from lib.encryption import generate_key, encrypt_value, decrypt_value


class TestEncryption:
    def test_roundtrip(self):
        key = generate_key()
        original = "sensitive-data-123"
        encrypted = encrypt_value(original, key)
        assert encrypted != original
        decrypted = decrypt_value(encrypted, key)
        assert decrypted == original

    def test_different_keys_produce_different_ciphertext(self):
        key1 = generate_key()
        key2 = generate_key()
        plain = "hello"
        e1 = encrypt_value(plain, key1)
        e2 = encrypt_value(plain, key2)
        assert e1 != e2
