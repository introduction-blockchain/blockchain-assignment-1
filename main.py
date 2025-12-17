import uuid
import time
import hashlib
import random
from fastapi import FastAPI, HTTPException
from models import AIRequest, Data, XRayResult
from blockchain import MedicalBlockchain

app = FastAPI()

# Initialize System
blockchain = MedicalBlockchain()

# --- Register Nodes (จำลองโหนดในระบบ) ---
# Reputation ต่างกันเพื่อให้เห็นผลของ Consensus ชัดเจน
blockchain.register_node("Bangkok Hospital Core", reputation=90)  # โอกาสได้เยอะสุด
blockchain.register_node("Research Center AI", reputation=50)     # โอกาสปานกลาง
blockchain.register_node("General Clinic Node", reputation=10)    # โอกาสน้อยสุด

@app.post("/create_block")
def create_block(request: AIRequest):
    """
    Simulate Full Flow: 
    Receive Image -> AI Process -> Create Data -> Mine Block (Consensus)
    """
    
    # --- Step 1: Mock AI Process ---
    mock_diseases = ["Pneumonia", "Tuberculosis", "Normal", "Covid-19"]
    diagnosis = random.choice(mock_diseases)
    confidence = round(random.uniform(0.75, 0.99), 4)
    ipfs_hash = f"QmHash{uuid.uuid4().hex[:10]}"

    # --- Step 2: Create Data Object ---
    data = Data( 
        id=uuid.uuid4().hex,
        doctor_public_key=request.doctor_id,
        patient_hash_id=hashlib.sha256(request.patient_id.encode()).hexdigest(),
        ai_result=XRayResult(
            diagnosis=diagnosis,
            confidence_score=confidence,
            ipfs_image_hash=ipfs_hash
        ),
        timestamp=time.time(),
    )
    
    # ใส่เข้า Mempool (Pending List)
    blockchain.add_data(data)
    
    # --- Step 3: Trigger Mining (Consensus working here) ---
    mining_result = blockchain.create_block()
    
    if not mining_result:
        raise HTTPException(status_code=500, detail="Mining failed")

    # --- Step 4: Return Result ---
    return {
        "status": "Success & Recorded on Chain",
        "ai_diagnosis": {
            "disease": diagnosis,
            "confidence": confidence
        },
        "consensus_result": mining_result # ดูว่า Node ไหนเป็นคนสร้าง Block นี้
    }

@app.get("/chain")
def get_chain():
    """ดู Blockchain ทั้งหมด"""
    return blockchain.chain

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