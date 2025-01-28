import hashlib
import json
from typing import Any, Union
import base64
import secrets

def hash_data(data: Union[str, dict, bytes]) -> str:
    """
    Create a SHA-256 hash of the input data.
    Handles different input types appropriately.
    """
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True)
    
    if isinstance(data, str):
        data = data.encode('utf-8')
        
    return hashlib.sha256(data).hexdigest()

def generate_nonce(length: int = 32) -> str:
    """
    Generate a cryptographically secure random nonce.
    """
    return secrets.token_hex(length)

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Hash a password using PBKDF2 with a random salt.
    Returns (hash, salt).
    """
    if not salt:
        salt = secrets.token_hex(16)
        
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # Number of iterations
    )
    
    return base64.b64encode(key).decode('utf-8'), salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    Verify a password against its hash and salt.
    """
    new_hash, _ = hash_password(password, salt)
    return new_hash == password_hash

def create_signature(private_key: str, data: Union[str, dict]) -> str:
    """
    Create a digital signature for data using a private key.
    """
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True)
        
    key_bytes = base64.b64decode(private_key)
    signature = private_key_obj.sign(
        data.encode('utf-8'),
        hashfunc=hashlib.sha256
    )
    
    return base64.b64encode(signature).decode('utf-8')

def verify_signature(public_key: str, signature: str, data: Union[str, dict]) -> bool:
    """
    Verify a digital signature using a public key.
    """
    try:
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
            
        key_bytes = base64.b64decode(public_key)
        signature_bytes = base64.b64decode(signature)
        
        public_key_obj.verify(
            signature_bytes,
            data.encode('utf-8'),
            hashfunc=hashlib.sha256
        )
        return True
    except Exception:
        return False