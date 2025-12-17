import uuid
import random
import time
from typing import List, Optional
from models import Node, Block, Data

class MedicalBlockchain:
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_data: List[Data] = []
        self.nodes: List[Node] = []
        
        # สร้าง Genesis Block
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], "0", "System")
        self.chain.append(genesis_block)

    def register_node(self, name: str, reputation: int) -> Node:
        node_id = str(uuid.uuid4())
        new_node = Node(node_id, name, reputation)
        self.nodes.append(new_node)
        return new_node

    def add_data(self, data: Data):
        self.pending_data.append(data)
        return True

    def get_previous_block(self):
        return self.chain[-1]

    # --- Consensus: Proof of Reputation & Validity (PoRV) ---
    def select_validator(self) -> Optional[Node]:
        """
        เลือกผู้สร้าง Block โดยใช้วิธี Weighted Random Selection
        Reputation สูง = มีโอกาสได้รับเลือกสูงกว่า
        """
        if not self.nodes:
            return None
        
        # 1. รวมคะแนน Reputation ทั้งหมดในระบบ
        total_reputation = sum(node.reputation for node in self.nodes)
        
        # กรณีไม่มีคะแนนเลย ให้สุ่มปกติ
        if total_reputation == 0:
            return random.choice(self.nodes)

        # 2. สุ่มตัวเลขเสี่ยงทาย (Dart throw) ตั้งแต่ 0 ถึง คะแนนรวม
        pick = random.uniform(0, total_reputation)
        
        # 3. วนลูปเช็คช่วงคะแนน (Cumulative Logic)
        current = 0
        for node in self.nodes:
            current += node.reputation
            # ถ้าแต้มที่สุ่มได้ อยู่ในช่วงคะแนนสะสมของ Node นี้ -> เลือก Node นี้
            if current > pick:
                return node
                
        # Fallback (ไม่ควรเกิดขึ้นถ้า Logic ถูก)
        return self.nodes[0]
    
    def validate_and_slash(self, new_block: Block):
        """
        จำลองกระบวนการที่ Node อื่นๆ ช่วยกันตรวจ Block ใหม่
        ถ้าเจอว่าข้อมูลผิด (Invalid) จะลด Reputation ของผู้สร้าง (Validator)
        """
        validator_node = next((n for n in self.nodes if n.name == new_block.validator), None)
        
        if not validator_node:
            return False

        # --- จำลองการตรวจสอบ Validity ---
        # สมมติ Logic ว่า: ถ้า AI Confidence ต่ำเกินไปแต่ดันทายผล 
        # หรือ Hash ไม่ตรง จะถือว่าเป็น Block ที่ไม่ Valid
        
        is_valid = True
        
        # ตัวอย่าง: ตรวจสอบ Integrity พื้นฐาน
        if new_block.calculate_hash() != new_block.hash:
            is_valid = False
            reason = "Hash Mismatch"
        
        # ตัวอย่าง: ตรวจสอบทางเกณฑ์การแพทย์ (Medical Validity Logic)
        # สมมติว่าถ้า Confidence ต่ำกว่า 0.8 แต่ระบบปล่อยผ่านมาได้ ถือว่า Node นี้ไม่มีคุณภาพ
        for data in new_block.data:
            if data.ai_result.confidence_score < 0.8:
                 is_valid = False
                 reason = "Low Confidence Accepted (Medical Risk)"
        
        # --- การให้รางวัล หรือ ลงโทษ ---
        if is_valid:
            # รางวัล: เพิ่ม Reputation เล็กน้อย (สร้าง Trust สะสม)
            validator_node.reputation += 1
            print(f"Block Validated: {validator_node.name} reputation increased to {validator_node.reputation}")
            return True
        else:
            # ลงโทษ (Slashing): ลด Reputation อย่างหนัก!
            # นี่คือจุดต่างสำคัญ: เขาไม่ได้เสียเงิน แต่เสีย "โอกาสในอนาคต" ที่จะถูกเลือกอีก
            validator_node.reputation = max(0, validator_node.reputation - 20)
            print(f"BLOCK REJECTED ({reason}): {validator_node.name} slashed to {validator_node.reputation}")
            return False

    def create_block(self):
        if not self.pending_data:
            return None

        # 1. เลือก Validator (Consensus: Weighted Random)
        validator = self.select_validator()
        if not validator:
            return None

        # 2. Validator สร้างร่าง Block ขึ้นมา (Block Proposal)
        previous_block = self.get_previous_block()
        new_block = Block(
            index=len(self.chain),
            data=self.pending_data.copy(),
            previous_hash=previous_block.hash,
            validator=validator.name,
        )

        # --- 3. จุดเรียกใช้ validate_and_slash (VALIDITY CHECK) ---
        # จำลองการที่ Node อื่นๆ รุมกันตรวจสอบ Block นี้
        is_block_valid = self.validate_and_slash(new_block)

        if not is_block_valid:
            # กรณี: ไม่ผ่านการตรวจสอบ (Validator โดน Slash ไปแล้วในฟังก์ชันนั้น)
            # เราจะไม่บันทึก Block นี้ลง Chain และแจ้งเตือนกลับไป
            return {
                "status": "REJECTED",
                "message": "Block validation failed due to invalid data.",
                "slashed_validator": validator.name,
                "current_reputation": validator.reputation
            }

        # 4. กรณีผ่าน: บันทึกลง Chain ถาวร
        self.chain.append(new_block)
        
        # 5. เคลียร์ Pending Data (Transaction ถูก Process แล้ว)
        self.pending_data = []

        return {
            "message": "Block Mined Successfully",
            "block_index": new_block.index,
            "validator": validator.name,
            "validator_reputation": validator.reputation,
            "block_hash": new_block.hash
        }