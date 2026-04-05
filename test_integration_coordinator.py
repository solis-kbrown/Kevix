"""
Test suite for Integration Coordinator
"""

import asyncio
import sys
sys.path.insert(0, '/workspace')

from agent.integration_coordinator import IntegrationCoordinator, create_integration_coordinator

async def test_coordinator_creation():
    """Test 1: Integration Coordinator creation"""
    print("Test 1: Integration Coordinator creation...")
    
    coordinator = IntegrationCoordinator(
        agent_id="test_coordinator_001",
        c2_server="localhost",
        c2_port=4444
    )
    
    assert coordinator is not None
    assert coordinator.agent_id == "test_coordinator_001"
    assert coordinator.c2_server == "localhost"
    
    print("✅ Test 1 PASSED: Coordinator created successfully")
    return True

async def test_initialization():
    """Test 2: Full initialization"""
    print("\nTest 2: Full initialization...")
    
    coordinator = await create_integration_coordinator(
        agent_id="test_init_001",
        c2_server="localhost",
        c2_port=4444,
        enable_dashboard=False
    )
    
    if coordinator:
        assert coordinator.state.value == "operational"
        assert coordinator.monitoring_system is not None
        assert coordinator.communication_system is not None
        
        await coordinator.shutdown()
        print("✅ Test 2 PASSED: Full initialization successful")
        return True
    else:
        print("❌ Test 2 FAILED: Initialization failed")
        return False

async def test_synchronization():
    """Test 3: Data synchronization"""
    print("\nTest 3: Data synchronization...")
    
    coordinator = await create_integration_coordinator(
        agent_id="test_sync_001",
        c2_server="localhost",
        c2_port=4444,
        enable_dashboard=False
    )
    
    if coordinator:
        await coordinator.start_synchronization()
        await asyncio.sleep(6)  # Wait for sync cycles
        
        metrics = coordinator.metrics
        assert metrics.uptime > 0
        
        await coordinator.stop_synchronization()
        await coordinator.shutdown()
        print("✅ Test 3 PASSED: Synchronization working")
        return True
    else:
        print("❌ Test 3 FAILED: Synchronization test failed")
        return False

async def test_alerts():
    """Test 4: Alert system"""
    print("\nTest 4: Alert system...")
    
    coordinator = await create_integration_coordinator(
        agent_id="test_alerts_001",
        c2_server="localhost",
        c2_port=4444,
        enable_dashboard=True
    )
    
    if coordinator:
        coordinator.add_custom_alert("info", "Test alert", "test_agent")
        coordinator.add_custom_alert("warning", "Test warning", "test_agent")
        
        assert coordinator.dashboard is not None
        assert len(coordinator.dashboard.alerts) >= 2
        
        await coordinator.shutdown()
        print("✅ Test 4 PASSED: Alert system working")
        return True
    else:
        print("❌ Test 4 FAILED: Alert system test failed")
        return False

async def test_integration_status():
    """Test 5: Integration status"""
    print("\nTest 5: Integration status...")
    
    coordinator = await create_integration_coordinator(
        agent_id="test_status_001",
        c2_server="localhost",
        c2_port=4444,
        enable_dashboard=False
    )
    
    if coordinator:
        status = coordinator.get_integration_status()
        
        assert 'state' in status
        assert 'uptime' in status
        assert 'messages_processed' in status
        assert 'monitoring_system_initialized' in status
        assert status['monitoring_system_initialized'] == True
        
        await coordinator.shutdown()
        print("✅ Test 5 PASSED: Integration status working")
        return True
    else:
        print("❌ Test 5 FAILED: Status test failed")
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Integration Coordinator - Integration Tests")
    print("=" * 60)
    
    tests = [
        test_coordinator_creation,
        test_initialization,
        test_synchronization,
        test_alerts,
        test_integration_status
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ FAILED: {test.__name__}")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{len(tests)} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All tests passed! Integration Coordinator is ready.\n")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review.\n")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())