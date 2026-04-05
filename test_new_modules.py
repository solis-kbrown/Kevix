"""
Test suite for new monitoring modules
"""

import sys
import time
sys.path.insert(0, '/workspace')

from agent.status_reporter import StatusReporter
from agent.persistence_monitor import PersistenceMonitor, PersistenceStatus
from agent.deployment_tracker import DeploymentTracker, DeploymentStatus

def test_status_reporter():
    """Test Status Reporter"""
    print("Test 1: Status Reporter...")
    
    reporter = StatusReporter(agent_id="test_agent_001")
    
    # Test system metrics
    metrics = reporter.get_system_metrics()
    assert 'hostname' in metrics
    assert 'ip_address' in metrics
    assert 'platform' in metrics
    assert 'cpu_percent' in metrics
    assert 'memory_percent' in metrics
    
    # Test status report generation
    agent_metrics = {
        'start_time': time.time() - 3600,
        'current_mission': 'scanning',
        'targets_scanned': 50,
        'targets_exploited': 10,
        'agents_deployed': 5
    }
    
    status = reporter.generate_status_report(agent_metrics)
    assert status.agent_id == "test_agent_001"
    assert status.status == "active"
    assert status.targets_scanned == 50
    
    print("✅ Test 1 PASSED: Status Reporter working")
    return True

def test_persistence_monitor():
    """Test Persistence Monitor"""
    print("\nTest 2: Persistence Monitor...")
    
    # Create mock persistence manager
    class MockPersistenceManager:
        def __init__(self):
            self.install_count = 0
        
        def install_persistence(self):
            self.install_count += 1
            return True
    
    persistence_manager = MockPersistenceManager()
    monitor = PersistenceMonitor(persistence_manager)
    
    # Test health check
    health = monitor.check_persistence_health()
    assert 'status' in health
    assert 'active_mechanisms' in health
    assert 'failed_mechanisms' in health
    assert 'health_score' in health
    
    # Test status summary
    summary = monitor.get_status_summary()
    assert 'status' in summary
    assert 'health_score' in summary
    
    print("✅ Test 2 PASSED: Persistence Monitor working")
    return True

def test_deployment_tracker():
    """Test Deployment Tracker"""
    print("\nTest 3: Deployment Tracker...")
    
    tracker = DeploymentTracker()
    
    # Test queue deployment
    deploy_id = tracker.queue_deployment("192.168.1.100", "Linux", priority=5)
    assert deploy_id.startswith("deploy_")
    
    # Test get queue status
    queue_status = tracker.get_queue_status()
    assert queue_status['pending_count'] >= 1
    
    # Test start deployment
    tracker.start_deployment(deploy_id)
    queue_status = tracker.get_queue_status()
    assert queue_status['in_progress_count'] >= 1
    
    # Test complete deployment (success)
    tracker.complete_deployment(deploy_id, success=True)
    metrics = tracker.get_deployment_metrics()
    assert metrics['successful_deployments'] >= 1
    assert metrics['success_rate'] >= 0
    
    # Test complete deployment (failure) - exceed retry limit
    deploy_id2 = tracker.queue_deployment("192.168.1.101", "Windows", priority=3)
    tracker.start_deployment(deploy_id2)
    # Fail it 4 times (exceeding max_retries of 3)
    for i in range(4):
        tracker.complete_deployment(deploy_id2, success=False, error_message="Connection timeout")
    metrics = tracker.get_deployment_metrics()
    assert metrics['failed_deployments'] >= 1
    
    # Test recent deployments
    recent = tracker.get_recent_deployments(5)
    assert len(recent) >= 2
    
    # Test failed deployments
    failed = tracker.get_failed_deployments()
    assert len(failed) >= 1
    
    print("✅ Test 3 PASSED: Deployment Tracker working")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 New Monitoring Modules - Integration Tests")
    print("=" * 60)
    
    tests = [
        test_status_reporter,
        test_persistence_monitor,
        test_deployment_tracker
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
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
        print("\n🎉 All tests passed! New modules are ready.\n")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())