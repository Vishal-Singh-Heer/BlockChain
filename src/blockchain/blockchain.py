from typing import List, Optional, Dict, Set
from collections import defaultdict
import time
from .block import Block, Transaction
from ..consensus.proof_of_work import ProofOfWork
from ..utils.logger import get_logger

logger = get_logger(__name__)

class Blockchain:
    def __init__(self, difficulty: int = 4):
        self.difficulty = difficulty
        self.unconfirmed_transactions: List[Transaction] = []
        self.chain: List[Block] = []
        self.orphan_blocks: Dict[str, Block] = {}  # hash -> block
        self.pending_blocks: Dict[str, Block] = {}  # hash -> block
        self.known_transactions: Set[str] = set()
        self.pow = ProofOfWork(difficulty)
        self.create_genesis_block()

    def create_genesis_block(self) -> None:
        """Create and add the genesis block to the chain."""
        genesis_tx = Transaction(
            sender="0",
            recipient="Genesis",
            amount=0,
            signature="0",
            timestamp=0
        )
        genesis_block = Block(
            miner="Genesis",
            transactions=[genesis_tx],
            previous_hash="0" * 64,
            timestamp=0,
            difficulty=self.difficulty
        )
        self.chain.append(genesis_block)

    @property
    def last_block(self) -> Block:
        """Get the latest block in the chain."""
        return self.chain[-1]

    def add_transaction(self, transaction: Transaction) -> bool:
        """Add a new transaction to the pool if valid."""
        # Check if transaction already exists
        tx_hash = transaction.calculate_hash()
        if tx_hash in self.known_transactions:
            return False

        # Validate transaction
        if not self.validate_transaction(transaction):
            return False

        self.unconfirmed_transactions.append(transaction)
        self.known_transactions.add(tx_hash)
        return True

    def validate_transaction(self, transaction: Transaction) -> bool:
        """Validate a transaction."""
        # Basic validation
        if not transaction.sender or not transaction.recipient:
            return False
        if transaction.amount <= 0:
            return False
        if not transaction.signature:
            return False
        
        # Add more complex validation (e.g., check balance, verify signature)
        return True

    def mine_block(self, miner_address: str) -> Optional[Block]:
        """Mine a new block with current transactions."""
        if not self.unconfirmed_transactions:
            return None

        last_block = self.last_block
        new_block = Block(
            miner=miner_address,
            transactions=self.unconfirmed_transactions[:10],  # Limit transactions per block
            previous_hash=last_block.hash,
            difficulty=self.difficulty
        )

        # Perform proof of work
        if self.pow.mine(new_block):
            # Clear mined transactions and add block
            self.unconfirmed_transactions = self.unconfirmed_transactions[10:]
            if self.add_block(new_block):
                return new_block
        return None

    def add_block(self, block: Block) -> bool:
        """Add a new block to the chain if valid."""
        # Validate block
        if not block.is_valid():
            logger.warning(f"Invalid block received: {block.hash}")
            return False

        # Check if block connects to our chain
        if block.previous_hash == self.last_block.hash:
            # Validate proof of work
            if not self.pow.validate(block):
                logger.warning(f"Invalid proof of work for block: {block.hash}")
                return False

            self.chain.append(block)
            logger.info(f"Added new block to chain: {block.hash}")
            
            # Process any pending blocks that might connect
            self._process_pending_blocks()
            return True
        else:
            # Store as pending block
            self.pending_blocks[block.hash] = block
            return False

    def _process_pending_blocks(self) -> None:
        """Process pending blocks that might now connect to the chain."""
        added_blocks = True
        while added_blocks:
            added_blocks = False
            for block_hash, block in list(self.pending_blocks.items()):
                if block.previous_hash == self.last_block.hash:
                    if self.add_block(block):
                        del self.pending_blocks[block_hash]
                        added_blocks = True
                        break

    def get_balance(self, address: str) -> float:
        """Calculate the balance for an address."""
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.recipient == address:
                    balance += tx.amount
                if tx.sender == address:
                    balance -= tx.amount
        return balance

    def verify_chain(self) -> bool:
        """Verify the entire blockchain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]

            # Check block integrity
            if not current.is_valid():
                return False

            # Verify block connection
            if current.previous_hash != previous.hash:
                return False

            # Verify proof of work
            if not self.pow.validate(current):
                return False

        return True

    def get_chain_data(self) -> dict:
        """Get blockchain data for network synchronization."""
        return {
            'length': len(self.chain),
            'chain': [block.to_dict() for block in self.chain],
            'difficulty': self.difficulty
        }

    def replace_chain(self, new_chain: List[Block]) -> bool:
        """Replace current chain with a new, valid chain."""
        # Validate new chain
        if not self._validate_chain(new_chain):
            return False

        # Check if new chain is longer
        if len(new_chain) <= len(self.chain):
            return False

        # Replace chain
        self.chain = new_chain
        return True

    def _validate_chain(self, chain: List[Block]) -> bool:
        """Validate a potential new chain."""
        if not chain or len(chain) < 1:
            return False

        # Validate genesis block
        if chain[0].hash != self.chain[0].hash:
            return False

        # Validate remaining blocks
        for i in range(1, len(chain)):
            if not chain[i].is_valid():
                return False
            if chain[i].previous_hash != chain[i-1].hash:
                return False
            if not self.pow.validate(chain[i]):
                return False

        return True