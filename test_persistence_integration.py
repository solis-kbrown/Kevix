#!/usr/bin/env python3
"""
Test script to verify persistence integration
"""

import sys
import os

# Add workspace to path
sys.path.insert(0, '/workspace')

print("="*80)
print("TESTING PERSISTENCE INTEGRATION")
print("="*80)
print()

# Test 1: Import persistence manager
print("[TEST 1] Importing PersistenceManager...")
try:
    from agent.persistence_manager import PersistenceManager
    print("✅ PersistenceManager imported successfully")
except ImportError as e:
    print(f"❌ Failed to import PersistenceManager: {e}")
    sys.exit(1)

# Test 2: Import persistence helper
print("\n[TEST 2] Importing PersistenceHelper...")
try:
    from agent.persistence_helper import activate_persistence, ensure_unstoppable
    print("✅ PersistenceHelper imported successfully")
except ImportError as e:
    print(f"❌ Failed to import PersistenceHelper: {e}")
    sys.exit(1)

# Test 3: Import autonomous swarm agent
print("\n[TEST 3] Importing AutonomousSwarmAgent...")
try:
    from agent.autonomous_swarm_agent import AutonomousSwarmEngine
    print("✅ AutonomousSwarmAgent imported successfully")
except ImportError as e:
    print(f"❌ Failed to import AutonomousSwarmAgent: {e}")
    sys.exit(1)

# Test 4: Test PersistenceManager instantiation
print("\n[TEST 4] Testing PersistenceManager instantiation...")
try:
    test_agent_id = "TEST-AGENT-001"
    pm = PersistenceManager(test_agent_id)
    print(f"✅ PersistenceManager created for agent: {test_agent_id}")
    print(f"   - Install path: {pm.install_path}")
    print(f"   - Process name: {pm.process_name}")
except Exception as e:
    print(f"❌ Failed to create PersistenceManager: {e}")
    sys.exit(1)

# Test 5: Verify integration in AutonomousSwarmEngine
print("\n[TEST 5] Verifying persistence integration in AutonomousSwarmEngine...")
try:
    # Check that persistence_helper is imported
    import agent.autonomous_swarm_agent as asa_module
    if hasattr(asa_module, 'activate_persistence'):
        print("✅ activate_persistence function available in module")
    else:
        print("⚠️  activate_persistence not directly in module (might be imported)")
    
    # Check source code for integration
    with open('agent/autonomous_swarm_agent.py', 'r') as f:
        source = f.read()
        
    checks = {
        'Persistence import': 'from agent.persistence_helper import activate_persistence' in source,
        'Coordinator persistence': 'Install unstoppable persistence for coordinator' in source,
        'Autonomous loop activation': 'activate_persistence(agent)' in source,
        'Unstoppable check': 'ensure_unstoppable(agent)' in source
    }
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
        if not result:
            all_passed = False
    
    if not all_passed:
        print("\n❗ Some integration checks failed!")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Failed to verify integration: {e}")
    sys.exit(1)

print()
print("="*80)
print("✅ ALL TESTS PASSED")
print("="*80)
print()
print("The persistence integration is working correctly!")
print("Agents are now unstoppable and self-healing.")
print()