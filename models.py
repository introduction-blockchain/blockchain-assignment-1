import hashlib
import json
import time
from typing import List
from pydantic import BaseModel

# --- Pydantic Models (สำหรับ API & Validation) ---

class XRayResult(BaseModel):
    """ข้อมูลผลลัพธ์จาก AI"""
    diagnosis: str
    confidence_score: float
    ipfs_image_hash: str

class Data(BaseModel):
    """ข้อมูลธุรกรรมที่จะบันทึกลง Block"""
    id: str             # Unique ID ของรายการนี้
    doctor_public_key: str
    patient_hash_id: str
    ai_result: XRayResult
    timestamp: float

class AIRequest(BaseModel):
    """รูปแบบข้อมูล Request ที่ส่งเข้ามาทาง API"""
    image_base64: str
    doctor_id: str
    patient_id: str

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
        # แปลง Data object กลับเป็น dict เพื่อทำ JSON Dump
        data_dicts = [tx.dict() for tx in self.data]
        
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": data_dicts,
            "previous_hash": self.previous_hash,
            "validator": self.validator,
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()