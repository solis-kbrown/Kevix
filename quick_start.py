#!/usr/bin/env python3
"""
Quick Start Script for IR Platform
Sets up environment and demonstrates usage
"""

import os
import sys
import json
import subprocess
from pathlib import Path


def print_banner():
    print("="*80)
    print("AI-Driven IR & Ransomware Response Platform")
    print("Authorized Use Only - Incident Response & Cybersecurity")
    print("="*80)
    print()


def check_dependencies():
    """Check if required dependencies are installed"""
    print("[*] Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("[-] Python 3.8+ required")
        return False
    
    # Check nmap
    try:
        subprocess.run(["nmap", "--version"], capture_output=True, check=True)
        print("[+] nmap: OK")
    except:
        print("[-] nmap: NOT FOUND")
        print("    Install with: sudo apt-get install nmap")
        return False
    
    # Check Python packages
    required_packages = [
        "requests",
        "flask",
        "urllib3"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"[+] {package}: OK")
        except ImportError:
            print(f"[-] {package}: NOT FOUND")
            missing.append(package)
    
    if missing:
        print(f"\n[*] Installing missing packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print("[+] Packages installed")
    
    return True


def setup_directories():
    """Create required directories"""
    print("\n[*] Setting up directories...")
    
    directories = [
        "data/scans",
        "data/reports",
        "data/agents",
        "data/exploits",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"[+] Created: {directory}/")


def check_config():
    """Check configuration file"""
    print("\n[*] Checking configuration...")
    
    if not os.path.exists("config.json"):
        print("[-] config.json not found")
        return False
    
    with open("config.json", 'r') as f:
        config = json.load(f)
    
    # Check for API key
    api_key = config.get("ai", {}).get("openrouter_api_key", "")
    
    if api_key:
        print("[+] Configuration OK")
        print(f"[+] AI API key: {'*' * (len(api_key) - 4) + api_key[-4:]}")
    else:
        print("[!] AI API key not configured")
        print("    Edit config.json and add your OpenRouter API key")
        print("    Get API key from: https://openrouter.ai/keys")
    
    return True


def demo_scan_only():
    """Demonstrate scan-only mode"""
    print("\n" + "="*80)
    print("DEMO: Scan-Only Mode (No Exploitation)")
    print("="*80)
    
    print("\nExample command:")
    print("""
python3 iroperator.py \\
  --engagement "ENG-DEMO-001" \\
  --targets "127.0.0.1" \\
  --api-key "your-api-key-here"
    """)
    
    response = input("\nRun demo scan on localhost? (y/n): ")
    if response.lower() == 'y':
        print("\n[*] Running demo scan...")
        print("    Note: This will scan localhost only")
        
        # Import and run scanner
        from scanner.network_scanner import NetworkScanner
        
        scanner = NetworkScanner()
        result = scanner.scan_host("127.0.0.1", ports="22,80,443,8080")
        
        print(f"\n[+] Scan complete")
        print(f"    Target: {result.get('target')}")
        print(f"    Services found: {len(result.get('services', []))}")
        
        for service in result.get('services', []):
            print(f"      - Port {service['port']}/{service['protocol']}: {service.get('product', 'Unknown')}")
    
    print()


def demo_c2_server():
    """Demonstrate C2 server"""
    print("\n" + "="*80)
    print("DEMO: C2 Server")
    print("="*80)
    
    print("\nExample command:")
    print("python3 c2/server.py")
    
    print("\nFeatures:")
    print("  - Listen for agent connections")
    print("  - Issue commands to agents")
    print("  - Track agent status")
    print("  - Monitor operations")
    
    print()


def demo_full_workflow():
    """Demonstrate full workflow"""
    print("\n" + "="*80)
    print("DEMO: Full Workflow (Scan → AI → Exploit → Deploy)")
    print("="*80)
    
    print("\nExample command:")
    print("""
python3 iroperator.py \\
  --engagement "ENG-2024-001" \\
  --targets "192.168.1.0/24" \\
  --api-key "your-api-key-here" \\
  --auto-exploit \\
  --max-targets 5
    """)
    
    print("\nWorkflow:")
    print("  1. Scan IP ranges for services")
    print("  2. AI analyzes vulnerabilities")
    print("  3. Execute exploits automatically")
    print("  4. Deploy agents to compromised systems")
    print("  5. Generate comprehensive report")
    
    print("\n⚠️  WARNING: Auto-exploit mode will actually execute exploits!")
    print("    Only use on targets you have explicit authorization to test.")
    print()


def show_menu():
    """Show interactive menu"""
    print("\n" + "="*80)
    print("QUICK START MENU")
    print("="*80)
    print("1. Check all dependencies")
    print("2. Setup directories")
    print("3. Check configuration")
    print("4. Run scan demo")
    print("5. Show C2 server demo")
    print("6. Show full workflow demo")
    print("7. Exit")
    print("="*80)


def main():
    """Main entry point"""
    print_banner()
    
    while True:
        show_menu()
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            check_dependencies()
        elif choice == "2":
            setup_directories()
        elif choice == "3":
            check_config()
        elif choice == "4":
            demo_scan_only()
        elif choice == "5":
            demo_c2_server()
        elif choice == "6":
            demo_full_workflow()
        elif choice == "7":
            print("\nExiting...")
            break
        else:
            print("\nInvalid option")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()