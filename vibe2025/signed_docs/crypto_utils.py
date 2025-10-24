from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding


"""
Prompt:
given a string in python, create functions sign_text and verify_signature, that would sign a sha256 of this text 
and verify the signeture; for the signatures create functions to generate keys, save/load them from files

"""

def generate_keys() -> rsa.RSAPrivateKey:
    """Generate RSA private key pair"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    return private_key


def save_private_key(private_key: rsa.RSAPrivateKey, filename, password=None):
    """Save private key to file with optional password protection"""
    encryption = (
        serialization.BestAvailableEncryption(password.encode())
        if password
        else serialization.NoEncryption()
    )

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption
    )

    with open(filename, 'wb') as f:
        f.write(pem)


def save_public_key(private_key, filename):
    """Save public key to file"""
    public_key = private_key.public_key()
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with open(filename, 'wb') as f:
        f.write(pem)


def load_private_key(filename, password=None):
    """Load private key from file"""
    with open(filename, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=password.encode() if password else None
        )
    return private_key


def load_public_key(filename):
    """Load public key from file"""
    with open(filename, 'rb') as f:
        public_key = serialization.load_pem_public_key(f.read())
    return public_key


def sign_text(text, private_key: rsa.RSAPrivateKey):
    """Sign SHA-256 hash of text using private key"""
    message = text.encode()

    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    return signature


def verify_signature(text, signature, public_key):
    """Verify signature of text using public key"""
    message = text.encode()

    try:
        public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:
        return False


# Example usage
if __name__ == "__main__":
    # Generate and save keys
    private_key = generate_keys()
    save_private_key(private_key, 'private_key.pem')
    save_public_key(private_key, 'public_key.pem')

    # Sign text
    text = "Hello, this is a test message"
    signature = sign_text(text, private_key)
    print(f"Signature: {signature.hex()[:64]}...")

    # Load keys and verify
    loaded_private_key = load_private_key('private_key.pem')
    loaded_public_key = load_public_key('public_key.pem')

    is_valid = verify_signature(text, signature, loaded_public_key)
    print(f"Signature valid: {is_valid}")

    # Test with tampered text
    is_valid_tampered = verify_signature("Tampered message", signature, loaded_public_key)
    print(f"Tampered signature valid: {is_valid_tampered}")
