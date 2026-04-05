"""
Test suite for Dashboard UI integration
"""

import asyncio
import json
import sys
import os
sys.path.insert(0, '/workspace')

from agent.dashboard_ui import DashboardUI, DashboardConfig, AgentStatus, SystemMetrics, create_mock_agents

def test_dashboard_creation():
    """Test 1: Dashboard instance creation"""
    print("Test 1: Dashboard instance creation...")
    
    config = DashboardConfig()
    dashboard = DashboardUI(config)
    
    assert dashboard is not None
    assert dashboard.config.host == "0.0.0.0"
    assert dashboard.config.port == 8080
    assert dashboard.system_metrics.total_agents == 0
    
    print("✅ Test 1 PASSED: Dashboard instance created successfully")
    return True

def test_agent_status_update():
    """Test 2: Agent status updates"""
    print("\nTest 2: Agent status updates...")
    
    config = DashboardConfig()
    dashboard = DashboardUI(config)
    
    # Create test agent
    agent = AgentStatus(
        agent_id="test_agent_001",
        hostname="test-host",
        ip_address="192.168.1.100",
        platform="Linux",
        status="active",
        cpu_usage=45.5,
        memory_usage=32.2,
        disk_usage=55.0,
        network_latency=10.5,
        last_heartbeat="2024-01-01 12:00:00",
        uptime=3600.0,
        mission="Scanning",
        targets_scanned=50,
        exploits_used=10,
        deployments_completed=5
    )
    
    dashboard.update_agent_status(agent)
    
    assert len(dashboard.agents) == 1
    assert dashboard.system_metrics.total_agents == 1
    assert dashboard.system_metrics.active_agents == 1
    
    print("✅ Test 2 PASSED: Agent status updates work correctly")
    return True

def test_system_metrics_calculation():
    """Test 3: System metrics calculation"""
    print("\nTest 3: System metrics calculation...")
    
    config = DashboardConfig()
    dashboard = DashboardUI(config)
    
    # Add multiple agents
    agents = create_mock_agents(5)
    for agent in agents:
        dashboard.update_agent_status(agent)
    
    # Check metrics
    assert dashboard.system_metrics.total_agents == 5
    assert dashboard.system_metrics.active_agents >= 3  # At least 3 active
    assert len(dashboard.metrics_history) > 0
    assert len(dashboard.agents) == 5
    
    print("✅ Test 3 PASSED: System metrics calculated correctly")
    return True

def test_alerts_system():
    """Test 4: Alerts system"""
    print("\nTest 4: Alerts system...")
    
    config = DashboardConfig()
    dashboard = DashboardUI(config)
    
    # Add alerts
    dashboard.add_alert("warning", "High CPU usage detected", "agent_001")
    dashboard.add_alert("info", "New agent joined", "agent_002")
    dashboard.add_alert("error", "Connection failed", None)
    
    assert len(dashboard.alerts) == 3
    assert dashboard.alerts[0]['level'] == 'error'
    assert dashboard.alerts[0]['agent_id'] is None
    assert dashboard.alerts[2]['level'] == 'warning'
    
    print("✅ Test 4 PASSED: Alerts system works correctly")
    return True

def test_html_generation():
    """Test 5: HTML dashboard generation"""
    print("\nTest 5: HTML dashboard generation...")
    
    config = DashboardConfig()
    dashboard = DashboardUI(config)
    
    # Add mock data
    agents = create_mock_agents(3)
    for agent in agents:
        dashboard.update_agent_status(agent)
    
    dashboard.add_alert("info", "Test alert", "agent_001")
    
    # Generate HTML
    html = dashboard.generate_dashboard_html()
    
    assert '<!DOCTYPE html>' in html
    assert 'ServerRoot.net' in html
    assert 'Autonomous Swarm Defense' in html
    assert 'agent_' in html
    assert 'chart.js' in html
    
    print("✅ Test 5 PASSED: HTML dashboard generated successfully")
    return True

def test_api_data():
    """Test 6: API data generation"""
    print("\nTest 6: API data generation...")
    
    config = DashboardConfig()
    dashboard = DashboardUI(config)
    
    # Add mock data
    agents = create_mock_agents(2)
    for agent in agents:
        dashboard.update_agent_status(agent)
    
    # Get API data
    api_data = dashboard.get_api_data()
    
    assert 'system_metrics' in api_data
    assert 'agents' in api_data
    assert 'alerts' in api_data
    assert 'metrics_history' in api_data
    assert 'last_updated' in api_data
    assert len(api_data['agents']) == 2
    
    print("✅ Test 6 PASSED: API data generated correctly")
    return True

def test_metrics_history():
    """Test 7: Metrics history tracking"""
    print("\nTest 7: Metrics history tracking...")
    
    config = DashboardConfig(max_history_points=10)
    dashboard = DashboardUI(config)
    
    # Add agents to generate history
    for i in range(3):
        agents = create_mock_agents(1)
        for agent in agents:
            dashboard.update_agent_status(agent)
        asyncio.sleep(0.1)  # Small delay
    
    # Check history
    assert len(dashboard.metrics_history) >= 3
    assert dashboard.metrics_history[0]['timestamp'] is not None
    assert 'active_agents' in dashboard.metrics_history[0]
    
    print("✅ Test 7 PASSED: Metrics history tracked correctly")
    return True

def test_mock_agents():
    """Test 8: Mock agent generation"""
    print("\nTest 8: Mock agent generation...")
    
    mock_agents = create_mock_agents(5)
    
    assert len(mock_agents) == 5
    assert all(isinstance(agent, AgentStatus) for agent in mock_agents)
    
    # Check first agent
    assert mock_agents[0].agent_id.startswith('agent_')
    assert mock_agents[0].hostname is not None
    assert mock_agents[0].ip_address is not None
    assert mock_agents[0].status in ['active', 'offline', 'degraded', 'compromised']
    
    print("✅ Test 8 PASSED: Mock agents generated correctly")
    return True

def test_empty_dashboard():
    """Test 9: Empty dashboard state"""
    print("\nTest 9: Empty dashboard state...")
    
    config = DashboardConfig()
    dashboard = DashboardUI(config)
    
    # Generate HTML with no data
    html = dashboard.generate_dashboard_html()
    
    assert 'No agents currently reporting' in html
    assert 'No alerts' in html
    assert dashboard.system_metrics.total_agents == 0
    
    print("✅ Test 9 PASSED: Empty dashboard handled correctly")
    return True

def test_concurrent_updates():
    """Test 10: Concurrent agent updates"""
    print("\nTest 10: Concurrent agent updates...")
    
    config = DashboardConfig()
    dashboard = DashboardUI(config)
    
    # Simulate concurrent updates
    async def update_agents():
        tasks = []
        for i in range(10):
            agent = AgentStatus(
                agent_id=f"concurrent_agent_{i}",
                hostname=f"host-{i}",
                ip_address=f"10.0.0.{i}",
                platform="Linux",
                status="active",
                cpu_usage=30.0,
                memory_usage=40.0,
                disk_usage=50.0,
                network_latency=5.0,
                last_heartbeat="2024-01-01 12:00:00",
                uptime=3600.0,
                mission="Testing",
                targets_scanned=10,
                exploits_used=5,
                deployments_completed=3
            )
            dashboard.update_agent_status(agent)
        
        assert dashboard.system_metrics.total_agents == 10
    
    asyncio.run(update_agents())
    
    print("✅ Test 10 PASSED: Concurrent updates handled correctly")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 ServerRoot.net Dashboard UI - Integration Tests")
    print("=" * 60)
    
    tests = [
        test_dashboard_creation,
        test_agent_status_update,
        test_system_metrics_calculation,
        test_alerts_system,
        test_html_generation,
        test_api_data,
        test_metrics_history,
        test_mock_agents,
        test_empty_dashboard,
        test_concurrent_updates
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
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{len(tests)} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All tests passed! Dashboard UI is ready.\n")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())