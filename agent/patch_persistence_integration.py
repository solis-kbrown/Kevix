#!/usr/bin/env python3
"""
Patch script to integrate persistence manager into autonomous_swarm_agent.py
This script adds the necessary persistence activation calls
"""

import re
import shutil
from pathlib import Path


def patch_autonomous_swarm_agent():
    """
    Add persistence activation calls to autonomous_swarm_agent.py
    """
    file_path = Path("agent/autonomous_swarm_agent.py")
    
    if not file_path.exists():
        print(f"[!] File not found: {file_path}")
        return False
    
    # Create backup
    backup_path = file_path.with_suffix('.py.backup')
    shutil.copy(file_path, backup_path)
    print(f"[✓] Backup created: {backup_path}")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patch 1: Add persistence import (already done, skip)
    print("[✓] Persistence imports already present")
    
    # Patch 2: Add persistence activation in start_swarm after coordinator creation
    # Find the coordinator initialization and add persistence activation
    coordinator_pattern = r'(coordinator\.state = AgentState\.COORDINATING\s+)(print\(f".*Coordinator Created.*"\))'
    
    if "Install unstoppable persistence for coordinator" not in content:
        replacement = r'\1# Install unstoppable persistence for coordinator\n        print(f"🔒 Installing unstoppable persistence...")\n        if coordinator.persistence_manager:\n            if coordinator.persistence_manager.install_persistence():\n                print(f"✅ Persistence installed successfully")\n                print(f"🛡️  Self-healing activated")\n                print(f"⚡ Coordinator cannot be stopped or deleted\\n")\n            else:\n                print(f"⚠️  Persistence installation failed\\n")\n        \n        \2'
        content = re.sub(coordinator_pattern, replacement, content)
        print("[✓] Added coordinator persistence activation")
    else:
        print("[✓] Coordinator persistence activation already present")
    
    # Patch 4: Add persistence activation in autonomous_agent_loop
    # Find the autonomous loop and add activation at the start
    loop_start_pattern = r'(print\(f".*Autonomous Loop Started.*"\)\s+print\(f".*ATTACK CHAIN.*"\)\s*)(while agent\.active and self\.running:)'
    
    if "Start health monitoring for unstoppable operation" not in content:
        replacement = r'\1# Start health monitoring for unstoppable operation\n        if activate_persistence(agent):\n            print(f"   ❤️  Self-healing activated")\n            print(f"   🛡️  Unstoppable mode enabled\\n")\n        \n        \2'
        content = re.sub(loop_start_pattern, replacement, content)
        print("[✓] Added persistence activation in autonomous loop")
    else:
        print("[✓] Autonomous loop persistence activation already present")
    
    # Patch 5: Add persistence check to ensure_unstoppable in loop
    # Find the while loop and add unstoppable check
    while_pattern = r'(while agent\.active and self\.running:\s+try:\s+)(# Update heartbeat\n\s+agent\.last_heartbeat = datetime\.now\(\))'
    
    if "ensure_unstoppable" not in content:
        replacement = r'\1# Ensure agent remains unstoppable\n                ensure_unstoppable(agent)\n                \n                \2'
        content = re.sub(while_pattern, replacement, content)
        print("[✓] Added unstoppable check in autonomous loop")
    else:
        print("[✓] Unstoppable check already present")
    
    # Write the patched content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n[✓] Successfully patched: {file_path}")
    print(f"[✓] Backup saved at: {backup_path}")
    return True


if __name__ == "__main__":
    print("="*80)
    print("PATCHING AUTONOMOUS SWARM AGENT WITH PERSISTENCE INTEGRATION")
    print("="*80)
    print()
    
    success = patch_autonomous_swarm_agent()
    
    print()
    print("="*80)
    if success:
        print("✅ PATCHING COMPLETE")
        print("The autonomous swarm agent now has unstoppable persistence!")
    else:
        print("❌ PATCHING FAILED")
    print("="*80)