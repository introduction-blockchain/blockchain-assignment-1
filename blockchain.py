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
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], "0", "Genesis Block")
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

    def select_validator(self) -> Optional[Node]:
        if not self.nodes: return None
        total_reputation = sum(node.reputation for node in self.nodes)
        if total_reputation == 0: return random.choice(self.nodes)
        pick = random.uniform(0, total_reputation)
        current = 0
        for node in self.nodes:
            current += node.reputation
            if current > pick: return node
        return self.nodes[0]
    
    def validate_and_slash(self, new_block: Block):
        validator_node = next((n for n in self.nodes if n.name == new_block.validator), None)
        if not validator_node: return False

        is_valid = True
        if new_block.calculate_hash() != new_block.hash:
            is_valid = False
        
        if is_valid:
            validator_node.reputation += 1
            return True
        else:
            validator_node.reputation = max(0, validator_node.reputation - 20)
            return False

    def create_block(self):
        if not self.pending_data: return None
        validator = self.select_validator()
        if not validator: return None

        previous_block = self.get_previous_block()
        new_block = Block(
            index=len(self.chain),
            data=self.pending_data.copy(),
            previous_hash=previous_block.hash,
            validator=validator.name,
        )

        is_block_valid = self.validate_and_slash(new_block)
        if not is_block_valid:
            return None

        self.chain.append(new_block)
        self.pending_data = []

        return {
            "message": "Block Mined Successfully",
            "index": new_block.index,
            "validator": validator.name,
            "hash": new_block.hash
        }