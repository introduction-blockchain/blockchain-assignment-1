# main.py
import uuid
import time
import hashlib
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import Models
from models import AIRequest, Data, XRayResult, DecryptRequest, SensitiveData
# Import Blockchain Logic
from blockchain import MedicalBlockchain
# Import Crypto Logic (จากไฟล์ใหม่ที่เราสร้าง)
from crypto_utils import generate_key_pair, encrypt_data, decrypt_data

app = FastAPI()

# Initialize System
class DoctorKeyRequest(BaseModel):
    doctor_name: str
    
blockchain = MedicalBlockchain()
key_inventory = []

# Register Mock Nodes
blockchain.register_node("Bangkok Hospital Core", reputation=90)
blockchain.register_node("Research Center AI", reputation=50)
blockchain.register_node("General Clinic Node", reputation=10)
    
# --- API Endpoints ---
@app.get("/generate_keys")
def api_generate_keys(request: DoctorKeyRequest):
    """
    Utility: สร้าง Key Pair และบันทึกเก็บไว้ในระบบ (เพื่อความสะดวกในการ Demo)
    """
    try:
        private_key, public_key = generate_key_pair()
        
        # เก็บข้อมูลลงใน Inventory เพื่อใช้เรียกดูภายหลัง
        key_data = {
            "doctor_name": request.doctor_name,
            "doctor_public_key": public_key,
            "doctor_private_key": private_key,
            "created_at": time.ctime()
        }
        key_inventory.append(key_data)
        
        return {
            "note": "Keys saved to inventory for demo purposes.",
            "data": key_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/get_all_keys")
def get_all_keys():
    """
    API พิเศษสำหรับ Demo: ดู Key ทั้งหมดที่เคย Generate ไว้ใน Session นี้
    """
    if not key_inventory:
        return {"message": "No keys generated yet."}
    return {
        "count": len(key_inventory),
        "keys": key_inventory
    }

@app.post("/create_block")
def create_block(request: AIRequest):
    """
    รับข้อมูลคนไข้ -> เข้ารหัสข้อมูลลับ -> AI ประมวลผล -> ลง Block
    """
    authorized_keys = [k["doctor_public_key"] for k in key_inventory]
    if request.doctor_public_key not in authorized_keys:
        raise HTTPException(
            status_code=401, 
            detail="Unauthorized: This Public Key is not registered in the system."
        )
        
    # 1. Mock AI Process
    mock_diseases = ["Pneumonia", "Tuberculosis", "Normal", "Covid-19"]
    diagnosis = random.choice(mock_diseases)
    ipfs_hash = f"QmHash{uuid.uuid4().hex[:10]}"

    # 2. Prepare Sensitive Data
    sensitive_info = {
        "name": request.patient_name,
        "age": request.patient_age,
        "symptoms": request.symptoms,
        "doctor_notes": f"Initial diagnosis: {diagnosis}"
    }
    
    # 3. Encrypt Data (เรียกใช้ function จาก crypto_utils)
    try:
        encrypted_blob = encrypt_data(sensitive_info, request.doctor_public_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 4. Create Data Object (On-Chain Data)
    data = Data( 
        id=uuid.uuid4().hex,
        doctor_public_key=request.doctor_public_key,
        patient_hash_id=hashlib.sha256(request.patient_id.encode()).hexdigest(),
        encrypted_data=encrypted_blob, 
        ai_result=XRayResult(
            diagnosis=diagnosis,
            ipfs_image_hash=ipfs_hash
        ),
        timestamp=time.time(),
    )
    
    blockchain.add_data(data)
    mining_result = blockchain.create_block()
    
    if not mining_result:
        raise HTTPException(status_code=500, detail="Mining failed")

    return {
        "status": "Success",
        "message": "Data encrypted and recorded on chain.",
        "ai_summary": diagnosis,
        "mining_info": mining_result
    }

@app.get("/chain")
def get_chain():
    """ดู Blockchain"""
    return blockchain.chain

@app.post("/my_patient_history")
def get_decrypted_chain(req: DecryptRequest):
    """
    ดูประวัติคนไข้ของหมอคนนี้ (ต้องใช้ Private Key ถอดรหัส)
    """
    my_records = []
    
    for block in blockchain.chain:
        for tx in block.data:
            # เช็คว่าเป็นเคสของหมอคนนี้ไหม
            if tx.doctor_public_key.strip() == req.doctor_public_key.strip():
                
                try:
                    # Decrypt Data (เรียกใช้ function จาก crypto_utils)
                    decrypted_info = decrypt_data(tx.encrypted_data, req.doctor_private_key)
                    
                    my_records.append({
                        "block_index": block.index,
                        "timestamp": tx.timestamp,
                        "ai_diagnosis": tx.ai_result,
                        "patient_sensitive_data": decrypted_info
                    })
                except ValueError:
                    # กรณีถอดรหัสไม่ได้ (เช่น Key ผิด) ให้ข้าม หรือแจ้ง Error เฉพาะรายการ
                    continue
    
    if not my_records:
        return {"message": "No records found or Decryption failed (Wrong Key)."}
        
    return {
        "doctor_records_count": len(my_records),
        "records": my_records
    }
    
@app.get("/nodes")
def get_nodes():
    """ดูรายชื่อ Nodes และคะแนน Reputation"""
    return [{
        "name": n.name, 
        "reputation": n.reputation
    } for n in blockchain.nodes]

@app.get("/integrity_check")
def check_integrity():
    """ตรวจสอบความถูกต้องของ Chain"""
    for i in range(1, len(blockchain.chain)):
        previous = blockchain.chain[i-1]
        current = blockchain.chain[i]
        
        if current.previous_hash != previous.hash:
            return {"status": "CORRUPTED", "block_index": i, "reason": "Link Broken"}
        
        if current.calculate_hash() != current.hash:
            return {"status": "TAMPERED", "block_index": i, "reason": "Data Modified"}
            
    return {"status": "SECURE", "message": "Blockchain is valid."}