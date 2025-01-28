import asyncio
import json
import time
import uuid
from typing import Dict, Set, Optional, List, Tuple
from dataclasses import dataclass, asdict
import socket
from ..utils.logger import get_logger
from ..blockchain.blockchain import Blockchain
from ..blockchain.block import Block, Transaction

logger = get_logger(__name__)

@dataclass
class Peer:
    host: str
    port: int
    last_seen: float
    node_id: str
    version: str
    height: int = 0
    
    def to_dict(self):
        return asdict(self)

class GossipProtocol:
    VERSION = "1.0.0"
    PEER_TIMEOUT = 300  # 5 minutes
    MAX_PEERS = 10
    GOSSIP_INTERVAL = 30
    CLEANUP_INTERVAL = 60
    
    def __init__(self, host: str, port: int, blockchain: Blockchain):
        self.host = host
        self.port = port
        self.node_id = str(uuid.uuid4())
        self.blockchain = blockchain
        self.peers: Dict[str, Peer] = {}  # node_id -> Peer
        self.known_messages: Set[str] = set()
        self.server: Optional[asyncio.DatagramTransport] = None
        self.running = False
        
    async def start(self):
        """Start the gossip protocol."""
        self.running = True
        loop = asyncio.get_event_loop()
        
        # Start UDP server
        self.server, _ = await loop.create_datagram_endpoint(
            lambda: GossipProtocolHandler(self),
            local_addr=(self.host, self.port)
        )
        
        # Start background tasks
        asyncio.create_task(self._periodic_gossip())
        asyncio.create_task(self._cleanup_peers())
        logger.info(f"Gossip protocol started on {self.host}:{self.port}")

    async def stop(self):
        """Stop the gossip protocol."""
        self.running = False
        if self.server:
            self.server.close()
        logger.info("Gossip protocol stopped")

    async def _periodic_gossip(self):
        """Periodically send gossip messages to peers."""
        while self.running:
            if self.peers:
                await self._broadcast_status()
            await asyncio.sleep(self.GOSSIP_INTERVAL)

    async def _cleanup_peers(self):
        """Remove inactive peers."""
        while self.running:
            current_time = time.time()
            inactive_peers = [
                node_id for node_id, peer in self.peers.items()
                if current_time - peer.last_seen > self.PEER_TIMEOUT
            ]
            for node_id in inactive_peers:
                del self.peers[node_id]
                logger.info(f"Removed inactive peer: {node_id}")
            await asyncio.sleep(self.CLEANUP_INTERVAL)

    async def handle_message(self, data: bytes, addr: Tuple[str, int]):
        """Handle incoming messages."""
        try:
            message = json.loads(data.decode())
            message_type = message.get('type')
            
            if message_type == 'HELLO':
                await self._handle_hello(message, addr)
            elif message_type == 'STATUS':
                await self._handle_status(message, addr)
            elif message_type == 'GET_BLOCKS':
                await self._handle_get_blocks(message, addr)
            elif message_type == 'BLOCKS':
                await self._handle_blocks(message, addr)
            elif message_type == 'NEW_TRANSACTION':
                await self._handle_new_transaction(message, addr)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    async def _handle_hello(self, message: dict, addr: Tuple[str, int]):
        """Handle peer introduction."""
        node_id = message.get('node_id')
        version = message.get('version')
        
        if node_id not in self.peers and len(self.peers) < self.MAX_PEERS:
            self.peers[node_id] = Peer(
                host=addr[0],
                port=addr[1],
                last_seen=time.time(),
                node_id=node_id,
                version=version
            )
            logger.info(f"New peer connected: {node_id}")
            
            # Send status response
            await self._send_status(addr)

    async def _handle_status(self, message: dict, addr: Tuple[str, int]):
        """Handle blockchain status updates."""
        node_id = message.get('node_id')
        height = message.get('height', 0)
        
        if node_id in self.peers:
            peer = self.peers[node_id]
            peer.last_seen = time.time()
            peer.height = height
            
            # If peer has longer chain, request blocks
            if height > len(self.blockchain.chain):
                await self._request_blocks(addr, len(self.blockchain.chain))

    async def _handle_get_blocks(self, message: dict, addr: Tuple[str, int]):
        """Handle block requests."""
        start = message.get('start', 0)
        end = message.get('end', len(self.blockchain.chain))
        
        blocks = [
            block.to_dict() for block in self.blockchain.chain[start:end]
        ]
        
        response = {
            'type': 'BLOCKS',
            'blocks': blocks,
            'node_id': self.node_id
        }
        
        await self._send_message(response, addr)

    async def _handle_blocks(self, message: dict, addr: Tuple[str, int]):
        """Handle received blocks."""
        blocks_data = message.get('blocks', [])
        
        try:
            blocks = [Block.from_dict(block_data) for block_data in blocks_data]
            
            # Validate and add blocks
            for block in blocks:
                if not self.blockchain.add_block(block):
                    logger.warning(f"Failed to add block: {block.hash}")
                    
        except Exception as e:
            logger.error(f"Error processing blocks: {str(e)}")

    async def _handle_new_transaction(self, message: dict, addr: Tuple[str, int]):
        """Handle new transaction broadcasts."""
        try:
            tx_data = message.get('transaction')
            transaction = Transaction.from_dict(tx_data)
            
            if self.blockchain.add_transaction(transaction):
                # Forward to other peers
                await self._broadcast_transaction(transaction)
                
        except Exception as e:
            logger.error(f"Error processing transaction: {str(e)}")

    async def _send_message(self, message: dict, addr: Tuple[str, int]):
        """Send a message to a specific peer."""
        try:
            data = json.dumps(message).encode()
            self.server.sendto(data, addr)
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")

    async def _broadcast_message(self, message: dict):
        """Broadcast a message to all peers."""
        for peer in self.peers.values():
            await self._send_message(message, (peer.host, peer.port))

    async def _broadcast_status(self):
        """Broadcast current blockchain status."""
        message = {
            'type': 'STATUS',
            'node_id': self.node_id,
            'version': self.VERSION,
            'height': len(self.blockchain.chain)
        }
        await self._broadcast_message(message)

    async def _broadcast_transaction(self, transaction: Transaction):
        """Broadcast a new transaction."""
        message = {
            'type': 'NEW_TRANSACTION',
            'transaction': transaction.to_dict(),
            'node_id': self.node_id
        }
        await self._broadcast_message(message)

    async def _request_blocks(self, addr: Tuple[str, int], start: int):
        """Request blocks from a peer."""
        message = {
            'type': 'GET_BLOCKS',
            'start': start,
            'node_id': self.node_id
        }
        await self._send_message(message, addr)

class GossipProtocolHandler:
    def __init__(self, protocol: GossipProtocol):
        self.protocol = protocol

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        asyncio.create_task(self.protocol.handle_message(data, addr))