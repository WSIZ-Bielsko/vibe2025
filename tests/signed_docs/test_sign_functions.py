import pytest
import tempfile
import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ec

from vibe2025.signed_docs.crypto_utils import generate_keys, sign_text, verify_signature, save_private_key, save_public_key, \
    load_private_key, load_public_key


def test_sign_and_verify_valid_signature():
    """Test that a valid signature can be created and verified"""
    # Generate keys
    private_key = generate_keys()
    public_key = private_key.public_key()

    # Sign text
    text = "Hello, this is a test message"
    signature = sign_text(text, private_key)

    # Verify signature
    assert verify_signature(text, signature, public_key) is True


def test_verify_signature_with_tampered_text():
    """Test that verification fails with modified text"""
    # Generate keys
    private_key = generate_keys()
    public_key = private_key.public_key()

    # Sign original text
    original_text = "Original message"
    signature = sign_text(original_text, private_key)

    # Verify with tampered text
    tampered_text = "Tampered message"
    assert verify_signature(tampered_text, signature, public_key) is False


def test_save_and_load_keys():
    """Test that keys can be saved to and loaded from files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        private_key_path = Path(tmpdir) / "test_private.pem"
        public_key_path = Path(tmpdir) / "test_public.pem"

        # Generate and save keys
        private_key = generate_keys()
        save_private_key(private_key, str(private_key_path))
        save_public_key(private_key, str(public_key_path))

        # Verify files exist
        assert private_key_path.exists()
        assert public_key_path.exists()

        # Load keys
        loaded_private_key = load_private_key(str(private_key_path))
        loaded_public_key = load_public_key(str(public_key_path))

        # Verify loaded keys work
        text = "Test message for loaded keys"
        signature = sign_text(text, loaded_private_key)
        assert verify_signature(text, signature, loaded_public_key) is True


## how hacks #1

import os
import tempfile
import pytest

# Assumes the functions are imported from your module:
# from your_module import (
#     generate_keys, sign_text, verify_signature,
#     save_private_key, save_public_key, load_private_key, load_public_key
# )

def test_signature_replay_same_message_different_context():
    # Replay attack: reusing a valid signature for a different context string must fail
    priv = generate_keys()
    pub = priv.public_key()
    message = "pay=100;to=alice"
    signature = sign_text(message, priv)
    different_context = "pay=100;to=alice;nonce=12345"
    assert verify_signature(different_context, signature, pub) is False  # context-bound verification should fail on change [web:6]


def test_signature_tampered_bytes_fail():
    # Signature tampering: flipping a byte in the signature must invalidate it
    priv = generate_keys()
    pub = priv.public_key()
    msg = "integrity check"
    sig = bytearray(sign_text(msg, priv))
    sig[0] ^= 0xFF  # flip first byte
    assert verify_signature(msg, bytes(sig), pub) is False  # tampered signature invalidates verification [web:6]


def test_public_key_swap_attack_fails():
    # Key substitution: signature created with key A must not verify with key B
    priv_a = generate_keys()
    priv_b = generate_keys()
    pub_b = priv_b.public_key()
    msg = "key substitution test"
    sig_a = sign_text(msg, priv_a)
    assert verify_signature(msg, sig_a, pub_b) is False  # swapping public keys breaks verification [web:6]


def test_modified_message_same_signature_fails():
    # Message malleability attempt: reusing same signature over modified message must fail
    priv = generate_keys()
    pub = priv.public_key()
    original = "order=42;item=bike"
    sig = sign_text(original, priv)
    modified = "order=42;item=ebike"  # single character change
    assert verify_signature(modified, sig, pub) is False  # any change to message breaks RSA-PSS verification [web:11][web:6]


def test_saved_keys_cannot_verify_cross_key_signatures():
    # Persistence misuse: ensure signatures are tied to the correct saved public key (prevents accidental key-mix)
    with tempfile.TemporaryDirectory() as d:
        priv1 = generate_keys()
        priv2 = generate_keys()
        p1 = os.path.join(d, "k1.pem")
        P1 = os.path.join(d, "K1.pub.pem")
        p2 = os.path.join(d, "k2.pem")
        P2 = os.path.join(d, "K2.pub.pem")

        save_private_key(priv1, p1)
        save_public_key(priv1, P1)
        save_private_key(priv2, p2)
        save_public_key(priv2, P2)

        pub1 = load_public_key(P1)
        pub2 = load_public_key(P2)

        msg = "cross-key verification"
        sig1 = sign_text(msg, load_private_key(p1))
        sig2 = sign_text(msg, load_private_key(p2))

        # Each signature must verify only with its matching public key
        assert verify_signature(msg, sig1, pub1) is True  # correct pairing verifies [web:11][web:6]
        assert verify_signature(msg, sig1, pub2) is False  # wrong key pairing must fail [web:6]
        assert verify_signature(msg, sig2, pub2) is True  # correct pairing verifies [web:11][web:6]
        assert verify_signature(msg, sig2, pub1) is False  # wrong key pairing must fail [web:6]

def test_no_signature_provided():
    """
    Tests the verification function's behavior when None or an empty byte string
    is provided as the signature. It should not validate.
    """
    private_key = generate_keys()
    public_key = private_key.public_key()
    text = "A message that needs a signature"

    # The `verify` method from the cryptography library is expected to raise an
    # exception with an invalid signature format, which our wrapper catches.
    assert verify_signature(text, None, public_key) is False
    assert verify_signature(text, b'', public_key) is False


def test_wrong_algorithm_or_key_type_attack():
    """
    Tests robustness against signatures created with a different algorithm or
    key type (e.g., ECDSA instead of RSA). Verification should fail.
    """
    rsa_private_key = generate_keys()
    text = "Message signed with RSA"
    signature = sign_text(text, rsa_private_key)

    # Generate an ECDSA public key (a different algorithm)
    ecdsa_private_key = ec.generate_private_key(ec.SECP256R1())
    ecdsa_public_key = ecdsa_private_key.public_key()

    assert verify_signature(text, signature, ecdsa_public_key) is False
