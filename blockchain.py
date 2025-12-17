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

    def create_block(self):
        if not self.pending_data:
            return None

        # 1. เลือก Validator (Consensus)
        validator = self.select_validator()
        if not validator:
            return None

        # 2. สร้าง Block
        previous_block = self.get_previous_block()
        new_block = Block(
            index=len(self.chain),
            data=self.pending_data.copy(), # Copy ข้อมูลมาใส่ Block
            previous_hash=previous_block.hash,
            validator=validator.name,
        )

        # 3. บันทึกลง Chain
        self.chain.append(new_block)
        
        # 4. เคลียร์ Pending Data
        self.pending_data = []

        return {
            "message": "Block Mined Successfully",
            "block_index": new_block.index,
            "validator": validator.name,          # ใครเป็นคนสร้าง
            "validator_reputation": validator.reputation, # คะแนนความน่าเชื่อถือตอนสร้าง
            "block_hash": new_block.hash
        }