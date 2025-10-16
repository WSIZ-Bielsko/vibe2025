import os
from vibe2025.secure_storage.service import EncryptedStoreService


def test_roundtrip(tmp_dir='..'):
    path = os.path.join(tmp_dir, " data.enc")
    pw = "superpassword"
    s = EncryptedStoreService(path, pw)
    s.load()
    s.put("foo", "bar")
    s.put("alpha", "beta")
    s.lock()

    # load again and test
    s2 = EncryptedStoreService(path, pw)
    s2.load()
    assert set(s2.list_keys()) == {"foo", "alpha"}
    assert s2.get("foo") == "bar"
    assert s2.get("alpha") == "beta"
    s2.lock()
    os.remove(path)


if __name__ == "__main__":
    test_roundtrip()
