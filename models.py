import hashlib
import json
import time
from typing import List, Optional
from pydantic import BaseModel

# --- Pydantic Models (สำหรับ API & Validation) ---

class XRayResult(BaseModel):
    """ข้อมูลผลลัพธ์จาก AI"""
    diagnosis: str
    ipfs_image_hash: str

class SensitiveData(BaseModel):
    """ข้อมูลส่วนตัวคนไข้ (จะถูกเข้ารหัสก่อนลง Block)"""
    patient_name: str
    patient_age: int
    symptoms: str
    doctor_notes: str

class Data(BaseModel):
    """ข้อมูลธุรกรรมที่จะบันทึกลง Block"""
    id: str             
    doctor_public_key: str      # Public Key เพื่อระบุตัวตนหมอ (และใช้ Verify)
    patient_hash_id: str        # Hash ไอดีคนไข้ (ไว้ค้นหาแบบไม่ระบุตัวตน)
    encrypted_data: str         # <--- ข้อมูล SensitiveData ที่ถูกเข้ารหัสแล้ว (Base64)
    ai_result: XRayResult

class AIRequest(BaseModel):
    """Request สร้าง Block: ต้องส่ง Public Key มาด้วยเพื่อใช้เข้ารหัส"""
    image_base64: str
    patient_id: str
    
    # ข้อมูลส่วนตัวคนไข้
    patient_name: str
    patient_age: int
    symptoms: str
    
    # Key ของหมอ (User สร้างเองแล้วส่งมา)
    doctor_public_key: str 

class DecryptRequest(BaseModel):
    """Request สำหรับขอดูข้อมูลแบบถอดรหัส"""
    doctor_public_key: str
    doctor_private_key: str  # ต้องใช้ Private Key เพื่อปลดล็อคข้อมูล

# --- Python Classes (สำหรับโครงสร้างภายใน Blockchain) ---

class Node:
    """ตัวแทนโรงพยาบาล/Node ในระบบ"""
    def __init__(self, node_id: str, name: str, reputation: int):
        self.node_id = node_id
        self.name = name
        self.reputation = reputation
        self.balance = 0.0

class Block:
    """โครงสร้างบล็อก"""
    def __init__(self, index: int, data: List[Data], previous_hash: str, validator: str):
        self.index = index
        self.timestamp = time.time()
        self.data = data
        self.previous_hash = previous_hash
        self.validator = validator
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """คำนวณ Hash ของบล็อก"""
        data_dicts = [tx.dict() for tx in self.data]
        
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": data_dicts,
            "previous_hash": self.previous_hash,
            "validator": self.validator,
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()