# crypto_utils.py
import base64
import json
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

def generate_key_pair():
    """
    สร้าง RSA Key Pair (Public/Private) ขนาด 2048 bit
    Return: (private_key_str, public_key_str)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Export Private Key
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Export Public Key
    pem_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return pem_private.decode('utf-8'), pem_public.decode('utf-8')

def encrypt_data(data_dict: dict, public_key_str: str) -> str:
    """
    เข้ารหัส Dictionary เป็น String (Base64) โดยใช้ Public Key
    """
    try:
        # 1. Load Public Key
        public_key = serialization.load_pem_public_key(
            public_key_str.encode()
        )
        
        # 2. Convert Data to JSON Bytes
        data_bytes = json.dumps(data_dict).encode('utf-8')
        
        # 3. Encrypt using RSA
        encrypted = public_key.encrypt(
            data_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # 4. Return as Base64 String
        return base64.b64encode(encrypted).decode('utf-8')
        
    except Exception as e:
        # ส่ง Error กลับไปให้ main.py จัดการ
        raise ValueError(f"Encryption Failed: {str(e)}")

def decrypt_data(encrypted_b64: str, private_key_str: str) -> dict:
    """
    ถอดรหัส String (Base64) กลับเป็น Dictionary โดยใช้ Private Key
    """
    try:
        # 1. Load Private Key
        private_key = serialization.load_pem_private_key(
            private_key_str.encode(),
            password=None
        )
        
        # 2. Decode Base64 to Bytes
        encrypted_bytes = base64.b64decode(encrypted_b64)
        
        # 3. Decrypt using RSA
        original_data = private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # 4. Convert Bytes back to Dict
        return json.loads(original_data.decode('utf-8'))
        
    except Exception as e:
        raise ValueError(f"Decryption Failed: {str(e)}")
    