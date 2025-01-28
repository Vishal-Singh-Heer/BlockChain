import os
import json
import time
import hashlib
import base64
from typing import Optional, Dict, List, Tuple
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from dataclasses import dataclass, asdict
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class Transaction:
    sender: str
    recipient: str
    amount: float
    timestamp: float
    nonce: int
    fee: float
    data: Optional[Dict] = None
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

    def calculate_hash(self) -> str:
        tx_dict = self.to_dict()
        tx_dict.pop('signature', None)  # Remove signature for hash calculation
        return hashlib.sha256(json.dumps(tx_dict, sort_keys=True).encode()).hexdigest()

class Wallet:
    def __init__(self, private_key: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize a wallet with an optional private key and password.
        If no private key is provided, a new one will be generated.
        """
        self.version = "1.0.0"
        if private_key:
            self._private_key = self._load_private_key(private_key, password)
        else:
            self._private_key = ec.generate_private_key(ec.SECP256K1())
            
        self._public_key = self._private_key.public_key()
        self.address = self._generate_address()
        self.transaction_history: List[Transaction] = []
        self.nonce = 0

    def _generate_address(self) -> str:
        """
        Generate a wallet address from the public key using a more secure method.
        """
        # Get public key in compressed format
        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint
        )
        
        # Double hash with SHA256 and RIPEMD160
        sha256_hash = hashlib.sha256(public_bytes).digest()
        ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
        
        # Add version byte (0x00 for mainnet)
        versioned_hash = b'\x00' + ripemd160_hash
        
        # Add checksum
        checksum = hashlib.sha256(hashlib.sha256(versioned_hash).digest()).digest()[:4]
        binary_address = versioned_hash + checksum
        
        # Encode in base58
        alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        value = int.from_bytes(binary_address, byteorder='big')
        result = ''
        while value:
            value, mod = divmod(value, 58)
            result = alphabet[mod] + result
            
        # Add leading zeros from version byte
        for byte in versioned_hash:
            if byte == 0:
                result = alphabet[0] + result
            else:
                break
                
        return result

    def create_transaction(
        self,
        recipient: str,
        amount: float,
        fee: float = 0.0001,
        data: Optional[Dict] = None
    ) -> Transaction:
        """
        Create a new transaction.
        """
        if not self._is_valid_address(recipient):
            raise ValueError("Invalid recipient address")
            
        if amount <= 0:
            raise ValueError("Amount must be positive")
            
        if fee < 0:
            raise ValueError("Fee cannot be negative")
            
        transaction = Transaction(
            sender=self.address,
            recipient=recipient,
            amount=amount,
            timestamp=time.time(),
            nonce=self.nonce,
            fee=fee,
            data=data
        )
        
        # Sign the transaction
        transaction.signature = self._sign_transaction(transaction)
        self.nonce += 1
        
        return transaction

    def _sign_transaction(self, transaction: Transaction) -> str:
        """
        Sign a transaction with the private key.
        """
        tx_hash = transaction.calculate_hash()
        signature = self._private_key.sign(
            bytes.fromhex(tx_hash),
            ec.ECDSA(hashes.SHA256())
        )
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def verify_transaction(transaction: Transaction, public_key_bytes: bytes) -> bool:
        """
        Verify a transaction's signature.
        """
        try:
            public_key = serialization.load_pem_public_key(public_key_bytes)
            signature = base64.b64decode(transaction.signature)
            tx_hash = bytes.fromhex(transaction.calculate_hash())
            
            public_key.verify(
                signature,
                tx_hash,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except (InvalidSignature, ValueError):
            return False

    def export_wallet(self, password: str, filename: str = None) -> Optional[str]:
        """
        Export the wallet to an encrypted file or return encrypted data.
        """
        if not password:
            raise ValueError("Password is required for wallet export")
            
        encrypted_key = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password.encode())
        )
        
        wallet_data = {
            'version': self.version,
            'private_key': base64.b64encode(encrypted_key).decode('utf-8'),
            'address': self.address,
            'nonce': self.nonce
        }
        
        if filename:
            with open(filename, 'w') as f:
                json.dump(wallet_data, f)
            return None
        else:
            return json.dumps(wallet_data)

    @classmethod
    def import_wallet(cls, password: str, filename: Optional[str] = None, data: Optional[str] = None) -> 'Wallet':
        """
        Import a wallet from an encrypted file or data string.
        """
        if filename and data:
            raise ValueError("Provide either filename or data, not both")
            
        if filename:
            with open(filename, 'r') as f:
                wallet_data = json.load(f)
        else:
            wallet_data = json.loads(data)
            
        encrypted_key = base64.b64decode(wallet_data['private_key'])
        
        # Create wallet instance
        wallet = cls(encrypted_key, password)
        wallet.nonce = wallet_data.get('nonce', 0)
        
        if wallet.address != wallet_data['address']:
            raise ValueError("Address mismatch in imported wallet")
            
        return wallet

    def _load_private_key(self, key_data: str, password: Optional[str]) -> ec.EllipticCurvePrivateKey:
        """
        Load a private key from encrypted data.
        """
        try:
            if password:
                return serialization.load_pem_private_key(
                    base64.b64decode(key_data),
                    password=password.encode()
                )
            else:
                return serialization.load_pem_private_key(
                    base64.b64decode(key_data),
                    password=None
                )
        except Exception as e:
            raise ValueError(f"Failed to load private key: {str(e)}")

    @staticmethod
    def _is_valid_address(address: str) -> bool:
        """
        Validate a wallet address format and checksum.
        """
        try:
            # Decode base58
            alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
            value = 0
            for char in address:
                value = value * 58 + alphabet.index(char)
                
            # Convert to bytes
            binary_address = value.to_bytes((value.bit_length() + 7) // 8, byteorder='big')
            
            # Check length
            if len(binary_address) != 25:
                return False
                
            # Verify checksum
            versioned_hash = binary_address[:-4]
            checksum = binary_address[-4:]
            calculated_checksum = hashlib.sha256(hashlib.sha256(versioned_hash).digest()).digest()[:4]
            
            return checksum == calculated_checksum
        except Exception:
            return False

    def get_balance(self, blockchain) -> float:
        """
        Calculate wallet balance from blockchain.
        """
        balance = 0.0
        seen_transactions = set()
        
        for block in blockchain.chain:
            for tx in block.transactions:
                tx_hash = tx.calculate_hash()
                if tx_hash in seen_transactions:
                    continue
                    
                seen_transactions.add(tx_hash)
                if tx.recipient == self.address:
                    balance += tx.amount
                if tx.sender == self.address:
                    balance -= (tx.amount + tx.fee)
                    
        return balance

    def get_transaction_history(self, blockchain) -> List[Dict]:
        """
        Get detailed transaction history from blockchain.
        """
        history = []
        seen_transactions = set()
        
        for block in blockchain.chain:
            block_transactions = []
            for tx in block.transactions:
                tx_hash = tx.calculate_hash()
                if tx_hash in seen_transactions:
                    continue
                    
                if tx.sender == self.address or tx.recipient == self.address:
                    block_transactions.append({
                        'hash': tx_hash,
                        'type': 'sent' if tx.sender == self.address else 'received',
                        'counterparty': tx.recipient if tx.sender == self.address else tx.sender,
                        'amount': tx.amount,
                        'fee': tx.fee,
                        'timestamp': tx.timestamp,
                        'block_height': block.height,
                        'confirmations': blockchain.get_current_height() - block.height + 1,
                        'data': tx.data
                    })
                    seen_transactions.add(tx_hash)
                    
            if block_transactions:
                history.extend(block_transactions)
                
        return sorted(history, key=lambda x: x['timestamp'], reverse=True)