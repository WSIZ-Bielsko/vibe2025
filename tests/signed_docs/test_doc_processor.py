import pytest
from datetime import datetime
from uuid import uuid4
from pathlib import Path
from vibe2025.signed_docs.processor import DocumentProcessor, Document, Paragraph, Signature


@pytest.fixture
def sample_document():
    """Fixture providing a sample document for testing"""
    return Document(
        id=uuid4(),
        author_id=1,
        addressee_id=2,
        created_at=datetime.now(),
        content=[
            Paragraph(fixed_text="Dear", placeholder="name", text="John Doe"),
            Paragraph(fixed_text="Amount", placeholder="value", text="1000 USD")
        ]
    )


@pytest.fixture
def processor_with_keys(tmp_path):
    """Fixture providing a DocumentProcessor with generated keys"""
    processor = DocumentProcessor()
    processor.generate_keys()
    key_path = tmp_path / "private_key.pem"
    processor.save_private_key(str(key_path))
    return processor, key_path


def test_sign_and_verify_document(processor_with_keys, sample_document):
    """Test signing a document and verifying the signature"""
    processor, _ = processor_with_keys

    # Sign the document
    signature = processor.sign_document(sample_document, signator_id=42)

    # Verify signature properties
    assert signature.document_id == sample_document.id
    assert signature.signator_id == 42
    assert len(signature.signature) > 0
    assert len(signature.public_key) > 0

    # Verify signature is valid
    is_valid = processor.verify_signature(sample_document, signature)
    assert is_valid is True


def test_signature_fails_with_tampered_document(processor_with_keys, sample_document):
    """Test that signature verification fails when document is modified"""
    processor, _ = processor_with_keys

    # Sign the original document
    signature = processor.sign_document(sample_document, signator_id=1)

    # Tamper with the document content
    tampered_document = sample_document.model_copy(deep=True)
    tampered_document.content[0].text = "Jane Doe"

    # Verification should fail
    is_valid = processor.verify_signature(tampered_document, signature)
    assert is_valid is False


def test_save_and_load_document_signature_pair(processor_with_keys, sample_document, tmp_path):
    """Test saving and loading document-signature pairs from file"""
    processor, _ = processor_with_keys

    # Create signature
    signature = processor.sign_document(sample_document, signator_id=5)

    # Save to file
    pair_file = tmp_path / "doc_sig_pair.json"
    processor.save_document_signature_pair(sample_document, signature, str(pair_file))

    # Verify file exists
    assert pair_file.exists()

    # Load from file
    loaded_doc, loaded_sig = processor.load_document_signature_pair(str(pair_file))

    # Verify loaded data matches original
    assert loaded_doc.id == sample_document.id
    assert loaded_doc.author_id == sample_document.author_id
    assert loaded_sig.document_id == signature.document_id
    assert loaded_sig.signature == signature.signature

    # Verify signature is still valid after loading
    is_valid = processor.verify_signature(loaded_doc, loaded_sig)
    assert is_valid is True


def test_key_persistence_and_signature_verification(tmp_path, sample_document):
    """Test that keys can be saved, loaded, and used for verification"""
    # Create processor and generate keys
    processor1 = DocumentProcessor()
    processor1.generate_keys()

    # Save private key
    key_file = tmp_path / "test_private_key.pem"
    processor1.save_private_key(str(key_file))

    # Sign document with first processor
    signature = processor1.sign_document(sample_document, signator_id=10)

    # Create new processor and load the same key
    processor2 = DocumentProcessor()
    processor2.load_private_key(str(key_file))

    # Verify that loaded key can verify the signature
    is_valid = processor2.verify_signature(sample_document, signature)
    assert is_valid is True

    # Verify both processors can sign with same key
    signature2 = processor2.sign_document(sample_document, signator_id=10)
    is_valid = processor1.verify_signature(sample_document, signature2)
    assert is_valid is True


def test_signature_replay_attack_different_document(processor_with_keys, sample_document):
    """Test that a signature cannot be reused for a different document"""
    processor, _ = processor_with_keys

    # Sign the original document
    original_signature = processor.sign_document(sample_document, signator_id=1)

    # Create a completely different document with different ID
    different_document = Document(
        id=uuid4(),  # Different ID
        author_id=999,  # Different author
        addressee_id=888,
        created_at=datetime.now(),
        content=[
            Paragraph(fixed_text="Approved", placeholder="amount", text="9999999 USD")
        ]
    )

    # Try to use original signature on different document
    is_valid = processor.verify_signature(different_document, original_signature)
    assert is_valid is False


def test_forged_signature_with_different_keys(processor_with_keys, sample_document, tmp_path):
    """Test that signature from different key pair is rejected"""
    processor1, _ = processor_with_keys

    # Create second processor with different keys
    processor2 = DocumentProcessor()
    processor2.generate_keys()

    # Attacker signs document with their own key
    attacker_signature = processor2.sign_document(sample_document, signator_id=1)

    # Replace public key in signature with victim's public key
    legitimate_public_key = processor1.get_public_key_pem()
    forged_signature = Signature(
        document_id=attacker_signature.document_id,
        json_version=attacker_signature.json_version,
        signator_id=attacker_signature.signator_id,
        public_key=legitimate_public_key,  # Replaced with legitimate key
        signature=attacker_signature.signature,  # But signature from attacker's key
        signed_at=attacker_signature.signed_at
    )

    # Verification should fail because signature doesn't match public key
    is_valid = processor1.verify_signature(sample_document, forged_signature)
    assert is_valid is False


def test_manipulated_json_version_in_signature(processor_with_keys, sample_document):
    """Test that tampering with the stored JSON version is detected"""
    processor, _ = processor_with_keys

    # Sign the document
    original_signature = processor.sign_document(sample_document, signator_id=1)

    # Create tampered document JSON with modified content
    tampered_document = sample_document.model_copy(deep=True)
    tampered_document.content[0].text = "Modified Content"

    # Create fake signature with tampered JSON but keeping original signature bytes
    tampered_json = tampered_document.model_dump_json(indent=None)

    manipulated_signature = Signature(
        document_id=original_signature.document_id,
        json_version=tampered_json,  # Modified JSON
        signator_id=original_signature.signator_id,
        public_key=original_signature.public_key,
        signature=original_signature.signature,  # Original signature bytes
        signed_at=original_signature.signed_at
    )

    # Verification should fail because signature doesn't match the tampered JSON
    is_valid = processor.verify_signature(sample_document, manipulated_signature)
    assert is_valid is False

    # Also verify with the tampered document itself
    is_valid_tampered = processor.verify_signature(tampered_document, manipulated_signature)
    assert is_valid_tampered is False
