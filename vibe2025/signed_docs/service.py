from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from vibe2025.signed_docs.model import Document, Signature


class SignedDocumentsService:
    """Service for managing trusted public keys and verifying document signatures"""

    def __init__(self):
        """Initialize with empty trusted keys dictionary"""
        self.trusted_keys: dict[int, str] = {}

    def add_trusted_key(self, signer_id: int, public_key_pem: str) -> None:
        """
        Add a trusted public key for a signer

        Args:
            signer_id: Unique identifier for the signer
            public_key_pem: Public key in PEM format

        Raises:
            ValueError: If public key format is invalid
        """
        # Validate the key can be loaded
        try:
            serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
        except Exception as e:
            raise ValueError(f"Invalid public key format: {e}")

        self.trusted_keys[signer_id] = public_key_pem

    def remove_trusted_key(self, signer_id: int) -> bool:
        """
        Remove a trusted public key

        Args:
            signer_id: Identifier of the signer to remove

        Returns:
            True if key was removed, False if signer_id wasn't found
        """
        if signer_id in self.trusted_keys:
            del self.trusted_keys[signer_id]
            return True
        return False

    def get_trusted_key(self, signer_id: int) -> str | None:
        """Get trusted public key for a signer"""
        return self.trusted_keys.get(signer_id)

    def list_trusted_signers(self) -> list[int]:
        """Get list of all trusted signer IDs"""
        return list(self.trusted_keys.keys())

    def verify_document_signature(self, document: Document, signature: Signature) -> bool:
        """
        Verify a document signature using trusted public keys

        Args:
            document: The document to verify
            signature: The signature to check

        Returns:
            True if signature is valid and from a trusted signer, False otherwise
        """
        try:
            # Check if signer is trusted
            if signature.signator_id not in self.trusted_keys:
                return False

            # Check document ID matches
            if document.id != signature.document_id:
                return False

            # Get trusted public key
            trusted_key_pem = self.trusted_keys[signature.signator_id]

            # Verify the signature's public key matches trusted key
            if signature.public_key != trusted_key_pem:
                return False

            # Load public key
            public_key = serialization.load_pem_public_key(
                trusted_key_pem.encode('utf-8')
            )

            # Get canonical JSON
            current_json = document.model_dump_json(indent=None)
            if current_json != signature.json_version:
                return False

            # Verify the cryptographic signature
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


# Example usage
if __name__ == "__main__":
    from uuid import uuid4
    from datetime import datetime
    from vibe2025.signed_docs.model import Paragraph
    from vibe2025.signed_docs.processor import DocumentProcessor

    # Setup: Create a document and sign it
    processor = DocumentProcessor()
    processor.generate_keys()

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

    sig = processor.sign_document(doc, signator_id=42)

    # Create service and add trusted key
    service = SignedDocumentsService()
    service.add_trusted_key(42, processor.get_public_key_pem())

    # Verify signature
    is_valid = service.verify_document_signature(doc, sig)
    print(f"Signature valid: {is_valid}")  # True

    # Try with untrusted signer
    sig_untrusted = processor.sign_document(doc, signator_id=999)
    is_valid = service.verify_document_signature(doc, sig_untrusted)
    print(f"Untrusted signature valid: {is_valid}")  # False

    # Remove trusted key
    removed = service.remove_trusted_key(42)
    print(f"Key removed: {removed}")  # True

    # Verify fails after removal
    is_valid = service.verify_document_signature(doc, sig)
    print(f"Signature valid after removal: {is_valid}")  # False
