import json
from datetime import datetime
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from vibe2025.signed_docs.crypto_utils import save_public_key, generate_keys
from vibe2025.signed_docs.model import Document, Signature, Paragraph

"""
Prompt:
now given the model attached below, write a class "DocumentProcessor" that allows 
to create Signature objects for given Documents; 
also saving/loading (document,signature) pairs, verifying signatures
"""

"""
This is a de-facto client for working with Documents and Signatures.
"""

class DocumentProcessor:
    def __init__(self, private_key_path: str = None):
        """Initialize processor with optional private key"""
        self.private_key = None
        if private_key_path and Path(private_key_path).exists():
            self.load_private_key(private_key_path)

    def generate_keys(self):
        """Generate new RSA key pair"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        return self.private_key

    def save_private_key(self, filename: str, password: str = None):
        """Save private key to file"""
        if not self.private_key:
            raise ValueError("No private key to save")

        encryption = (
            serialization.BestAvailableEncryption(password.encode())
            if password
            else serialization.NoEncryption()
        )

        pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption
        )

        Path(filename).write_bytes(pem)

    def load_private_key(self, filename: str, password: str = None):
        """Load private key from file"""
        pem_data = Path(filename).read_bytes()
        self.private_key = serialization.load_pem_private_key(
            pem_data,
            password=password.encode() if password else None
        )
        return self.private_key

    def get_public_key_pem(self) -> str:
        """Get public key as PEM string"""
        if not self.private_key:
            raise ValueError("No private key available")

        public_key = self.private_key.public_key()
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')

    def _document_to_canonical_json(self, document: Document) -> str:
        """Convert the document to canonical JSON for signing"""
        return document.model_dump_json(indent=None)

    def sign_document(self, document: Document, signator_id: int) -> Signature:
        """Create signature for a document"""
        if not self.private_key:
            raise ValueError("No private key loaded")

        # Get canonical JSON representation
        json_version = self._document_to_canonical_json(document)
        message = json_version.encode('utf-8')

        # Sign the document
        signature_bytes = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return Signature(
            document_id=document.id,
            json_version=json_version,
            signator_id=signator_id,
            public_key=self.get_public_key_pem(),
            signature=signature_bytes.hex(),
            signed_at=datetime.now()
        )

    def verify_signature(self, document: Document, signature: Signature) -> bool:
        """Verify a signature against a document"""
        try:
            # Check document ID matches
            if document.id != signature.document_id:
                return False

            # Load public key from signature
            public_key = serialization.load_pem_public_key(
                signature.public_key.encode('utf-8')
            )

            # Get canonical JSON and verify it matches stored version
            current_json = self._document_to_canonical_json(document)
            if current_json != signature.json_version:
                return False

            # Verify the signature
            message = signature.json_version.encode('utf-8')
            signature_bytes = bytes.fromhex(signature.signature)

            public_key.verify(
                signature_bytes,
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
        except Exception:
            return False

    def save_document_signature_pair(self, document: Document, signature: Signature, filename: str):
        """Save document and signature to JSON file"""
        data = {
            "document": json.loads(document.model_dump_json()),
            "signature": json.loads(signature.model_dump_json())
        }
        Path(filename).write_text(json.dumps(data, indent=2, default=str))

    def load_document_signature_pair(self, filename: str) -> tuple[Document, Signature]:
        """Load document and signature from JSON file"""
        data = json.loads(Path(filename).read_text())
        document = Document(**data["document"])
        signature = Signature(**data["signature"])
        return document, signature


# Example usage
if __name__ == "__main__":
    from uuid import uuid4

    # Create processor and generate keys
    processor = DocumentProcessor()
    processor.generate_keys()
    processor.save_private_key("private_key.pem")

    # Create a document
    doc = Document(
        id=uuid4(),
        author_id=1,
        addressee_id=2,
        created_at=datetime.now(),
        content=[
            Paragraph(fixed_text="Dear", placeholder="name", text="John"),
            Paragraph(fixed_text="Amount", placeholder="value", text="1000")
        ]
    )

    # Sign the document
    sig = processor.sign_document(doc, signator_id=1)
    print(f"Document signed: {sig.document_id}")

    # Verify signature
    is_valid = processor.verify_signature(doc, sig)
    print(f"Signature valid: {is_valid}")

    # Save pair
    processor.save_document_signature_pair(doc, sig, "doc_sig_pair.json")

    # Load and verify
    loaded_doc, loaded_sig = processor.load_document_signature_pair("doc_sig_pair.json")
    print(f"Loaded document: {loaded_doc}")
    is_valid = processor.verify_signature(loaded_doc, loaded_sig)
    print(f"Loaded signature valid: {is_valid}")

