import json
import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
from typing import Dict, Optional

class EncryptedStoreService:
    def __init__(self, path: str, master_password: str):
        self.path = path
        self.master_password = master_password
        self._store: Dict[str, str] = {}
        self._opened = False
        self._salt: Optional[bytes] = None

    def _derive_key(self, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self.master_password.encode("utf-8")))

    def load(self):
        if not os.path.exists(self.path):
            # generate new salt for the new file
            print('creating new file')
            self._salt = os.urandom(16)
            self._store = {}
            self._opened = True
            return
        with open(self.path, "rb") as f:
            header = f.read(24)
            self._salt = header[:16]
            data = header[16:] + f.read()
            key = self._derive_key(self._salt)
            store_json = Fernet(key).decrypt(data).decode("utf-8")
            self._store = json.loads(store_json)
            self._opened = True

    def list_keys(self):
        if not self._opened:
            raise RuntimeError("EncryptedStoreService is not loaded")
        return list(self._store.keys())

    def get(self, key: str) -> Optional[str]:
        if not self._opened:
            raise RuntimeError("EncryptedStoreService is not loaded")
        return self._store.get(key)

    def put(self, key: str, value: str):
        if not self._opened:
            raise RuntimeError("EncryptedStoreService is not loaded")
        self._store[key] = value

    def lock(self):
        if not self._opened:
            raise RuntimeError("EncryptedStoreService is not loaded")
        key = self._derive_key(self._salt if self._salt else os.urandom(16))
        store_json = json.dumps(self._store).encode("utf-8")
        encrypted = Fernet(key).encrypt(store_json)
        with open(self.path, "wb") as f:
            f.write(self._salt)
            f.write(encrypted)
        self._store = {}
        self._opened = False
        self._salt = None
