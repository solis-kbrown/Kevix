"""
Network Scanner Module
Scans IP ranges to discover services and identify potential vulnerabilities
"""

import subprocess
import json
import re
import socket
from typing import Dict, List, Optional
from datetime import datetime
import ipaddress

class NetworkScanner:
    """
    Network scanner for service discovery and vulnerability assessment
    - Scans IP ranges for open ports
    - Identifies services and versions
    - Detects potential vulnerabilities
    - Integrates with AI for intelligent analysis
    """
    
    def __init__(self, output_dir="data/scans"):
        self.output_dir = output_dir
        self.scan_results = []
    
    def parse_ip_ranges(self, targets: str) -> List[str]:
        """
        Parse IP ranges and CIDR notation into individual IPs
        
        Args:
            targets: String like "192.168.1.1-10", "10.0.0.0/24", or "host.example.com"
        
        Returns:
            List of IP addresses to scan
        """
        ip_list = []
        
        # Handle CIDR notation
        if '/' in targets:
            try:
                network = ipaddress.ip_network(targets, strict=False)
                ip_list = [str(ip) for ip in network.hosts()]
                # Limit to prevent excessive scans
                if len(ip_list) > 512:
                    print(f"Warning: Range has {len(ip_list)} hosts, limiting to first 512")
                    ip_list = ip_list[:512]
                return ip_list
            except:
                pass
        
        # Handle range notation (192.168.1.1-10)
        if '-' in targets:
            parts = targets.split('-')
            if len(parts) == 2:
                try:
                    base = parts[0].rsplit('.', 1)[0]
                    start = int(parts[0].rsplit('.', 1)[1])
                    end = int(parts[1])
                    ip_list = [f"{base}.{i}" for i in range(start, end + 1)]
                    return ip_list
                except:
                    pass
        
        # Handle single IP or hostname
        try:
            # Try to resolve hostname
            ip = socket.gethostbyname(targets)
            return [ip]
        except:
            # Return as-is if it's already an IP
            return [targets]
    
    def scan_host(self, ip: str, ports: str = None) -> Dict:
        """
        Scan a single host for open ports and services
        
        Args:
            ip: Target IP address
            ports: Port specification (default/topports/range)
        
        Returns:
            Dictionary with scan results
        """
        print(f"[+] Scanning host: {ip}")
        
        # Default ports: common services
        if not ports:
            ports = "21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,1723,3389,5900,8080,8443,8888"
        
        # Build nmap command
        nmap_cmd = [
            "nmap", "-sV", "-sC", "-O",
            "--version-intensity", "5",
            "--script", "vuln",
            "-p", ports,
            "-T3",
            ip
        ]
        
        try:
            result = subprocess.run(
                nmap_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            scan_data = {
                "target": ip,
                "timestamp": datetime.now().isoformat(),
                "command": " ".join(nmap_cmd),
                "status": "completed" if result.returncode == 0 else "error",
                "raw_output": result.stdout,
                "error": result.stderr,
                "services": self._parse_nmap_output(result.stdout),
                "vulnerabilities": self._extract_vulnerabilities(result.stdout)
            }
            
            return scan_data
            
        except subprocess.TimeoutExpired:
            return {
                "target": ip,
                "timestamp": datetime.now().isoformat(),
                "status": "timeout",
                "error": "Scan timed out"
            }
        except Exception as e:
            return {
                "target": ip,
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    def _parse_nmap_output(self, nmap_output: str) -> List[Dict]:
        """Parse nmap output to extract service information"""
        services = []
        lines = nmap_output.split('\n')
        
        for i, line in enumerate(lines):
            # Match port/service lines: PORT/STATE SERVICE VERSION
            match = re.match(r'(\d+)/(tcp|udp)\s+(\w+)\s+(.+)', line)
            if match:
                port = int(match.group(1))
                protocol = match.group(2)
                state = match.group(3)
                service_info = match.group(4)
                
                service = {
                    "port": port,
                    "protocol": protocol,
                    "state": state,
                    "service": service_info.split(' ')[0],
                    "version": self._extract_version(service_info)
                }
                
                # Extract product and version separately
                parts = service_info.split()
                if len(parts) > 1:
                    service["product"] = service_info
                else:
                    service["product"] = service_info
                
                services.append(service)
        
        return services
    
    def _extract_version(self, service_info: str) -> Optional[str]:
        """Extract version string from service information"""
        # Look for version patterns: product X.Y.Z
        version_match = re.search(r'(\d+\.\d+(\.\d+)?)', service_info)
        return version_match.group(1) if version_match else None
    
    def _extract_vulnerabilities(self, nmap_output: str) -> List[Dict]:
        """Extract vulnerability information from nmap vuln script output"""
        vulnerabilities = []
        
        # Look for vulnerability script results
        vuln_pattern = re.compile(r'\|?\s+(CVE-\d{4}-\d+)|VULNERABLE|Vulnerability', re.IGNORECASE)
        
        lines = nmap_output.split('\n')
        current_vuln = None
        
        for line in lines:
            # Check for CVE
            cve_match = re.search(r'(CVE-\d{4}-\d+)', line, re.IGNORECASE)
            if cve_match:
                if current_vuln:
                    vulnerabilities.append(current_vuln)
                current_vuln = {
                    "cve": cve_match.group(1),
                    "description": "",
                    "severity": "UNKNOWN"
                }
            
            # Check for severity
            if "CRITICAL" in line.upper():
                if current_vuln:
                    current_vuln["severity"] = "CRITICAL"
            elif "HIGH" in line.upper():
                if current_vuln:
                    current_vuln["severity"] = "HIGH"
            elif "MEDIUM" in line.upper() or "MODERATE" in line.upper():
                if current_vuln:
                    current_vuln["severity"] = "MEDIUM"
            
            # Extract VULNERABLE flags
            if "VULNERABLE" in line.upper() and current_vuln:
                current_vuln["verified"] = True
        
        if current_vuln:
            vulnerabilities.append(current_vuln)
        
        return vulnerabilities
    
    def quick_scan_port(self, ip: str, port: int, timeout: float = 2.0) -> Dict:
        """
        Quick scan of a single port on a single host
        
        Args:
            ip: Target IP
            port: Port to scan
            timeout: Connection timeout in seconds
        
        Returns:
            Port status information
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                # Port is open, try to grab banner
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    sock.connect((ip, port))
                    if port in [21, 22, 25, 80, 110, 143, 443, 993, 995]:
                        banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    else:
                        banner = None
                    sock.close()
                except:
                    banner = None
                
                return {
                    "ip": ip,
                    "port": port,
                    "status": "open",
                    "banner": banner
                }
            else:
                return {
                    "ip": ip,
                    "port": port,
                    "status": "closed"
                }
        except:
            return {
                "ip": ip,
                "port": port,
                "status": "error"
            }
    
    def scan_range(self, targets: str, ports: str = None) -> Dict:
        """
        Scan a range of IP addresses
        
        Args:
            targets: IP range or CIDR notation
            ports: Ports to scan
        
        Returns:
            Complete scan results
        """
        print(f"[*] Starting scan of: {targets}")
        
        ip_list = self.parse_ip_ranges(targets)
        print(f"[*] Targets to scan: {len(ip_list)} hosts")
        
        scan_id = f"SCAN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        results = {
            "scan_id": scan_id,
            "targets": targets,
            "ip_count": len(ip_list),
            "timestamp": datetime.now().isoformat(),
            "hosts": []
        }
        
        for ip in ip_list:
            host_result = self.scan_host(ip, ports)
            results["hosts"].append(host_result)
            
            # Count open ports
            open_ports = len(host_result.get("services", []))
            print(f"[*] {ip}: {open_ports} open ports found")
        
        # Statistics
        total_services = sum(len(h.get("services", [])) for h in results["hosts"])
        hosts_with_services = sum(1 for h in results["hosts"] if h.get("services"))
        
        results["statistics"] = {
            "total_hosts_scanned": len(ip_list),
            "hosts_services_found": hosts_with_services,
            "total_services_found": total_services,
            "vulnerabilities_found": sum(len(h.get("vulnerabilities", [])) for h in results["hosts"])
        }
        
        # Save results
        self._save_scan_results(results)
        
        print(f"[+] Scan complete: {scan_id}")
        print(f"    Services found: {total_services}")
        print(f"    Vulnerabilities found: {results['statistics']['vulnerabilities_found']}")
        
        return results
    
    def _save_scan_results(self, results: Dict):
        """Save scan results to file"""
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        
        output_file = f"{self.output_dir}/{results['scan_id']}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"[+] Scan results saved to: {output_file}")
    
    def get_exploitable_targets(self, scan_results: Dict) -> List[Dict]:
        """
        Extract potentially exploitable targets from scan results
        
        Returns list of targets with service information for AI analysis
        """
        exploitable = []
        
        for host in scan_results.get("hosts", []):
            for service in host.get("services", []):
                if service.get("state") == "open":
                    exploitable.append({
                        "host": host.get("target"),
                        "ip": host.get("target"),
                        "port": service.get("port"),
                        "protocol": service.get("protocol"),
                        "service": service.get("service"),
                        "version": service.get("version"),
                        "product": service.get("product"),
                        "banner": service.get("banner"),
                        "scan_id": scan_results.get("scan_id")
                    })
        
        return exploitable


class vulnerabilityScanner:
    """
    Enhanced vulnerability scanner using existing tools and AI analysis
    """
    
    def __init__(self):
        self.scanner = NetworkScanner()
    
    def comprehensive_scan(self, targets: str, use_ai: bool = False, 
                          ai_assistant=None) -> Dict:
        """
        Perform comprehensive scan with AI vulnerability analysis
        
        Args:
            targets: IP range to scan
            use_ai: Whether to use AI for vulnerability analysis
            ai_assistant: AIExploitAssistant instance
        
        Returns:
            Complete scan results with vulnerability analysis
        """
        # Basic scan
        results = self.scanner.scan_range(targets)
        
        if use_ai and ai_assistant:
            print("[*] Performing AI vulnerability analysis...")
            
            exploitable = self.scanner.get_exploitable_targets(results)
            
            for target in exploitable:
                print(f"[*] AI analyzing: {target['ip']}:{target['port']} ({target['service']})")
                
                # Query AI for vulnerability analysis
                analysis = ai_assistant.analyze_service(target)
                
                # Store AI analysis with target
                target["ai_analysis"] = analysis
                
                # Add vulnerabilities to results
                if "vulnerabilities" in analysis:
                    for vuln in analysis["vulnerabilities"]:
                        results.setdefault("ai_vulnerabilities", []).append({
                            "target": target["ip"],
                            "port": target["port"],
                            "service": target["service"],
                            **vuln
                        })
            
            results["ai_analysis_complete"] = True
        
        return results