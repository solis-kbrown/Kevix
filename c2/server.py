"""
C2 Server
Central Command and Control server for IR operations
"""

import socket
import threading
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - C2 - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/c2_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class C2Server:
    """
    Command and Control Server
    - Receives agent check-ins
    - Issues commands to agents
    - Tracks agent status
    - Manages IR operations
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8443, 
                 db_path: str = "data/c2_database.db"):
        self.host = host
        self.port = port
        self.db_path = db_path
        self.agents = {}  # agent_id -> agent_info
        self.commands = {}  # agent_id -> list of commands
        self.active = False
        self._init_database()
    
    def _init_database(self):
        """Initialize C2 database"""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Agents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    hostname TEXT,
                    platform TEXT,
                    arch TEXT,
                    username TEXT,
                    ip_address TEXT,
                    first_checkin TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_checkin TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # Commands table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    command TEXT,
                    status TEXT DEFAULT 'pending',
                    output TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            
            # Operations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_name TEXT,
                    operation_type TEXT,
                    description TEXT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    agents_involved TEXT
                )
            """)
            
            conn.commit()
        
        logger.info(f"C2 Database initialized: {self.db_path}")
    
    def start(self):
        """Start the C2 server"""
        self.active = True
        
        # Start listener thread
        listener_thread = threading.Thread(target=self._listener)
        listener_thread.daemon = True
        listener_thread.start()
        
        logger.info(f"C2 Server started on {self.host}:{self.port}")
    
    def stop(self):
        """Stop the C2 server"""
        self.active = False
        logger.info("C2 Server stopped")
    
    def _listener(self):
        """Listen for incoming agent connections"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen(100)
            
            logger.info(f"Listening for agent connections on port {self.port}")
            
            while self.active:
                try:
                    client, addr = server.accept()
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except Exception as e:
                    logger.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client: socket.socket, addr):
        """Handle client connection"""
        try:
            data = client.recv(8192).decode()
            if not data:
                return
            
            request = json.loads(data)
            
            response = self._process_request(request, addr)
            
            if response:
                client.sendall(json.dumps(response).encode())
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from {addr}: {data[:100]}")
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            client.close()
    
    def _process_request(self, request: Dict, addr) -> Dict:
        """Process incoming request from agent"""
        msg_type = request.get("type")
        agent_id = request.get("agent_id")
        
        if msg_type == "register":
            return self._handle_register(request, addr)
        elif msg_type == "get_commands":
            return self._handle_get_commands(agent_id)
        elif msg_type == "result":
            return self._handle_result(request)
        elif msg_type == "heartbeat":
            return self._handle_heartbeat(agent_id)
        else:
            return {"error": "Unknown message type"}
    
    def _handle_register(self, request: Dict, addr):
        """Handle agent registration"""
        agent_id = request.get("agent_id")
        hostname = request.get("hostname")
        platform = request.get("platform")
        arch = request.get("arch")
        username = request.get("username")
        ip_address = addr[0]
        
        # Store agent info
        self.agents[agent_id] = {
            "hostname": hostname,
            "platform": platform,
            "arch": arch,
            "username": username,
            "ip_address": ip_address,
            "last_checkin": datetime.now().isoformat(),
            "first_checkin": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agents 
                (agent_id, hostname, platform, arch, username, ip_address, last_checkin)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (agent_id, hostname, platform, arch, username, ip_address))
            conn.commit()
        
        logger.info(f"Agent registered: {agent_id} ({hostname} @ {ip_address})")
        
        return {
            "status": "registered",
            "message": "Agent successfully registered",
            "c2_time": datetime.now().isoformat()
        }
    
    def _handle_get_commands(self, agent_id: str) -> Dict:
        """Handle request for commands"""
        if agent_id not in self.agents:
            return {"error": "Agent not registered"}
        
        # Update last checkin
        self.agents[agent_id]["last_checkin"] = datetime.now().isoformat()
        
        # Get pending commands
        commands = self.commands.get(agent_id, [])
        
        # Clear commands after sending
        self.commands[agent_id] = []
        
        if commands:
            logger.info(f"Sending {len(commands)} commands to {agent_id}")
        
        return {"commands": commands}
    
    def _handle_result(self, request: Dict):
        """Handle command execution result"""
        agent_id = request.get("agent_id")
        command_id = request.get("command_id")
        output = request.get("output")
        
        logger.info(f"Received result from {agent_id} for command {command_id}")
        
        # Update command status in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE commands 
                SET status = 'completed', output = ?, completed = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (json.dumps(output), command_id))
            conn.commit()
        
        return {"status": "result_received"}
    
    def _handle_heartbeat(self, agent_id: str) -> Dict:
        """Handle agent heartbeat"""
        if agent_id in self.agents:
            self.agents[agent_id]["last_checkin"] = datetime.now().isoformat()
        
        return {"status": "alive"}
    
    def issue_command(self, agent_id: str, command: str) -> int:
        """
        Issue command to specific agent
        
        Returns:
            Command ID
        """
        if agent_id not in self.commands:
            self.commands[agent_id] = []
        
        command_id = int(datetime.now().timestamp())
        self.commands[agent_id].append({
            "id": command_id,
            "command": command,
            "timestamp": datetime.now().isoformat()
        })
        
        # Log to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO commands (agent_id, command, status, timestamp)
                VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
            """, (agent_id, command))
            conn.commit()
        
        logger.info(f"Command '{command}' issued to {agent_id} (ID: {command_id})")
        
        return command_id
    
    def broadcast_command(self, command: str, platform: str = None) -> List[int]:
        """
        Broadcast command to all agents or specific platform
        
        Returns:
            List of command IDs
        """
        command_ids = []
        
        for agent_id, agent_info in self.agents.items():
            if platform is None or agent_info.get("platform") == platform:
                cmd_id = self.issue_command(agent_id, command)
                command_ids.append(cmd_id)
        
        return command_ids
    
    def get_agent_status(self, agent_id: str = None) -> Dict:
        """
        Get status of one or all agents
        
        Args:
            agent_id: Specific agent ID, or None for all
        
        Returns:
            Agent status information
        """
        if agent_id:
            return self.agents.get(agent_id, {"error": "Agent not found"})
        else:
            return self.agents
    
    def get_active_agents_count(self) -> int:
        """Get count of active agents"""
        active_threshold = datetime.now().timestamp() - 600  # 10 minutes
        
        return sum(
            1 for agent in self.agents.values()
            if datetime.fromisoformat(agent["last_checkin"]).timestamp() > active_threshold
        )
    
    def create_operation(self, operation_name: str, operation_type: str,
                        description: str = "") -> int:
        """Create a new IR operation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO operations
                (operation_name, operation_type, description, status)
                VALUES (?, ?, ?, 'active')
            """, (operation_name, operation_type, description))
            conn.commit()
            
            return cursor.lastrowid
    
    def get_operation_status(self, operation_id: int) -> Dict:
        """Get operation status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM operations WHERE id = ?
            """, (operation_id,))
            
            result = cursor.fetchone()
            return dict(result) if result else {"error": "Operation not found"}


class C2Console:
    """
    Console interface for interacting with C2 server
    """
    
    def __init__(self, c2_server: C2Server):
        self.c2 = c2_server
    
    def show_menu(self):
        """Display console menu"""
        print("\n" + "="*50)
        print("C2 CONSOLE - IR Command & Control")
        print("="*50)
        print("1. List all agents")
        print("2. Show agent details")
        print("3. Issue command to agent")
        print("4. Broadcast command to all")
        print("5. Show active operations")
        print("6. Create new operation")
        print("7. Scan for agents")
        print("8. Exit")
        print("="*50)
    
    def list_agents(self):
        """List all registered agents"""
        agents = self.c2.get_agent_status()
        
        if not agents:
            print("\nNo agents registered")
            return
        
        print(f"\nRegistered Agents: {len(agents)}")
        print("-"*80)
        print(f"{'Agent ID':<25} {'Hostname':<20} {'Platform':<10} {'Last Checkin':<20}")
        print("-"*80)
        
        for agent_id, agent_info in agents.items():
            last_checkin = agent_info.get("last_checkin", "never")
            print(f"{agent_id:<25} {agent_info.get('hostname', 'Unknown'):<20} "
                  f"{agent_info.get('platform', 'Unknown'):<10} {last_checkin:<19}")
    
    def show_agent_details(self, agent_id: str):
        """Show detailed information about an agent"""
        agent = self.c2.get_agent_status(agent_id)
        
        if "error" in agent:
            print(f"\nError: {agent['error']}")
            return
        
        print(f"\nAgent Details:")
        print(f"  ID: {agent_id}")
        print(f"  Hostname: {agent.get('hostname', 'Unknown')}")
        print(f"  Platform: {agent.get('platform', 'Unknown')}")
        print(f"  Architecture: {agent.get('arch', 'Unknown')}")
        print(f"  Username: {agent.get('username', 'Unknown')}")
        print(f"  IP Address: {agent.get('ip_address', 'Unknown')}")
        print(f"  Status: {agent.get('status', 'Unknown')}")
        print(f"  First Checkin: {agent.get('first_checkin', 'Unknown')}")
        print(f"  Last Checkin: {agent.get('last_checkin', 'Unknown')}")
    
    def issue_command_interactive(self):
        """Interactive command issuing"""
        agent_id = input("Enter Agent ID: ").strip()
        command = input("Enter Command: ").strip()
        
        if agent_id and command:
            command_id = self.c2.issue_command(agent_id, command)
            print(f"\nCommand issued (ID: {command_id})")
        else:
            print("\nInvalid input")
    
    def broadcast_command_interactive(self):
        """Interactive command broadcast"""
        command = input("Enter Command: ").strip()
        platform = input("Target Platform (leave blank for all): ").strip() or None
        
        if command:
            command_ids = self.c2.broadcast_command(command, platform)
            print(f"\nCommand broadcasted to {len(command_ids)} agents")
        else:
            print("\nInvalid input")


def main():
    """Main entry point"""
    c2 = C2Server(host="0.0.0.0", port=8443)
    c2.start()
    
    console = C2Console(c2)
    
    try:
        while True:
            console.show_menu()
            choice = input("\nSelect option: ").strip()
            
            if choice == "1":
                console.list_agents()
            elif choice == "2":
                agent_id = input("Enter Agent ID: ").strip()
                console.show_agent_details(agent_id)
            elif choice == "3":
                console.issue_command_interactive()
            elif choice == "4":
                console.broadcast_command_interactive()
            elif choice == "5":
                print("\nOperations feature - coming soon")
            elif choice == "6":
                print("\nOperations feature - coming soon")
            elif choice == "7":
                print(f"\nActive agents: {c2.get_active_agents_count()}")
            elif choice == "8":
                print("\nExiting...")
                c2.stop()
                break
            else:
                print("\nInvalid option")
    
    except KeyboardInterrupt:
        print("\nShutting down...")
        c2.stop()


if __name__ == "__main__":
    main()