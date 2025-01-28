# BlockChain

A sophisticated blockchain implementation in Python featuring advanced cryptography, proof-of-work consensus, secure wallet management, and asynchronous peer-to-peer networking.

## Features

### Advanced Blockchain Core
- Proof of Work consensus with dynamic difficulty adjustment
- Merkle tree implementation for efficient transaction verification
- Comprehensive block validation and chain integrity checks
- Orphaned block support and reconciliation
- Advanced transaction pool management with fee prioritization
- Memory-efficient block storage

### Enhanced Wallet System
- Secure wallet generation using ECDSA and SECP256K1 curve
- Password-protected key storage and management
- Transaction signing with nonce tracking
- Comprehensive transaction history tracking
- Balance management with UTXO tracking
- Support for custom transaction data
- Base58Check address encoding

### Asynchronous Networking
- Asynchronous peer-to-peer communication
- Advanced gossip protocol for network discovery
- Efficient block and transaction propagation
- Automatic peer management with health checks
- Network status monitoring and metrics
- Configurable peer limits and timeouts

### Security Features
- Advanced cryptographic signatures using ECDSA
- Multi-layer hash verification
- Secure nonce generation and validation
- Comprehensive transaction validation
- Protected wallet generation and storage
- Double-spend prevention

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/BlockChain.git
cd BlockChain
```

2. Create and activate virtual environment:
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Unix/macOS
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Initialize Node and Wallet

```python
from blockchain.core import Blockchain
from blockchain.networking import GossipProtocol
from blockchain.wallet import Wallet

# Create and configure blockchain
blockchain = Blockchain(difficulty=4)

# Initialize network node
node = GossipProtocol(
    host="localhost",
    port=8000,
    blockchain=blockchain
)

# Create wallet with password protection
wallet = Wallet()
exported_wallet = wallet.export_wallet(password="your-secure-password")
```

### Managing Transactions

```python
# Create transaction with custom data and fee
transaction = wallet.create_transaction(
    recipient="BC1q2w3e4r5t6y7u8i9o0p",
    amount=10.0,
    fee=0.001,
    data={"message": "Payment for services"}
)

# Add to blockchain
blockchain.add_transaction(transaction)

# Get transaction history
history = wallet.get_transaction_history(blockchain)
```

### Mining Operations

```python
# Start mining node
async def start_mining():
    while True:
        block = await blockchain.mine_block(wallet.address)
        if block:
            print(f"Block mined! Height: {block.height}, Hash: {block.hash}")

# Run mining node
import asyncio
asyncio.run(start_mining())
```

## Configuration

### Network Configuration (config/network_config.json)
```json
{
    "network": {
        "max_peers": 10,
        "peer_timeout": 300,
        "gossip_interval": 30,
        "sync_interval": 60
    },
    "blockchain": {
        "difficulty": 4,
        "target_block_time": 600,
        "max_block_size": 1000000,
        "min_transaction_fee": 0.0001
    },
    "wallet": {
        "key_version": 1,
        "address_prefix": "BC",
        "min_password_length": 8
    }
}
```

### Logging Configuration (config/logging_config.json)
```json
{
    "log_level": "INFO",
    "format": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
    "file_logging": {
        "enabled": true,
        "path": "logs/blockchain.log",
        "max_size": 10485760,
        "backup_count": 5
    }
}
```

## Development

### Running Tests
```bash
# Run all tests with coverage
pytest tests/ --cov=blockchain

# Run specific test category
pytest tests/test_wallet.py
pytest tests/test_blockchain.py
pytest tests/test_networking.py
```

### Code Style
The project follows PEP 8 guidelines. Format code using:
```bash
black blockchain/
isort blockchain/
```

### Type Checking
```bash
mypy blockchain/
```

## Documentation

Generate documentation using Sphinx:
```bash
cd docs
make html
```

View the documentation at `docs/_build/html/index.html`

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Run tests and type checking
4. Commit your changes (`git commit -m 'Add AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Bitcoin whitepaper for foundational blockchain concepts
- The Python cryptography community
- Contributors and maintainers of the cryptography, ecdsa, and aiohttp libraries
