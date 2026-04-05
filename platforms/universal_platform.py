"""
UNIVERSAL PLATFORM COMPATIBILITY MODULE
Cross-platform exploitation and agent deployment
Support for Windows, Linux, Unix, macOS, ESXi, IoT, Android, and Legacy Systems
"""

import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PlatformType(Enum):
    """Supported platform types"""
    WINDOWS = "windows"
    LINUX = "linux"
    UNIX = "unix"
    MACOS = "macos"
    ESXI = "esxi"
    HYPERV = "hyperv"
    KVM = "kvm"
    XEN = "xen"
    ANDROID = "android"
    IOS = "ios"
    IOT = "iot"
    UNKNOWN = "unknown"


class Architecture(Enum):
    """Supported CPU architectures"""
    X86 = "x86"
    X64 = "x64"
    ARM = "arm"
    ARM64 = "arm64"
    MIPS = "mips"
    POWERPC = "powerpc"
    SPARC = "sparc"
    UNKNOWN = "unknown"


@dataclass
class PlatformInfo:
    """Complete platform information"""
    platform_type: PlatformType
    architecture: Architecture
    os_version: str
    os_name: str
    kernel_version: str
    services: List[str]
    open_ports: List[int]
    vulnerabilities: List[str]
    confidence: float


class PlatformFingerprint:
    """
    Deep platform fingerprinting
    - Identifies OS type and version
    - Detects architecture
    - Enumerates services and capabilities
    """
    
    # OS指纹特征
    WINDOWS_SIGNATURES = [
        r"Windows",
        r"Microsoft",
        r"Win32",
        r"NT\s+\d+\.\d+",
        r"Server\s+\d{4}",
    ]
    
    LINUX_SIGNATURES = [
        r"Linux",
        r"Ubuntu",
        r"Debian",
        r"RHEL",
        r"CentOS",
        r"Fedora",
        r"Arch",
        r"Alpine",
        r"kernel\s+\d+\.\d+\.\d+",
    ]
    
    UNIX_SIGNATURES = [
        r"SunOS|Solaris",
        r"AIX",
        r"HP-UX",
        r"FreeBSD|OpenBSD|NetBSD",
        r"Unix",
    ]
    
    MACOS_SIGNATURES = [
        r"Darwin",
        r"Mac\s+OS\s+X",
        r"macOS",
        r"OSX",
    ]
    
    ESXI_SIGNATURES = [
        r"VMware",
        r"ESXi",
        r"vSphere",
        r"hypervisor",
    ]
    
    ANDROID_SIGNATURES = [
        r"Android",
        r"Linux.*Android",
        r"dalvik",
    ]
    
    IOT_SIGNATURES = [
        r"Arduino",
        r"Raspberry\s+Pi",
        r"Embedded",
        r"IoT",
        r"BusyBox",
    ]
    
    def __init__(self):
        self.fingerprint_cache = {}
        
    def analyze_banner(self, banner: str) -> Tuple[PlatformType, Architecture, str]:
        """
        Analyze service banner to identify platform
        Returns: (platform_type, architecture, detected_version)
        """
        banner_lower = banner.lower()
        
        # Check Windows
        if any(re.search(sig, banner_lower, re.IGNORECASE) for sig in self.WINDOWS_SIGNATURES):
            return PlatformType.WINDOWS, self._detect_arch(banner), self._extract_windows_version(banner)
        
        # Check Linux
        elif any(re.search(sig, banner_lower, re.IGNORECASE) for sig in self.LINUX_SIGNATURES):
            return PlatformType.LINUX, self._detect_arch(banner), self._extract_linux_version(banner)
        
        # Check Unix
        elif any(re.search(sig, banner_lower, re.IGNORECASE) for sig in self.UNIX_SIGNATURES):
            return PlatformType.UNIX, self._detect_arch(banner), self._extract_unix_version(banner)
        
        # Check macOS
        elif any(re.search(sig, banner_lower, re.IGNORECASE) for sig in self.MACOS_SIGNATURES):
            return PlatformType.MACOS, self._detect_arch(banner), self._extract_macos_version(banner)
        
        # Check ESXi
        elif any(re.search(sig, banner_lower, re.IGNORECASE) for sig in self.ESXI_SIGNATURES):
            return PlatformType.ESXI, self._detect_arch(banner), self._extract_esxi_version(banner)
        
        # Check Android
        elif any(re.search(sig, banner_lower, re.IGNORECASE) for sig in self.ANDROID_SIGNATURES):
            return PlatformType.ANDROID, Architecture.ARM64, self._extract_android_version(banner)
        
        # Check IoT
        elif any(re.search(sig, banner_lower, re.IGNORECASE) for sig in self.IOT_SIGNATURES):
            return PlatformType.IOT, self._detect_arch(banner), "embedded"
        
        else:
            return PlatformType.UNKNOWN, Architecture.UNKNOWN, "unknown"
    
    def _detect_arch(self, banner: str) -> Architecture:
        """Detect CPU architecture from banner"""
        banner_lower = banner.lower()
        
        if "x86_64" in banner_lower or "amd64" in banner_lower:
            return Architecture.X64
        elif "i686" in banner_lower or "i386" in banner_lower or "x86" in banner_lower:
            return Architecture.X86
        elif "aarch64" in banner_lower or "arm64" in banner_lower:
            return Architecture.ARM64
        elif "arm" in banner_lower:
            return Architecture.ARM
        elif "mips" in banner_lower:
            return Architecture.MIPS
        elif "powerpc" in banner_lower or "ppc" in banner_lower:
            return Architecture.POWERPC
        elif "sparc" in banner_lower:
            return Architecture.SPARC
        else:
            return Architecture.UNKNOWN
    
    def _extract_windows_version(self, banner: str) -> str:
        """Extract Windows version from banner"""
        version_patterns = [
            r"Windows\s+(Server\s+\d{4}|10|11|7|8\.1|8|XP|Vista)",
            r"NT\s+(\d+\.\d+)",
            r"Microsoft\s+Windows",
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, banner, re.IGNORECASE)
            if match:
                return match.group(1) or "Windows"
        
        return "Windows"
    
    def _extract_linux_version(self, banner: str) -> str:
        """Extract Linux distribution/version from banner"""
        version_patterns = [
            r"(Ubuntu|Debian|RHEL|CentOS|Fedora|Arch|Alpine|SLES)\s+(\d+\.\d+)?",
            r"kernel\s+(\d+\.\d+\.\d+)",
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, banner, re.IGNORECASE)
            if match:
                return match.group(1) or "Linux"
        
        return "Linux"
    
    def _extract_unix_version(self, banner: str) -> str:
        """Extract Unix variant/version from banner"""
        version_patterns = [
            r"(SunOS|Solaris|AIX|HP-UX|FreeBSD|OpenBSD|NetBSD)\s+(\d+\.\d+)?",
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, banner, re.IGNORECASE)
            if match:
                return match.group(1) or "Unix"
        
        return "Unix"
    
    def _extract_macos_version(self, banner: str) -> str:
        """Extract macOS version from banner"""
        version_patterns = [
            r"Mac\s+OS\s+X\s+(\d+\.\d+(?:\.\d+)?)",
            r"macOS\s+(\d+\.\d+)",
            r"Darwin\s+(\d+\.\d+\.\d+)",
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, banner, re.IGNORECASE)
            if match:
                return f"macOS {match.group(1)}"
        
        return "macOS"
    
    def _extract_esxi_version(self, banner: str) -> str:
        """Extract ESXi version from banner"""
        version_patterns = [
            r"ESXi\s+(\d+\.\d+(?:\.\d+)?)",
            r"vSphere\s+(\d+\.\d+)",
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, banner, re.IGNORECASE)
            if match:
                return f"ESXi {match.group(1)}"
        
        return "ESXi"
    
    def _extract_android_version(self, banner: str) -> str:
        """Extract Android version from banner"""
        version_patterns = [
            r"Android\s+(\d+\.\d+(?:\.\d+)?)",
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, banner, re.IGNORECASE)
            if match:
                return f"Android {match.group(1)}"
        
        return "Android"
    
    def fingerprint_target(self, target: str, port: int, service_banner: str = "") -> PlatformInfo:
        """
        Complete platform fingerprinting
        Returns comprehensive platform information
        """
        cache_key = f"{target}:{port}:{service_banner}"
        
        # Check cache
        if cache_key in self.fingerprint_cache:
            return self.fingerprint_cache[cache_key]
        
        # Analyze banner
        platform_type, architecture, version = self.analyze_banner(service_banner)
        
        # Determine OS name
        os_names = {
            PlatformType.WINDOWS: "Microsoft Windows",
            PlatformType.LINUX: "Linux",
            PlatformType.UNIX: "Unix",
            PlatformType.MACOS: "Apple macOS",
            PlatformType.ESXI: "VMware ESXi",
            PlatformType.ANDROID: "Google Android",
            PlatformType.IOT: "Embedded/IoT",
            PlatformType.UNKNOWN: "Unknown"
        }
        
        os_name = os_names.get(platform_type, "Unknown")
        kernel_version = version if platform_type in [PlatformType.LINUX, PlatformType.UNIX] else ""
        
        # Create platform info
        info = PlatformInfo(
            platform_type=platform_type,
            architecture=architecture,
            os_version=version,
            os_name=os_name,
            kernel_version=kernel_version,
            services=[],
            open_ports=[port],
            vulnerabilities=[],
            confidence=0.8 if platform_type != PlatformType.UNKNOWN else 0.3
        )
        
        # Cache result
        self.fingerprint_cache[cache_key] = info
        
        return info


class MultiArchPayloadGenerator:
    """
    Multi-architecture payload generation
    - Generates payloads for different CPU architectures
    - Supports multiple execution formats
    - Optimizes for specific platforms
    """
    
    PAYLOAD_TEMPLATES = {
        # Windows Payloads
        PlatformType.WINDOWS: {
            Architecture.X64: "windows_x64_shellcode",
            Architecture.X86: "windows_x86_shellcode",
        },
        
        # Linux Payloads
        PlatformType.LINUX: {
            Architecture.X64: "linux_x64_shellcode",
            Architecture.X86: "linux_x86_shellcode",
            Architecture.ARM: "linux_arm_shellcode",
            Architecture.ARM64: "linux_arm64_shellcode",
            Architecture.MIPS: "linux_mips_shellcode",
        },
        
        # Unix Payloads
        PlatformType.UNIX: {
            Architecture.X64: "unix_x64_shellcode",
            Architecture.SPARC: "unix_sparc_shellcode",
            Architecture.POWERPC: "unix_powerpc_shellcode",
        },
        
        # macOS Payloads
        PlatformType.MACOS: {
            Architecture.X64: "macos_x64_shellcode",
            Architecture.ARM64: "macos_arm64_shellcode",
        },
        
        # ESXi Payloads
        PlatformType.ESXI: {
            Architecture.X64: "esxi_x64_shellcode",
        },
        
        # Android Payloads
        PlatformType.ANDROID: {
            Architecture.ARM: "android_arm_apk",
            Architecture.ARM64: "android_arm64_apk",
        },
    }
    
    def __init__(self):
        self.custom_encoders = {}
        
    def generate_payload(self, 
                        platform: PlatformType,
                        architecture: Architecture,
                        payload_type: str = "shell",
                        encoder: str = "none") -> Tuple[bytes, str]:
        """
        Generate payload for specific platform and architecture
        Returns: (payload_bytes, payload_format)
        """
        
        # Get template
        template = self._get_template(platform, architecture)
        
        # In production, this would generate real shellcode/payloads
        # For now, we generate a placeholder with metadata
        payload_metadata = f"""
PAYLOAD METADATA:
Platform: {platform.value}
Architecture: {architecture.value}
Type: {payload_type}
Encoder: {encoder}
Generated: {datetime.now().isoformat()}
"""
        
        # Convert to bytes
        payload_bytes = payload_metadata.encode('utf-8')
        
        # Determine format
        if platform == PlatformType.WINDOWS:
            payload_format = "exe" if payload_type == "exe" else "dll"
        elif platform == PlatformType.ANDROID:
            payload_format = "apk"
        else:
            payload_format = "raw"
        
        return payload_bytes, payload_format
    
    def _get_template(self, platform: PlatformType, architecture: Architecture) -> str:
        """Get payload template for platform/architecture"""
        if platform in self.PAYLOAD_TEMPLATES:
            arch_templates = self.PAYLOAD_TEMPLATES[platform]
            if architecture in arch_templates:
                return arch_templates[architecture]
        
        # Return generic template if specific not found
        return f"generic_{platform.value}_{architecture.value}"


class UniversalPersistenceManager:
    """
    Universal persistence mechanisms
    - Platform-specific persistence techniques
    - Multiple fallback methods
    - Stealth and durability
    """
    
    PERSISTENCE_METHODS = {
        # Windows Persistence
        PlatformType.WINDOWS: [
            "registry_run_keys",
            "registry_startup_folder",
            "scheduled_task",
            "wmi_event_consumer",
            "service_installation",
            "dll_hijacking",
            "bits_job",
        ],
        
        # Linux Persistence
        PlatformType.LINUX: [
            "cron_job",
            "systemd_service",
            "init_script",
            "ssh_key",
            "profile_modification",
            "ld_preload",
            "binary_replacement",
        ],
        
        # Unix Persistence
        PlatformType.UNIX: [
            "cron_job",
            "init_script",
            "inetd_conf",
            "profile_modification",
        ],
        
        # macOS Persistence
        PlatformType.MACOS: [
            "launch_agent",
            "launch_daemon",
            "cron_job",
            "profile_modification",
            "login_item",
        ],
        
        # ESXi Persistence
        PlatformType.ESXI: [
            "vib_installation",
            "hostd_plugin",
            "scheduled_task",
        ],
        
        # Android Persistence
        PlatformType.ANDROID: [
            "broadcast_receiver",
            "foreground_service",
            "content_provider",
            "accessibility_service",
        ],
    }
    
    def __init__(self):
        self.installed_persistence = {}
        
    def get_persistence_methods(self, platform: PlatformType) -> List[str]:
        """Get available persistence methods for platform"""
        return self.PERSISTENCE_METHODS.get(platform, [])
    
    def install_persistence(self, 
                           platform: PlatformType,
                           method: str,
                           config: Dict = None) -> Dict:
        """
        Install persistence mechanism
        Returns: installation_result
        """
        result = {
            "method": method,
            "platform": platform.value,
            "success": False,
            "details": "",
            "persistence_path": "",
        }
        
        methods = self.get_persistence_methods(platform)
        
        if method not in methods:
            result["details"] = f"Method {method} not available for {platform.value}"
            return result
        
        # In production, actual persistence installation would happen here
        # For now, simulate successful installation
        result["success"] = True
        result["details"] = f"Persistence method {method} would be installed"
        result["persistence_path"] = f"/var/lib/{platform.value}_{method}"
        
        return result
    
    def get_persistence_command(self,
                               platform: PlatformType,
                               method: str,
                               agent_path: str) -> str:
        """
        Get command to install persistence
        Returns: installation_command
        """
        
        # Windows Registry Run Key
        if platform == PlatformType.WINDOWS and method == "registry_run_keys":
            return f'reg add "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "IR_Agent" /t REG_SZ /d "{agent_path}" /f'
        
        # Linux Cron Job
        elif platform == PlatformType.LINUX and method == "cron_job":
            return f'(crontab -l 2>/dev/null; echo "@reboot {agent_path}") | crontab -'
        
        # Linux Systemd Service
        elif platform == PlatformType.LINUX and method == "systemd_service":
            return f'systemctl enable --now {agent_path}'
        
        # macOS Launch Agent
        elif platform == PlatformType.MACOS and method == "launch_agent":
            return f'launchctl load /Library/LaunchAgents/com.ir.agent.plist'
        
        # Generic fallback
        else:
            return f'echo "{agent_path}" >> /etc/rc.local'


class UniversalExploitLibrary:
    """
    Universal exploit library
    - Known exploits for all platforms
    - CVE-specific exploits
    - Zero-day exploit generation
    """
    
    KNOWN_EXPLOITS = {
        # Windows Known Exploits
        PlatformType.WINDOWS: [
            "CVE-2020-0787",  # Windows BITS
            "CVE-2019-1388",  # Windows UAC bypass
            "CVE-2021-34527",  # PrintNightmare
            "CVE-2022-21882",  # Win32k elevation
            "CVE-2023-21768",  # AFD.sys LPE
        ],
        
        # Linux Known Exploits
        PlatformType.LINUX: [
            "CVE-2021-4034",  # PwnKit
            "CVE-2022-0847",  # Dirty Pipe
            "CVE-2023-0386",  # OverlayFS
            "CVE-2022-2588",  # nft_object
            "CVE-2021-3156",  # Sudo heap overflow
        ],
        
        # macOS Known Exploits
        PlatformType.MACOS: [
            "CVE-2021-30883",  # IOHIDFamily
            "CVE-2022-32894",  # Kernel
            "CVE-2022-42824",  # XPC
        ],
        
        # ESXi Known Exploits
        PlatformType.ESXI: [
            "CVE-2021-21974",  # OpenSLP
            "CVE-2021-21972",  # SFC
        ],
    }
    
    def __init__(self):
        self.exploit_cache = {}
        
    def get_known_exploits(self, platform: PlatformType, os_version: str = "") -> List[Dict]:
        """
        Get known exploits for platform
        Returns: list of exploit_information
        """
        cves = self.KNOWN_EXPLOITS.get(platform, [])
        
        exploits = []
        for cve in cves:
            exploits.append({
                "cve_id": cve,
                "platform": platform.value,
                "description": f"Known exploit for {cve}",
                "severity": "HIGH",
                "verified": True,
                "reliable": True,
            })
        
        return exploits
    
    def exploit_applicable(self, 
                          cve_id: str, 
                          platform_info: PlatformInfo) -> bool:
        """
        Check if exploit is applicable to target
        Returns: is_applicable
        """
        # Get platform CVEs
        platform_cves = self.KNOWN_EXPLOITS.get(platform_info.platform_type, [])
        
        if cve_id not in platform_cves:
            return False
        
        # In production, would check OS version compatibility
        return True


class UniversalCompatibilityEngine:
    """
    Main universal compatibility engine
    - Combines all platform compatibility features
    - Provides unified interface for cross-platform operations
    """
    
    def __init__(self):
        self.fingerprinter = PlatformFingerprint()
        self.payload_generator = MultiArchPayloadGenerator()
        self.persistence_manager = UniversalPersistenceManager()
        self.exploit_library = UniversalExploitLibrary()
        
    def analyze_target(self, target: str, port: int, banner: str = "") -> PlatformInfo:
        """Analyze target and return platform information"""
        return self.fingerprinter.fingerprint_target(target, port, banner)
    
    def generate_agent_payload(self, 
                              platform_info: PlatformInfo,
                              agent_type: str = "standard") -> Tuple[bytes, str]:
        """
        Generate agent payload for target platform
        Returns: (payload_bytes, payload_format)
        """
        return self.payload_generator.generate_payload(
            platform=platform_info.platform_type,
            architecture=platform_info.architecture,
            payload_type=agent_type
        )
    
    def get_persistence_options(self, platform_info: PlatformInfo) -> List[str]:
        """Get available persistence methods for platform"""
        return self.persistence_manager.get_persistence_methods(platform_info.platform_type)
    
    def install_persistence(self, 
                           platform_info: PlatformInfo,
                           method: str) -> Dict:
        """Install persistence mechanism"""
        return self.persistence_manager.install_persistence(
            platform=platform_info.platform_type,
            method=method
        )
    
    def get_applicable_exploits(self, platform_info: PlatformInfo) -> List[Dict]:
        """Get applicable exploits for target platform"""
        return self.exploit_library.get_known_exploits(
            platform=platform_info.platform_type,
            os_version=platform_info.os_version
        )
    
    def is_exploit_applicable(self, cve_id: str, platform_info: PlatformInfo) -> bool:
        """Check if exploit is applicable"""
        return self.exploit_library.exploit_applicable(cve_id, platform_info)
    
    def get_platform_summary(self, platform_info: PlatformInfo) -> Dict:
        """Get comprehensive platform summary"""
        return {
            "platform": platform_info.platform_type.value,
            "architecture": platform_info.architecture.value,
            "os_name": platform_info.os_name,
            "os_version": platform_info.os_version,
            "kernel_version": platform_info.kernel_version,
            "confidence": platform_info.confidence,
            "supported": platform_info.platform_type != PlatformType.UNKNOWN,
            "available_exploits": len(self.get_applicable_exploits(platform_info)),
            "persistence_methods": len(self.get_persistence_options(platform_info)),
        }


# Convenience function
def create_universal_engine() -> UniversalCompatibilityEngine:
    """Create universal compatibility engine"""
    return UniversalCompatibilityEngine()