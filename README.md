# Enhanced Blockchain Implementation

A feature-rich blockchain implementation in Python with proof-of-work consensus, wallet management, and peer-to-peer networking.

## Features

- **Advanced Blockchain Core**
  - Proof of Work consensus mechanism
  - Dynamic difficulty adjustment
  - Merkle tree for efficient transaction verification
  - Block validation and chain integrity checks
  - Support for orphaned blocks
  - Transaction pool management

- **Wallet System**
  - ECDSA-based cryptographic key pairs
  - Transaction signing and verification
  - Balance tracking
  - Transaction history
  - Key import/export functionality

- **Networking**
  - Peer-to-peer communication using UDP
  - Gossip protocol for network discovery
  - Efficient block and transaction propagation
  - Automatic peer management
  - Network status monitoring

- **Security Features**
  - Cryptographic signatures
  - Hash verification
  - Nonce validation
  - Transaction validation
  - Secure wallet generation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/enhanced-blockchain.git
cd enhanced-blockchain
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting a Node

```python
from src.blockchain import Blockchain
from src.networking import GossipProtocol

# Initialize blockchain
blockchain = Blockchain(difficulty=4)

# Start node
node = GossipProtocol("localhost", 8000, blockchain)
node.start()
```

### Creating a Wallet

```python
from src.blockchain import Wallet

# Create new wallet
wallet = Wallet()

# Get wallet address
address = wallet.address

# Export keys
private_key, public_key = wallet.export_keys()
```

### Making Transactions

```python
# Create and sign a transaction
transaction = wallet.create_transaction(
    recipient="recipient_address",
    amount=10.0,
    blockchain=blockchain
)

# Add to blockchain
blockchain.add_transaction(transaction)
```

### Mining Blocks

```python
# Mine a new block
success = blockchain.mine_block(miner_address=wallet.address)
if success:
    print("Block mined successfully!")
```

## Configuration

The blockchain can be configured through the `config/network_config.json` file:

```json
{
    "difficulty": 4,
    "target_block_time": 600,
    "max_peers": 10,
    "peer_timeout": 300,
    "gossip_interval": 30
}
```

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- The Bitcoin whitepaper for inspiration
- The Python community for excellent cryptographic libraries
