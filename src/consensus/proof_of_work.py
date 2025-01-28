import time
from typing import Optional
from ..blockchain.block import Block
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ProofOfWork:
    def __init__(self, difficulty: int = 4):
        self.difficulty = difficulty
        self.target = '0' * difficulty

    def mine(self, block: Block) -> bool:
        """
        Mine a block by finding a nonce that satisfies the difficulty requirement.
        Returns True if successful, False if mining was interrupted.
        """
        start_time = time.time()
        max_nonce = 2 ** 32  # 4 billion attempts max
        
        logger.info(f"Starting mining block at height {block.height}")
        
        for nonce in range(max_nonce):
            if nonce % 100000 == 0:  # Log progress periodically
                logger.debug(f"Mining attempt {nonce}, elapsed time: {time.time() - start_time:.2f}s")
            
            block.nonce = nonce
            block_hash = block.calculate_hash()
            
            if block_hash.startswith(self.target):
                mining_time = time.time() - start_time
                logger.info(f"Block mined! Nonce: {nonce}, Time: {mining_time:.2f}s, Hash: {block_hash}")
                block.hash = block_hash
                return True
                
        logger.warning("Mining failed - reached maximum nonce value")
        return False

    def validate(self, block: Block) -> bool:
        """
        Validate the proof of work for a block.
        """
        block_hash = block.calculate_hash()
        
        # Verify hash matches stored hash
        if block_hash != block.hash:
            logger.warning(f"Block hash mismatch. Calculated: {block_hash}, Stored: {block.hash}")
            return False
            
        # Verify hash meets difficulty requirement
        if not block_hash.startswith(self.target):
            logger.warning(f"Block hash doesn't meet difficulty requirement. Hash: {block_hash}")
            return False
            
        return True

    def adjust_difficulty(self, 
                        recent_blocks: list[Block], 
                        target_block_time: int = 600) -> Optional[int]:
        """
        Adjust mining difficulty based on recent block times.
        Returns new difficulty or None if no adjustment needed.
        """
        if len(recent_blocks) < 10:
            return None
            
        # Calculate average block time
        block_times = []
        for i in range(1, len(recent_blocks)):
            time_diff = recent_blocks[i].timestamp - recent_blocks[i-1].timestamp
            block_times.append(time_diff)
            
        avg_block_time = sum(block_times) / len(block_times)
        
        # Adjust difficulty if average block time is too far from target
        if avg_block_time < target_block_time * 0.5:
            return self.difficulty + 1
        elif avg_block_time > target_block_time * 1.5:
            return max(1, self.difficulty - 1)
            
        return None