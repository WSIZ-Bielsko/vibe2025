#!/usr/bin/env python3
"""
Console-based client for DocumentProcessor
"""
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from vibe2025.signed_docs.model import Document, Paragraph
from vibe2025.signed_docs.processor import DocumentProcessor


class DocumentClient:
    """Interactive console client for document signing operations"""

    def __init__(self):
        self.processor = DocumentProcessor()
        self.current_document = None

    def run(self):
        """Main interactive loop"""
        print("=== Document Processor Client ===\n")

        while True:
            self.print_menu()
            choice = input("\nEnter choice: ").strip()

            if choice == "1":
                self.generate_keys()
            elif choice == "2":
                self.save_keys()
            elif choice == "3":
                self.load_keys()
            elif choice == "4":
                self.show_public_key()
            elif choice == "5":
                self.create_document()
            elif choice == "6":
                self.sign_current_document()
            elif choice == "7":
                self.verify_document()
            elif choice == "8":
                self.save_document_signature()
            elif choice == "9":
                self.load_document_signature()
            elif choice == "0":
                print("Exiting...")
                break
            else:
                print("Invalid choice, try again.")

            input("\nPress Enter to continue...")

    def print_menu(self):
        """Display main menu"""
        print("\n" + "=" * 50)
        print("MENU:")
        print("=" * 50)
        print("Key Management:")
        print("  1. Generate new keys")
        print("  2. Save private key to file")
        print("  3. Load private key from file")
        print("  4. Show public key")
        print()
        print("Document Operations:")
        print("  5. Create new document")
        print("  6. Sign current document")
        print("  7. Verify document signature")
        print("  8. Save document + signature to file")
        print("  9. Load document + signature from file")
        print()
        print("  0. Exit")
        print("=" * 50)

    def generate_keys(self):
        """Generate new RSA key pair"""
        print("\n--- Generate Keys ---")
        try:
            self.processor.generate_keys()
            print("✓ Keys generated successfully")
        except Exception as e:
            print(f"✗ Error: {e}")

    def save_keys(self):
        """Save private key to file"""
        print("\n--- Save Private Key ---")
        if not self.processor.private_key:
            print("✗ No private key loaded. Generate keys first.")
            return

        filename = input("Enter filename (e.g., private_key.pem): ").strip()
        use_password = input("Use password protection? (y/n): ").strip().lower() == 'y'

        password = None
        if use_password:
            password = input("Enter password: ").strip()

        try:
            self.processor.save_private_key(filename, password)
            print(f"✓ Private key saved to {filename}")
        except Exception as e:
            print(f"✗ Error: {e}")

    def load_keys(self):
        """Load private key from file"""
        print("\n--- Load Private Key ---")
        filename = input("Enter filename: ").strip()

        if not Path(filename).exists():
            print(f"✗ File {filename} not found")
            return

        use_password = input("Is key password-protected? (y/n): ").strip().lower() == 'y'
        password = None
        if use_password:
            password = input("Enter password: ").strip()

        try:
            self.processor.load_private_key(filename, password)
            print(f"✓ Private key loaded from {filename}")
        except Exception as e:
            print(f"✗ Error: {e}")

    def show_public_key(self):
        """Display public key"""
        print("\n--- Public Key ---")
        try:
            pem = self.processor.get_public_key_pem()
            print(pem)
        except Exception as e:
            print(f"✗ Error: {e}")

    def create_document(self):
        """Create a new document interactively"""
        print("\n--- Create Document ---")

        try:
            author_id = int(input("Enter author ID: ").strip())
            addressee_id = int(input("Enter addressee ID: ").strip())

            print("\nAdd paragraphs (empty fixed_text to finish):")
            paragraphs = []
            while True:
                fixed_text = input("  Fixed text: ").strip()
                if not fixed_text:
                    break
                placeholder = input("  Placeholder: ").strip()
                text = input("  Text value: ").strip()
                paragraphs.append(Paragraph(
                    fixed_text=fixed_text,
                    placeholder=placeholder,
                    text=text
                ))

            if not paragraphs:
                print("✗ At least one paragraph required")
                return

            self.current_document = Document(
                id=uuid4(),
                parent_document_id=None,
                author_id=author_id,
                addressee_id=addressee_id,
                created_at=datetime.now(),
                content=paragraphs
            )

            print(f"\n✓ Document created with ID: {self.current_document.id}")
            print(f"  Author: {author_id}, Addressee: {addressee_id}")
            print(f"  Paragraphs: {len(paragraphs)}")

        except ValueError as e:
            print(f"✗ Invalid input: {e}")
        except Exception as e:
            print(f"✗ Error: {e}")

    def sign_current_document(self):
        """Sign the current document"""
        print("\n--- Sign Document ---")

        if not self.current_document:
            print("✗ No document loaded. Create or load a document first.")
            return

        if not self.processor.private_key:
            print("✗ No private key loaded. Generate or load keys first.")
            return

        try:
            signator_id = int(input("Enter signator ID: ").strip())
            signature = self.processor.sign_document(self.current_document, signator_id)

            print(f"\n✓ Document signed successfully")
            print(f"  Document ID: {signature.document_id}")
            print(f"  Signator ID: {signature.signator_id}")
            print(f"  Signed at: {signature.signed_at}")
            print(f"  Signature (first 64 chars): {signature.signature[:64]}...")

            # Store signature for saving
            self.current_signature = signature

        except ValueError as e:
            print(f"✗ Invalid input: {e}")
        except Exception as e:
            print(f"✗ Error: {e}")

    def verify_document(self):
        """Verify a document signature"""
        print("\n--- Verify Signature ---")

        if not hasattr(self, 'current_signature') or not self.current_signature:
            print("✗ No signature available. Sign or load a document first.")
            return

        if not self.current_document:
            print("✗ No document loaded.")
            return

        try:
            is_valid = self.processor.verify_signature(
                self.current_document,
                self.current_signature
            )

            if is_valid:
                print("✓ Signature is VALID")
            else:
                print("✗ Signature is INVALID")

        except Exception as e:
            print(f"✗ Error: {e}")

    def save_document_signature(self):
        """Save document and signature to file"""
        print("\n--- Save Document + Signature ---")

        if not self.current_document:
            print("✗ No document loaded.")
            return

        if not hasattr(self, 'current_signature') or not self.current_signature:
            print("✗ No signature available.")
            return

        filename = input("Enter filename (e.g., doc_sig.json): ").strip()

        try:
            self.processor.save_document_signature_pair(
                self.current_document,
                self.current_signature,
                filename
            )
            print(f"✓ Document and signature saved to {filename}")
        except Exception as e:
            print(f"✗ Error: {e}")

    def load_document_signature(self):
        """Load document and signature from file"""
        print("\n--- Load Document + Signature ---")

        filename = input("Enter filename: ").strip()

        if not Path(filename).exists():
            print(f"✗ File {filename} not found")
            return

        try:
            self.current_document, self.current_signature = \
                self.processor.load_document_signature_pair(filename)

            print(f"\n✓ Loaded from {filename}")
            print(f"  Document ID: {self.current_document.id}")
            print(f"  Author: {self.current_document.author_id}")
            print(f"  Addressee: {self.current_document.addressee_id}")
            print(f"  Paragraphs: {len(self.current_document.content)}")
            print(f"  Signator ID: {self.current_signature.signator_id}")
            print(f"  Signed at: {self.current_signature.signed_at}")

        except Exception as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    client = DocumentClient()
    client.run()
