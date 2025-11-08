import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Generate a real key pair
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

# Get public key in PEM format
public_key = private_key.public_key()
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode('utf-8')

# Prepare the payload
payload = {
    "signer_id": 42,
    "public_key_pem": public_pem
}

# Make the POST request
response = requests.post(
    "http://localhost:8000/keys/add",
    json=payload
)

print("Adding key...", payload)

# Check the response
if response.status_code == 201:
    print("✓ Key added successfully")
    print(response.json())
else:
    print(f"✗ Error {response.status_code}")
    print(response.json())
