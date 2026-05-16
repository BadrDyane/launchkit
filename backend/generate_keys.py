# launchkit/backend/generate_keys.py
"""
Run once: python generate_keys.py
Generates RSA-2048 key pair into ./keys/
Never commit these files — they are in .gitignore.
"""
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

KEYS_DIR = Path(__file__).parent / "keys"
KEYS_DIR.mkdir(exist_ok=True)

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend(),
)

private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption(),
)

public_pem = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)

(KEYS_DIR / "private.pem").write_bytes(private_pem)
(KEYS_DIR / "public.pem").write_bytes(public_pem)

print("RSA key pair generated:")
print(f"  {KEYS_DIR / 'private.pem'}")
print(f"  {KEYS_DIR / 'public.pem'}")