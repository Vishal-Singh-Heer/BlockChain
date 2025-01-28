from dataclasses import dataclass
from typing import List, Optional
import time
import hashlib
import json
from ..utils.crypto import hash_data

@dataclass
class Transaction:
    sender: str
    recipient: str
    amount: float
    signature: Optional[str] = None
    timestamp: float = time.time()

    def to_dict(self) -> dict:
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'signature': self.signature,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        return cls(**data)

class Block:
    def __init__(
        self,
        miner: str,
        transactions: List[Transaction],
        previous_hash: str,
        timestamp: Optional[float] = None,
        nonce: int = 0,
        difficulty: int = 4
    ):
        self.version = "1.0"
        self.timestamp = timestamp or time.time()
        self.previous_hash = previous_hash
        self.miner = miner
        self.transactions = transactions
        self.nonce = nonce
        self.difficulty = difficulty
        self.merkle_root = self._calculate_merkle_root()
        self.hash = self.calculate_hash()

    def _calculate_merkle_root(self) -> str:
        if not self.transactions:
            return hash_data("empty_block")
        
        leaves = [hash_data(tx.to_dict()) for tx in self.transactions]
        while len(leaves) > 1:
            if len(leaves) % 2 == 1:
                leaves.append(leaves[-1])
            leaves = [hash_data(leaves[i] + leaves[i + 1]) 
                     for i in range(0, len(leaves), 2)]
        return leaves[0]

    def calculate_hash(self) -> str:
        block_dict = {
            'version': self.version,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'miner': self.miner,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'nonce': self.nonce,
            'difficulty': self.difficulty,
            'merkle_root': self.merkle_root
        }
        return hash_data(block_dict)

    def to_dict(self) -> dict:
        return {
            'version': self.version,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'miner': self.miner,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'nonce': self.nonce,
            'difficulty': self.difficulty,
            'merkle_root': self.merkle_root,
            'hash': self.hash
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Block':
        transactions = [Transaction.from_dict(tx) for tx in data['transactions']]
        block = cls(
            miner=data['miner'],
            transactions=transactions,
            previous_hash=data['previous_hash'],
            timestamp=data['timestamp'],
            nonce=data['nonce'],
            difficulty=data['difficulty']
        )
        block.hash = data['hash']
        return block

    def is_valid(self) -> bool:
        """Verify block integrity."""
        if self.hash != self.calculate_hash():
            return False
        if not self.hash.startswith('0' * self.difficulty):
            return False
        if not all(isinstance(tx, Transaction) for tx in self.transactions):
            return False
        return True