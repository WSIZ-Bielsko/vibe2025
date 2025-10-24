#!/bin/bash

# Script to generate RSA key pair for DocumentProcessor
# Usage: ./generate_keys.sh [key_name] [key_size] [password]

set -e  # Exit on error

# Default values
KEY_NAME="${1:-document_key}"
KEY_SIZE="${2:-2048}"
PASSWORD="${3:-}"

# Output directory
OUTPUT_DIR="${4:-.}"
mkdir -p "$OUTPUT_DIR"

# File paths
TEMP_KEYPAIR="$OUTPUT_DIR/${KEY_NAME}_temp.pem"
PRIVATE_KEY="$OUTPUT_DIR/${KEY_NAME}_private.pem"
PUBLIC_KEY="$OUTPUT_DIR/${KEY_NAME}_public.pem"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Generating RSA key pair...${NC}"
echo "Key name: $KEY_NAME"
echo "Key size: $KEY_SIZE bits"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Step 1: Generate RSA key pair
echo -e "${BLUE}[1/3] Generating RSA key pair...${NC}"
openssl genrsa -out "$TEMP_KEYPAIR" "$KEY_SIZE" 2>/dev/null

# Step 2: Convert private key to PKCS8 format
echo -e "${BLUE}[2/3] Converting to PKCS8 format...${NC}"
if [ -n "$PASSWORD" ]; then
    # With password protection
    openssl pkcs8 -topk8 -inform PEM -outform PEM \
        -in "$TEMP_KEYPAIR" \
        -out "$PRIVATE_KEY" \
        -passout "pass:$PASSWORD"
    echo "Private key encrypted with password"
else
    # Without password protection
    openssl pkcs8 -topk8 -inform PEM -outform PEM -nocrypt \
        -in "$TEMP_KEYPAIR" \
        -out "$PRIVATE_KEY"
    echo "Private key saved without encryption"
fi

# Step 3: Extract public key
echo -e "${BLUE}[3/3] Extracting public key...${NC}"
openssl rsa -in "$TEMP_KEYPAIR" -pubout -out "$PUBLIC_KEY" 2>/dev/null

# Clean up temporary file
rm "$TEMP_KEYPAIR"

# Display results
echo ""
echo -e "${GREEN}✓ Key generation complete!${NC}"
echo ""
echo "Files created:"
echo "  Private key: $PRIVATE_KEY"
echo "  Public key:  $PUBLIC_KEY"
echo ""

# Show key information
echo "Key information:"
openssl rsa -in "$PRIVATE_KEY" -noout -text -passin "pass:$PASSWORD" 2>/dev/null | head -n 1

# Set proper permissions
chmod 600 "$PRIVATE_KEY"
chmod 644 "$PUBLIC_KEY"

echo ""
echo "Permissions set:"
echo "  Private key: 600 (owner read/write only)"
echo "  Public key:  644 (owner read/write, others read)"
echo ""
echo -e "${GREEN}Done!${NC}"
