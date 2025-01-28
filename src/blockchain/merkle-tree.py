from typing import List, Optional
import hashlib
from ..utils.crypto import hash_data

class MerkleNode:
    def __init__(self, hash_value: str, left: Optional['MerkleNode'] = None, right: Optional['MerkleNode'] = None):
        self.hash = hash_value
        self.left = left
        self.right = right

class MerkleTree:
    def __init__(self, transactions: List[dict]):
        self.transactions = transactions
        self.leaves: List[MerkleNode] = []
        self.root: Optional[MerkleNode] = None
        self._build_tree()

    def _build_tree(self):
        """Build the Merkle tree from the transaction list."""
        # Create leaf nodes
        self.leaves = [MerkleNode(hash_data(tx)) for tx in self.transactions]
        
        # Handle empty transaction list
        if not self.leaves:
            self.root = MerkleNode(hash_data("empty_tree"))
            return
            
        # Build tree from leaves
        nodes = self.leaves
        while len(nodes) > 1:
            # Handle odd number of nodes
            if len(nodes) % 2 == 1:
                nodes.append(nodes[-1])
                
            # Create parent nodes
            parents = []
            for i in range(0, len(nodes), 2):
                combined_hash = hash_data(nodes[i].hash + nodes[i+1].hash)
                parent = MerkleNode(combined_hash, nodes[i], nodes[i+1])
                parents.append(parent)
                
            nodes = parents
            
        self.root = nodes[0]

    def get_root_hash(self) -> str:
        """Get the Merkle root hash."""
        return self.root.hash if self.root else ""

    def get_proof(self, transaction_hash: str) -> List[dict]:
        """
        Generate a Merkle proof for a transaction.
        Returns a list of hashes and their positions (left/right) needed to reconstruct the root.
        """
        if not self.root:
            return []
            
        # Find the leaf node
        leaf_index = -1
        for i, leaf in enumerate(self.leaves):
            if leaf.hash == transaction_hash:
                leaf_index = i
                break
                
        if leaf_index == -1:
            return []
            
        proof = []
        nodes = self.leaves
        current_index = leaf_index
        
        while len(nodes) > 1:
            # Handle odd number of nodes
            if len(nodes) % 2 == 1:
                nodes.append(nodes[-1])
                
            # Get sibling hash
            is_right = current_index % 2 == 0
            sibling_index = current_index + 1 if is_right else current_index - 1
            
            proof.append({
                'hash': nodes[sibling_index].hash,
                'position': 'right' if is_right else 'left'
            })
            
            # Move up to parent level
            parents = []
            for i in range(0, len(nodes), 2):
                combined_hash = hash_data(nodes[i].hash + nodes[i+1].hash)
                parent = MerkleNode(combined_hash, nodes[i], nodes[i+1])
                parents.append(parent)
                
            nodes = parents
            current_index = current_index // 2
            
        return proof

    @staticmethod
    def verify_proof(transaction_hash: str, proof: List[dict], root_hash: str) -> bool:
        """
        Verify a Merkle proof for a transaction.
        """
        current_hash = transaction_hash
        
        for step in proof:
            sibling_hash = step['hash']
            if step['position'] == 'left':
                current_hash = hash_data(sibling_hash + current_hash)
            else:
                current_hash = hash_data(current_hash + sibling_hash)
                
        return current_hash == root_hash