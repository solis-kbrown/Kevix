"""
Unified Configuration Manager
Centralized configuration with hot-reload support
"""

import json
import logging
import threading
import time
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class UnifiedConfig:
    """Unified configuration manager with hot-reload support"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._reload_thread = None
        self._running = False
        self._callbacks : List[Callable] = []
        self._last_modified = 0
        
        # Load initial configuration
        self.load_config()
        
        # Start monitoring for changes
        self.start_monitoring()
    
    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                
                self._last_modified = config_path.stat().st_mtime
                logger.info(f"Configuration loaded from {self.config_file}")
                self._notify_callbacks()
                return True
            else:
                # Create default configuration
                self.config = self._default_config()
                self.save_config()
                logger.info(f"Created default configuration at {self.config_file}")
                return True
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            self._last_modified = Path(self.config_file).stat().st_mtime
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def reload_config(self) -> bool:
        """Reload configuration from file"""
        logger.info("Reloading configuration...")
        return self.load_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        with self._lock:
            keys = key.split('.')
            value = self.config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
    
    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """Set configuration value"""
        with self._lock:
            keys = key.split('.')
            config = self.config
            
            # Navigate to parent
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set value
            config[keys[-1]] = value
            
            if save:
                return self.save_config()
            return True
    
    def register_callback(self, callback: Callable):
        """Register callback for configuration changes"""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self):
        """Notify all registered callbacks"""
        for callback in self._callbacks:
            try:
                callback(self.config)
            except Exception as e:
                logger.error(f"Error in config callback: {e}")
    
    def start_monitoring(self, interval: int = 5):
        """Start monitoring configuration file for changes"""
        if not self._running:
            self._running = True
            self._reload_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
            self._reload_thread.start()
            logger.info("Configuration monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring configuration file"""
        self._running = False
        if self._reload_thread:
            self._reload_thread.join(timeout=2)
            logger.info("Configuration monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """Monitor loop for configuration changes"""
        while self._running:
            try:
                config_path = Path(self.config_file)
                if config_path.exists():
                    current_modified = config_path.stat().st_mtime
                    if current_modified > self._last_modified:
                        logger.info("Configuration file modified, reloading...")
                        self.load_config()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error monitoring configuration: {e}")
                time.sleep(interval)
    
    def _default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        return {
            "system": {
                "agent_id": "swarm_agent",
                "c2_server": "localhost",
                "c2_port": 4444,
                "debug_mode": False,
                "log_level": "INFO"
            },
            "persistence": {
                "enabled": True,
                "auto_repair": True,
                "health_check_interval": 5,
                "max_retries": 3
            },
            "deployment": {
                "enabled": True,
                "auto_discovery": True,
                "max_concurrent": 10,
                "retry_attempts": 3
            },
            "monitoring": {
                "enabled": True,
                "health_check_interval": 5,
                "heartbeat_interval": 30,
                "collect_metrics": True
            },
            "communication": {
                "enabled": True,
                "encryption_key": None,
                "connection_timeout": 30,
                "max_retries": 5
            },
            "dashboard": {
                "enabled": True,
                "host": "0.0.0.0",
                "port": 8080,
                "refresh_interval": 2
            },
            "ai": {
                "enabled": True,
                "mode": "enhanced",
                "use_god_mode": False
            },
            "swarm": {
                "replication_factor": 20,
                "max_generations": 4,
                "continuous_operation": True,
                "autonomous": True
            }
        }
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        required_sections = ['system', 'persistence', 'deployment', 'monitoring', 'communication']
        for section in required_sections:
            if section not in self.config:
                logger.error(f"Missing required configuration section: {section}")
                return False
        return True
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            'config_file': self.config_file,
            'sections': list(self.config.keys()),
            'last_modified': datetime.fromtimestamp(self._last_modified).isoformat() if self._last_modified else None,
            'valid': self.validate_config(),
            'monitoring_active': self._running
        }