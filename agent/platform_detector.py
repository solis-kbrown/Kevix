#!/usr/bin/env python3
"""
Platform Detector Module
Multi-platform detection system for Windows, Linux, macOS, Routers, VPNs, and Virtualization Platforms

Government Contract Requirement: Accurate platform detection for autonomous exploitation
"""

import asyncio
import socket
import ssl
import struct
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import aiohttp
import xml.etree.ElementTree as ET


class PlatformType(Enum):
    """Platform types supported"""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    ROUTER = "router"
    FIREWALL = "firewall"
    VPN = "vpn"
    VIRTUALIZATION = "virtualization"
    UNKNOWN = "unknown"


class Vendor(Enum):
    """Vendor types"""
    CISCO = "cisco"
    JUNIPER = "juniper"
    FORTINET = "fortinet"
    PALO_ALTO = "palo_alto"
    MIKROTIK = "mikrotik"
    UBIQUITI = "ubiquiti"
    VMWARE = "vmware"
    MICROSOFT = "microsoft"
    PROXMOX = "proxmox"
    UNKNOWN = "unknown"


@dataclass
class ServiceInfo:
    """Service information"""
    port: int
    service: str
    version: str
    banner: str
    vulnerabilities: List[str] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class PlatformDetectionResult:
    """Platform detection result"""
    target_ip: str
    platform_type: PlatformType
    vendor: Vendor = Vendor.UNKNOWN
    os_version: str = ""
    os_details: Dict = field(default_factory=dict)
    services: List[ServiceInfo] = field(default_factory=list)
    confidence: float = 0.0
    detection_method: str = ""
    timestamp: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "target_ip": self.target_ip,
            "platform_type": self.platform_type.value,
            "vendor": self.vendor.value,
            "os_version": self.os_version,
            "os_details": self.os_details,
            "services": [
                {
                    "port": s.port,
                    "service": s.service,
                    "version": s.version,
                    "banner": s.banner,
                    "vulnerabilities": s.vulnerabilities,
                    "confidence": s.confidence
                }
                for s in self.services
            ],
            "confidence": self.confidence,
            "detection_method": self.detection_method,
            "timestamp": self.timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }


class PlatformDetector:
    """
    Multi-platform detection system
    
    Capabilities:
    - Active OS fingerprinting
    - Service version detection
    - Banner grabbing
    - Protocol analysis
    - Platform-specific detection
    """
    
    # Common ports for quick scanning
    COMMON_PORTS = {
        # Windows
        135: "MSRPC",
        139: "NetBIOS",
        445: "SMB",
        3389: "RDP",
        5985: "WinRM HTTP",
        5986: "WinRM HTTPS",
        
        # Linux/Unix
        22: "SSH",
        21: "FTP",
        23: "Telnet",
        80: "HTTP",
        111: "RPC",
        443: "HTTPS",
        2049: "NFS",
        
        # macOS
        548: "AFP",
        631: "IPP",
        5353: "mDNS/Bonjour",
        
        # Router/Firewall/VPN
        23: "Telnet",
        443: "HTTPS",
        8443: "HTTPS",
        8080: "HTTP-Alt",
        1194: "OpenVPN",
        500: "IKE",
        4500: "IPsec NAT-T",
        
        # Virtualization
        22: "SSH",
        80: "HTTP",
        443: "HTTPS",
        902: "VMware Auth",
        903: "VMware Auth",
        8006: "Proxmox",
        3128: "Proxmox",
    }
    
    # Platform-specific signatures
    WINDOWS_SIGNATURES = [
        ("SMBv", 445, "SMB"),
        ("Microsoft", 135, "MSRPC"),
        ("Microsoft", 3389, "RDP"),
        ("Microsoft", 5985, "WinRM"),
        ("Microsoft Windows", 443, "HTTP"),
    ]
    
    LINUX_SIGNATURES = [
        ("OpenSSH", 22, "SSH"),
        ("Apache", 80, "HTTP"),
        ("nginx", 80, "HTTP"),
        ("Ubuntu", 22, "SSH"),
        ("Debian", 22, "SSH"),
        ("CentOS", 22, "SSH"),
        ("RHEL", 22, "SSH"),
    ]
    
    # Router/Firewall vendors
    ROUTER_SIGNATURES = {
        Vendor.CISCO: [
            ("Cisco", 23, "Telnet"),
            ("Cisco", 443, "HTTPS"),
            ("Cisco", 80, "HTTP"),
        ],
        Vendor.JUNIPER: [
            ("Juniper", 23, "Telnet"),
            ("Juniper", 443, "HTTPS"),
        ],
        Vendor.FORTINET: [
            ("Fortinet", 443, "HTTPS"),
            ("FortiGate", 443, "HTTPS"),
        ],
        Vendor.PALO_ALTO: [
            ("Palo Alto", 443, "HTTPS"),
            ("PAN-OS", 443, "HTTPS"),
        ],
        Vendor.MIKROTIK: [
            ("MikroTik", 80, "HTTP"),
            ("RouterOS", 80, "HTTP"),
        ],
        Vendor.UBIQUITI: [
            ("Ubiquiti", 443, "HTTPS"),
            ("UniFi", 443, "HTTPS"),
        ],
    }
    
    # VPN signatures
    VPN_SIGNATURES = {
        "OpenVPN": ("OpenVPN", 1194),
        "IPsec": ("IKE", 500),
        "WireGuard": ("wireguard", 51820),
    }
    
    # Virtualization platform signatures
    VIRTUALIZATION_SIGNATURES = {
        Vendor.VMWARE: [
            ("VMware", 80, "HTTP"),
            ("VMware", 443, "HTTPS"),
            ("VMware", 902, "VMware Auth"),
            ("vCenter", 443, "HTTPS"),
            ("ESXi", 443, "HTTPS"),
        ],
        Vendor.MICROSOFT: [
            ("Microsoft Hyper-V", 5985, "WinRM"),
            ("Windows Server", 3389, "RDP"),
        ],
        Vendor.PROXMOX: [
            ("Proxmox", 8006, "HTTPS"),
            ("Proxmox", 3128, "Proxmox"),
        ],
    }
    
    def __init__(self, timeout: float = 3.0, max_retries: int = 2):
        """
        Initialize platform detector
        
        Args:
            timeout: Connection timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def detect_platform(self, target_ip: str) -> PlatformDetectionResult:
        """
        Detect platform of target
        
        Args:
            target_ip: Target IP address
            
        Returns:
            PlatformDetectionResult with platform information
        """
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        result = PlatformDetectionResult(
            target_ip=target_ip,
            platform_type=PlatformType.UNKNOWN,
            confidence=0.0,
            timestamp=timestamp
        )
        
        # Step 1: Check if host is alive
        if not await self._check_host_alive(target_ip):
            result.detection_method = "host_down"
            return result
        
        result.detection_method = "active"
        
        # Step 2: Scan common ports
        open_ports = await self._scan_common_ports(target_ip)
        
        if not open_ports:
            result.detection_method = "no_open_ports"
            return result
        
        # Step 3: Detect services on open ports
        services = await self._detect_services(target_ip, open_ports)
        result.services = services
        
        # Step 4: Determine platform based on services
        platform_type, vendor, confidence = self._identify_platform(services)
        result.platform_type = platform_type
        result.vendor = vendor
        result.confidence = confidence
        
        # Step 5: Get OS version if possible
        result.os_version = await self._get_os_version(target_ip, platform_type, services)
        
        # Step 6: Get OS details
        result.os_details = await self._get_os_details(target_ip, platform_type, services)
        
        return result
    
    async def _check_host_alive(self, target_ip: str) -> bool:
        """
        Check if host is alive using TCP connection
        
        Args:
            target_ip: Target IP address
            
        Returns:
            True if host is alive, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((target_ip, 445))  # Try SMB port
            sock.close()
            return result == 0
        except Exception:
            return False
    
    async def _scan_common_ports(self, target_ip: str) -> List[int]:
        """
        Scan common ports to find open ones
        
        Args:
            target_ip: Target IP address
            
        Returns:
            List of open ports
        """
        open_ports = []
        
        # Scan ports concurrently
        tasks = []
        for port in self.COMMON_PORTS.keys():
            tasks.append(self._check_port(target_ip, port))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for port, is_open in zip(self.COMMON_PORTS.keys(), results):
            if is_open is True:
                open_ports.append(port)
        
        return open_ports
    
    async def _check_port(self, target_ip: str, port: int) -> bool:
        """
        Check if a specific port is open
        
        Args:
            target_ip: Target IP address
            port: Port number
            
        Returns:
            True if port is open
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((target_ip, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    async def _detect_services(self, target_ip: str, ports: List[int]) -> List[ServiceInfo]:
        """
        Detect services on open ports
        
        Args:
            target_ip: Target IP address
            ports: List of ports to scan
            
        Returns:
            List of ServiceInfo objects
        """
        services = []
        
        # Detect services concurrently
        tasks = []
        for port in ports:
            tasks.append(self._detect_service(target_ip, port))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for port, service_info in zip(ports, results):
            if service_info is not None:
                services.append(service_info)
        
        return services
    
    async def _detect_service(self, target_ip: str, port: int) -> Optional[ServiceInfo]:
        """
        Detect service on a specific port
        
        Args:
            target_ip: Target IP address
            port: Port number
            
        Returns:
            ServiceInfo object or None
        """
        try:
            # Get known service name
            service_name = self.COMMON_PORTS.get(port, "unknown")
            
            # Grab banner
            banner = await self._grab_banner(target_ip, port)
            
            # Analyze banner
            version = self._extract_version(banner, service_name)
            
            return ServiceInfo(
                port=port,
                service=service_name,
                version=version,
                banner=banner,
                confidence=0.8
            )
        except Exception:
            return None
    
    async def _grab_banner(self, target_ip: str, port: int) -> str:
        """
        Grab service banner from port
        
        Args:
            target_ip: Target IP address
            port: Port number
            
        Returns:
            Banner string
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((target_ip, port))
            
            # Try different protocols based on port
            if port in [80, 8080, 8000]:
                banner = self._grab_http_banner(sock)
            elif port in [443, 8443, 8444, 1194, 8006]:
                banner = await self._grab_https_banner(target_ip, port)
            elif port == 22:
                banner = self._grab_ssh_banner(sock)
            elif port in [21, 23, 25]:
                banner = self._grab_text_banner(sock)
            elif port in [135, 445]:
                banner = self._grab_smb_banner(target_ip)
            else:
                banner = self._grab_text_banner(sock)
            
            sock.close()
            return banner or ""
        except Exception:
            return ""
    
    def _grab_http_banner(self, sock: socket.socket) -> str:
        """Grab HTTP banner"""
        try:
            sock.send(b"HEAD / HTTP/1.1\r\nHost: localhost\r\n\r\n")
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            return banner
        except Exception:
            return ""
    
    async def _grab_https_banner(self, target_ip: str, port: int) -> str:
        """Grab HTTPS banner"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(target_ip, port, ssl=context),
                timeout=self.timeout
            )
            
            writer.write(b"HEAD / HTTP/1.1\r\nHost: localhost\r\n\r\n")
            await writer.drain()
            
            data = await reader.read(1024)
            banner = data.decode('utf-8', errors='ignore')
            
            writer.close()
            await writer.wait_closed()
            
            return banner
        except Exception:
            return ""
    
    def _grab_ssh_banner(self, sock: socket.socket) -> str:
        """Grab SSH banner"""
        try:
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            return banner
        except Exception:
            return ""
    
    def _grab_text_banner(self, sock: socket.socket) -> str:
        """Grab text-based banner"""
        try:
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            return banner
        except Exception:
            return ""
    
    def _grab_smb_banner(self, target_ip: str) -> str:
        """Grab SMB banner"""
        try:
            # Simplified SMB banner grab
            return f"SMB connection to {target_ip}"
        except Exception:
            return ""
    
    def _extract_version(self, banner: str, service: str) -> str:
        """
        Extract version from banner
        
        Args:
            banner: Service banner
            service: Service name
            
        Returns:
            Version string
        """
        if not banner:
            return "unknown"
        
        # Common version extraction patterns
        patterns = {
            "SSH": r"OpenSSH[_\s](\d+\.\d+)",
            "SMB": r"SMBv(\d+\.\d+)",
            "Apache": r"Apache/(\d+\.\d+\.\d+)",
            "nginx": r"nginx/(\d+\.\d+\.\d+)",
            "HTTP": r"Server:\s*([^\r\n]+)",
        }
        
        pattern = patterns.get(service, r"(\d+\.\d+\.\d+)")
        match = re.search(pattern, banner, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        # Extract Server header for HTTP
        if service in ["HTTP", "HTTPS"]:
            server_match = re.search(r"Server:\s*([^\r\n]+)", banner, re.IGNORECASE)
            if server_match:
                return server_match.group(1)
        
        # Extract first significant line
        lines = banner.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('HTTP'):
                return line.strip()[:100]
        
        return "unknown"
    
    def _identify_platform(self, services: List[ServiceInfo]) -> Tuple[PlatformType, Vendor, float]:
        """
        Identify platform based on services
        
        Args:
            services: List of services
            
        Returns:
            Tuple of (PlatformType, Vendor, confidence)
        """
        if not services:
            return PlatformType.UNKNOWN, Vendor.UNKNOWN, 0.0
        
        # Score each platform type
        scores = {
            PlatformType.WINDOWS: 0,
            PlatformType.LINUX: 0,
            PlatformType.MACOS: 0,
            PlatformType.ROUTER: 0,
            PlatformType.VPN: 0,
            PlatformType.VIRTUALIZATION: 0,
        }
        
        vendor_scores = {vendor: 0 for vendor in Vendor}
        
        # Check each service
        for service in services:
            banner_lower = service.banner.lower()
            
            # Windows signatures
            if any(sig in banner_lower for sig in ["windows", "microsoft", "smbv", "msrpc"]):
                scores[PlatformType.WINDOWS] += 2
            
            # Linux signatures
            if any(sig in banner_lower for sig in ["openssh", "ubuntu", "debian", "centos", "rhel"]):
                scores[PlatformType.LINUX] += 2
            
            # macOS signatures
            if any(sig in banner_lower for sig in ["afp", "bonjour", "macos", "darwin"]):
                scores[PlatformType.MACOS] += 2
            
            # VPN signatures
            if "openvpn" in banner_lower or service.port == 1194:
                scores[PlatformType.VPN] += 3
            
            if service.port in [500, 4500]:
                scores[PlatformType.VPN] += 2
            
            # Virtualization signatures
            if any(sig in banner_lower for sig in ["vmware", "esxi", "vcenter", "proxmox", "hyper-v"]):
                scores[PlatformType.VIRTUALIZATION] += 3
            
            # Router/Firewall detection
            for vendor, signatures in self.ROUTER_SIGNATURES.items():
                for sig, _, _ in signatures:
                    if sig.lower() in banner_lower:
                        scores[PlatformType.ROUTER] += 2
                        vendor_scores[vendor] += 2
        
        # Check specific ports as indicators
        for service in services:
            if service.port == 445:  # SMB
                scores[PlatformType.WINDOWS] += 3
            elif service.port == 22 and "openssh" in service.banner.lower():
                scores[PlatformType.LINUX] += 2
            elif service.port == 548:  # AFP
                scores[PlatformType.MACOS] += 3
            elif service.port in [8006, 3128]:  # Proxmox
                scores[PlatformType.VIRTUALIZATION] += 3
                vendor_scores[Vendor.PROXMOX] += 3
        
        # Determine winner
        max_score = max(scores.values())
        
        if max_score == 0:
            return PlatformType.UNKNOWN, Vendor.UNKNOWN, 0.0
        
        # Get all platforms with max score
        winners = [p for p, s in scores.items() if s == max_score]
        
        if len(winners) == 1:
            platform = winners[0]
            confidence = min(max_score / 5.0, 1.0)
            
            # Determine vendor
            max_vendor_score = max(vendor_scores.values())
            if max_vendor_score > 0:
                vendor = max(vendor_scores, key=vendor_scores.get)
            else:
                vendor = Vendor.UNKNOWN
            
            return platform, vendor, confidence
        
        # Tie - prefer more common platforms
        if PlatformType.WINDOWS in winners:
            return PlatformType.WINDOWS, Vendor.UNKNOWN, 0.5
        elif PlatformType.LINUX in winners:
            return PlatformType.LINUX, Vendor.UNKNOWN, 0.5
        else:
            return PlatformType.UNKNOWN, Vendor.UNKNOWN, 0.3
    
    async def _get_os_version(self, target_ip: str, platform: PlatformType, 
                            services: List[ServiceInfo]) -> str:
        """
        Get OS version if possible
        
        Args:
            target_ip: Target IP address
            platform: Platform type
            services: List of services
            
        Returns:
            OS version string
        """
        if platform == PlatformType.WINDOWS:
            # Try to get Windows version from SMB or RDP
            for service in services:
                if service.port == 445 and "SMBv" in service.version:
                    return f"Windows ({service.version})"
                elif service.port == 3389 and "Microsoft" in service.banner:
                    return "Windows Server/RDP"
        
        elif platform == PlatformType.LINUX:
            # Try to get Linux distro from SSH
            for service in services:
                if service.port == 22:
                    banner = service.banner.lower()
                    if "ubuntu" in banner:
                        return "Ubuntu"
                    elif "debian" in banner:
                        return "Debian"
                    elif "centos" in banner:
                        return "CentOS"
                    elif "rhel" in banner:
                        return "RHEL"
                    elif "openssh" in banner:
                        return "Linux (OpenSSH)"
        
        elif platform == PlatformType.VIRTUALIZATION:
            # Get virtualization platform version
            for service in services:
                if "vmware" in service.banner.lower():
                    if "esxi" in service.banner.lower():
                        return "VMware ESXi"
                    elif "vcenter" in service.banner.lower():
                        return "VMware vCenter"
                elif "proxmox" in service.banner.lower():
                    return "Proxmox VE"
        
        return platform.value.title()
    
    async def _get_os_details(self, target_ip: str, platform: PlatformType,
                            services: List[ServiceInfo]) -> Dict:
        """
        Get detailed OS information
        
        Args:
            target_ip: Target IP address
            platform: Platform type
            services: List of services
            
        Returns:
            Dictionary with OS details
        """
        details = {
            "architecture": "unknown",
            "domain_joined": False,
            "firewall_enabled": "unknown",
            "open_ports_count": len(services),
        }
        
        # Infer architecture from services
        for service in services:
            if "x64" in service.banner.lower() or "amd64" in service.banner.lower():
                details["architecture"] = "x64"
            elif "x86" in service.banner.lower() or "i386" in service.banner.lower():
                details["architecture"] = "x86"
        
        # Check for domain indicators (Windows)
        if platform == PlatformType.WINDOWS:
            details["domain_like"] = any(
                "domain" in service.banner.lower() or "corp" in service.banner.lower()
                for service in services
            )
        
        return details


# Convenience function for quick detection
async def quick_detect(target_ip: str) -> Dict:
    """
    Quick platform detection function
    
    Args:
        target_ip: Target IP address
        
    Returns:
        Dictionary with platform information
    """
    async with PlatformDetector() as detector:
        result = await detector.detect_platform(target_ip)
        return result.to_dict()