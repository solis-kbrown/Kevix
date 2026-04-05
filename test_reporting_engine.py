"""
Test Suite for Reporting Engine

Tests for:
- Execution logging
- Timeline visualization
- Attack chain reconstruction
- Success/failure analytics
- Performance benchmarking
- Export functions
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add agent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

from reporting_engine import (
    ReportingEngine,
    LogLevel,
    EventType,
    LogEntry,
    TimelineEvent,
    AttackChainReconstruction,
    TimeRange,
    PerformanceMetrics
)


class TestExecutionLogging(unittest.TestCase):
    """Test execution logging functionality"""
    
    def setUp(self):
        """Setup test engine"""
        self.engine = ReportingEngine()
    
    def test_log_entry_creation(self):
        """Test creating log entries"""
        self.engine.log(
            level=LogLevel.INFO,
            event_type=EventType.ATTACK_INITIATED,
            agent_id="agent_001",
            message="Test message",
            target_id="target_001",
            chain_id="chain_001",
            duration_ms=1000
        )
        
        self.assertEqual(len(self.engine.logs), 1)
        log = self.engine.logs[0]
        self.assertEqual(log.level, LogLevel.INFO)
        self.assertEqual(log.agent_id, "agent_001")
        self.assertEqual(log.message, "Test message")
    
    def test_log_filtering_by_level(self):
        """Test filtering logs by level"""
        self.engine.log(LogLevel.INFO, EventType.TARGET_DISCOVERY, "agent_001", "Info message")
        self.engine.log(LogLevel.ERROR, EventType.ERROR_OCCURRED, "agent_001", "Error message")
        self.engine.log(LogLevel.WARNING, EventType.STAGE_FAILED, "agent_001", "Warning message")
        
        error_logs = self.engine.get_logs(level=LogLevel.ERROR)
        self.assertEqual(len(error_logs), 1)
        self.assertEqual(error_logs[0].level, LogLevel.ERROR)
    
    def test_log_filtering_by_event_type(self):
        """Test filtering logs by event type"""
        self.engine.log(LogLevel.INFO, EventType.TARGET_DISCOVERY, "agent_001", "Target found")
        self.engine.log(LogLevel.INFO, EventType.ATTACK_INITIATED, "agent_001", "Attack started")
        self.engine.log(LogLevel.INFO, EventType.TARGET_DISCOVERY, "agent_001", "Another target")
        
        discovery_logs = self.engine.get_logs(event_type=EventType.TARGET_DISCOVERY)
        self.assertEqual(len(discovery_logs), 2)
    
    def test_log_filtering_by_agent(self):
        """Test filtering logs by agent ID"""
        self.engine.log(LogLevel.INFO, EventType.TARGET_DISCOVERY, "agent_001", "Agent 1 message")
        self.engine.log(LogLevel.INFO, EventType.TARGET_DISCOVERY, "agent_002", "Agent 2 message")
        
        agent1_logs = self.engine.get_logs(agent_id="agent_001")
        self.assertEqual(len(agent1_logs), 1)
        self.assertEqual(agent1_logs[0].agent_id, "agent_001")
    
    def test_log_filtering_by_target(self):
        """Test filtering logs by target ID"""
        self.engine.log(LogLevel.INFO, EventType.ATTACK_INITIATED, "agent_001", "Attack 1", "target_001")
        self.engine.log(LogLevel.INFO, EventType.ATTACK_INITIATED, "agent_001", "Attack 2", "target_002")
        
        target1_logs = self.engine.get_logs(target_id="target_001")
        self.assertEqual(len(target1_logs), 1)
        self.assertEqual(target1_logs[0].target_id, "target_001")
    
    def test_log_filtering_by_time_range(self):
        """Test filtering logs by time range"""
        now = datetime.now()
        past_time = now - timedelta(hours=2)
        future_time = now + timedelta(hours=2)
        
        self.engine.log(LogLevel.INFO, EventType.TARGET_DISCOVERY, "agent_001", "Old message")
        
        # Simulate log in the past by modifying timestamp directly
        self.engine.logs[0].timestamp = past_time
        
        self.engine.log(LogLevel.INFO, EventType.TARGET_DISCOVERY, "agent_001", "New message")
        
        time_range = TimeRange(start=past_time + timedelta(hours=1), end=future_time)
        recent_logs = self.engine.get_logs(time_range=time_range)
        
        self.assertEqual(len(recent_logs), 1)
        self.assertEqual(recent_logs[0].message, "New message")
    
    def test_log_limit(self):
        """Test limiting log results"""
        for i in range(10):
            self.engine.log(LogLevel.INFO, EventType.TARGET_DISCOVERY, "agent_001", f"Message {i}")
        
        limited_logs = self.engine.get_logs(limit=5)
        self.assertEqual(len(limited_logs), 5)
    
    def test_get_logs_by_agent(self):
        """Test getting logs by agent with time window"""
        for i in range(5):
            self.engine.log(LogLevel.INFO, EventType.TARGET_DISCOVERY, "agent_001", f"Message {i}")
        
        agent_logs = self.engine.get_logs_by_agent("agent_001", hours=24)
        self.assertEqual(len(agent_logs), 5)


class TestTimelineVisualization(unittest.TestCase):
    """Test timeline visualization functionality"""
    
    def setUp(self):
        """Setup test engine with sample data"""
        self.engine = ReportingEngine()
        
        # Create sample logs
        timestamps = [
            datetime.now() - timedelta(minutes=10),
            datetime.now() - timedelta(minutes=5),
            datetime.now()
        ]
        
        self.engine.logs = []
        for i, ts in enumerate(timestamps):
            log = LogEntry(
                timestamp=ts,
                level=LogLevel.INFO if i % 2 == 0 else LogLevel.ERROR,
                event_type=EventType.ATTACK_INITIATED if i == 0 else EventType.STAGE_COMPLETED,
                agent_id="agent_001",
                message=f"Event {i}",
                details={}
            )
            self.engine.logs.append(log)
    
    def test_timeline_generation(self):
        """Test timeline generation"""
        timeline = self.engine.generate_timeline()
        
        self.assertEqual(len(timeline), 3)
        self.assertIsInstance(timeline[0], TimelineEvent)
    
    def test_timeline_ordering(self):
        """Test timeline is ordered by timestamp"""
        timeline = self.engine.generate_timeline()
        
        for i in range(len(timeline) - 1):
            self.assertLessEqual(timeline[i].timestamp, timeline[i+1].timestamp)
    
    def test_timeline_status_determination(self):
        """Test timeline status is correctly determined"""
        timeline = self.engine.generate_timeline()
        
        # Check that ERROR logs have "failure" status
        failure_events = [e for e in timeline if e.status == "failure"]
        self.assertGreater(len(failure_events), 0)
    
    def test_chain_timeline(self):
        """Test getting timeline for specific chain"""
        self.engine.log(
            LogLevel.INFO, EventType.ATTACK_INITIATED, "agent_001",
            "Chain started", chain_id="chain_001"
        )
        
        chain_timeline = self.engine.get_chain_timeline("chain_001")
        self.assertGreater(len(chain_timeline), 0)
        
        # All events should have matching chain_id
        for event in chain_timeline:
            self.assertEqual(event.metadata['chain_id'], "chain_001")
    
    def test_agent_timeline(self):
        """Test getting timeline for specific agent"""
        timeline = self.engine.get_agent_timeline("agent_001", hours=24)
        
        self.assertGreater(len(timeline), 0)
        
        # All events should have matching agent_id
        for event in timeline:
            self.assertEqual(event.metadata['agent_id'], "agent_001")


class TestAttackChainReconstruction(unittest.TestCase):
    """Test attack chain reconstruction functionality"""
    
    def setUp(self):
        """Setup test engine"""
        self.engine = ReportingEngine()
    
    def test_register_attack_chain(self):
        """Test registering a new attack chain"""
        self.engine.register_attack_chain(
            chain_id="chain_001",
            target_id="target_001",
            target_hostname="server-prod-01",
            target_platform="windows",
            planned_stages=[
                {'stage': 'reconnaissance', 'duration': 5},
                {'stage': 'initial_access', 'duration': 10}
            ]
        )
        
        self.assertIn("chain_001", self.engine.attack_chains)
        chain = self.engine.attack_chains["chain_001"]
        self.assertEqual(chain['target_hostname'], "server-prod-01")
    
    def test_mark_stage_completed(self):
        """Test marking stage as completed"""
        self.engine.register_attack_chain(
            chain_id="chain_001",
            target_id="target_001",
            target_hostname="server-prod-01",
            target_platform="windows",
            planned_stages=[{'stage': 'reconnaissance'}]
        )
        
        self.engine.mark_stage_completed(
            chain_id="chain_001",
            stage_name="reconnaissance",
            success=True,
            duration_ms=5000
        )
        
        chain = self.engine.attack_chains["chain_001"]
        self.assertEqual(len(chain['executed_stages']), 1)
        self.assertEqual(chain['executed_stages'][0]['success'], True)
    
    def test_mark_chain_completed(self):
        """Test marking chain as completed"""
        self.engine.register_attack_chain(
            chain_id="chain_001",
            target_id="target_001",
            target_hostname="server-prod-01",
            target_platform="windows",
            planned_stages=[{'stage': 'reconnaissance'}]
        )
        
        self.engine.mark_chain_completed(
            chain_id="chain_001",
            success=True
        )
        
        chain = self.engine.attack_chains["chain_001"]
        self.assertIsNotNone(chain['end_time'])
        self.assertEqual(chain['success'], True)
    
    def test_reconstruct_chain(self):
        """Test reconstructing attack chain"""
        self.engine.register_attack_chain(
            chain_id="chain_001",
            target_id="target_001",
            target_hostname="server-prod-01",
            target_platform="windows",
            planned_stages=[
                {'stage': 'reconnaissance'},
                {'stage': 'initial_access'}
            ]
        )
        
        self.engine.mark_stage_completed("chain_001", "reconnaissance", True, 5000)
        self.engine.mark_chain_completed("chain_001", True)
        
        reconstruction = self.engine.reconstruct_chain("chain_001")
        
        self.assertIsInstance(reconstruction, AttackChainReconstruction)
        self.assertEqual(reconstruction.chain_id, "chain_001")
        self.assertEqual(reconstruction.target_hostname, "server-prod-01")
        self.assertTrue(reconstruction.success)
        self.assertIsNotNone(reconstruction.total_duration_ms)
    
    def test_reconstruct_failed_chain(self):
        """Test reconstructing failed attack chain"""
        self.engine.register_attack_chain(
            chain_id="chain_001",
            target_id="target_001",
            target_hostname="server-prod-01",
            target_platform="windows",
            planned_stages=[{'stage': 'reconnaissance'}]
        )
        
        self.engine.mark_stage_completed("chain_001", "reconnaissance", False, 5000)
        self.engine.mark_chain_completed("chain_001", False, failure_point="reconnaissance")
        
        reconstruction = self.engine.reconstruct_chain("chain_001")
        
        self.assertFalse(reconstruction.success)
        self.assertEqual(reconstruction.failure_point, "reconnaissance")
    
    def test_deviation_detection(self):
        """Test detection of planned but not executed stages"""
        self.engine.register_attack_chain(
            chain_id="chain_001",
            target_id="target_001",
            target_hostname="server-prod-01",
            target_platform="windows",
            planned_stages=[
                {'stage': 'reconnaissance'},
                {'stage': 'initial_access'},
                {'stage': 'defense_evasion'}
            ]
        )
        
        # Only execute first stage
        self.engine.mark_stage_completed("chain_001", "reconnaissance", True, 5000)
        self.engine.mark_chain_completed("chain_001", False, failure_point="reconnaissance")
        
        reconstruction = self.engine.reconstruct_chain("chain_001")
        
        # Should detect 2 deviations
        self.assertEqual(len(reconstruction.deviations), 2)
    
    def test_get_all_chains(self):
        """Test getting all attack chains"""
        self.engine.register_attack_chain("chain_001", "target_001", "server1", "windows", [])
        self.engine.register_attack_chain("chain_002", "target_002", "server2", "linux", [])
        
        chains = self.engine.get_all_chains()
        self.assertEqual(len(chains), 2)


class TestSuccessFailureAnalytics(unittest.TestCase):
    """Test success/failure analytics functionality"""
    
    def setUp(self):
        """Setup test engine with mixed results"""
        self.engine = ReportingEngine()
        
        # Create sample logs with mixed success/failure
        for i in range(10):
            level = LogLevel.INFO if i % 2 == 0 else LogLevel.ERROR
            self.engine.log(
                level=level,
                event_type=EventType.STAGE_COMPLETED,
                agent_id="agent_001",
                message=f"Attempt {i}",
                duration_ms=1000 if i % 2 == 0 else 500
            )
    
    def test_calculate_success_rate(self):
        """Test calculating overall success rate"""
        success_rate = self.engine.calculate_success_rate()
        
        self.assertIn('total', success_rate)
        self.assertIn('success', success_rate)
        self.assertIn('failure', success_rate)
        self.assertIn('rate', success_rate)
        
        # Should be approximately 50% (5 success, 5 failure)
        self.assertAlmostEqual(success_rate['rate'], 0.5, places=1)
    
    def test_calculate_success_rate_by_event_type(self):
        """Test calculating success rate by event type"""
        self.engine.log(LogLevel.INFO, EventType.ATTACK_INITIATED, "agent_001", "Attack")
        self.engine.log(LogLevel.INFO, EventType.ATTACK_INITIATED, "agent_001", "Attack")
        self.engine.log(LogLevel.ERROR, EventType.ATTACK_INITIATED, "agent_001", "Attack failed")
        
        success_rate = self.engine.calculate_success_rate(by_event_type=True)
        
        self.assertIn('attack_initiated', success_rate)
        attack_rate = success_rate['attack_initiated']
        self.assertEqual(attack_rate['total'], 3)
    
    def test_get_failure_analysis(self):
        """Test getting failure analysis"""
        failure_analysis = self.engine.get_failure_analysis()
        
        self.assertIn('total_failures', failure_analysis)
        self.assertIn('by_event_type', failure_analysis)
        self.assertIn('by_target', failure_analysis)
        self.assertIn('common_messages', failure_analysis)
        
        # Should have 5 failures (from setup)
        self.assertEqual(failure_analysis['total_failures'], 5)
    
    def test_get_target_analytics(self):
        """Test getting analytics for specific target"""
        for i in range(5):
            level = LogLevel.INFO if i % 2 == 0 else LogLevel.ERROR
            self.engine.log(
                level=level,
                event_type=EventType.STAGE_COMPLETED,
                agent_id="agent_001",
                message=f"Target event {i}",
                target_id="target_001",
                duration_ms=1000
            )
        
        analytics = self.engine.get_target_analytics("target_001")
        
        self.assertEqual(analytics['target_id'], "target_001")
        self.assertIn('total_events', analytics)
        self.assertIn('by_event_type', analytics)
        self.assertIn('by_level', analytics)
        self.assertGreater(analytics['total_events'], 0)


class TestPerformanceBenchmarking(unittest.TestCase):
    """Test performance benchmarking functionality"""
    
    def setUp(self):
        """Setup test engine with performance data"""
        self.engine = ReportingEngine()
        
        # Add performance data
        for i in range(10):
            duration = 1000 + (i * 100)
            success = i % 2 == 0
            self.engine.log(
                level=LogLevel.INFO,
                event_type=EventType.STAGE_COMPLETED,
                agent_id="agent_001",
                message=f"Operation {i}",
                duration_ms=duration
            )
    
    def test_update_performance_metrics(self):
        """Test updating performance metrics"""
        self.engine.update_performance_metrics()
        
        self.assertGreater(len(self.engine.performance_metrics), 0)
    
    def test_get_performance_metrics_summary(self):
        """Test getting performance metrics summary"""
        self.engine.update_performance_metrics()
        metrics = self.engine.get_performance_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertGreater(len(metrics), 0)
    
    def test_get_performance_metrics_for_operation(self):
        """Test getting performance metrics for specific operation"""
        self.engine.update_performance_metrics()
        
        metrics = self.engine.get_performance_metrics(operation_type="stage_completed")
        
        self.assertEqual(metrics['operation_type'], "stage_completed")
        self.assertIn('total_operations', metrics)
        self.assertIn('average_duration_ms', metrics)
        self.assertIn('success_rate', metrics)
    
    def test_compare_performance(self):
        """Test comparing performance between operations"""
        # Add two operation types
        for i in range(5):
            self.engine.log(
                LogLevel.INFO, EventType.TARGET_DISCOVERY, "agent_001",
                "Discovery", duration_ms=500
            )
        
        self.engine.update_performance_metrics()
        
        comparison = self.engine.compare_performance(["target_discovery", "stage_completed"])
        
        self.assertIn('target_discovery', comparison)
        self.assertIn('stage_completed', comparison)
        
        for op_type, metrics in comparison.items():
            self.assertIn('avg_duration_ms', metrics)
            self.assertIn('success_rate', metrics)


class TestExportFunctions(unittest.TestCase):
    """Test export functionality"""
    
    def setUp(self):
        """Setup test engine with sample data"""
        self.engine = ReportingEngine()
        
        # Add sample data
        for i in range(5):
            self.engine.log(
                LogLevel.INFO,
                EventType.TARGET_DISCOVERY,
                "agent_001",
                f"Discovery {i}",
                target_id=f"target_00{i}",
                duration_ms=1000 + (i * 100)
            )
        
        self.engine.register_attack_chain(
            "chain_001", "target_001", "server1", "windows",
            [{'stage': 'reconnaissance'}]
        )
        self.engine.mark_stage_completed("chain_001", "reconnaissance", True, 5000)
        self.engine.mark_chain_completed("chain_001", True)
    
    def test_export_logs_to_csv(self):
        """Test exporting logs to CSV"""
        csv_data = self.engine.export_logs_to_csv()
        
        self.assertIsInstance(csv_data, str)
        self.assertIn('timestamp', csv_data)
        self.assertIn('level', csv_data)
        self.assertIn('agent_id', csv_data)
    
    def test_export_timeline_to_csv(self):
        """Test exporting timeline to CSV"""
        csv_data = self.engine.export_timeline_to_csv()
        
        self.assertIsInstance(csv_data, str)
        self.assertIn('timestamp', csv_data)
        self.assertIn('event_type', csv_data)
        self.assertIn('title', csv_data)
    
    def test_export_chains_to_json(self):
        """Test exporting chains to JSON"""
        import json
        
        json_data = self.engine.export_chains_to_json()
        
        self.assertIsInstance(json_data, str)
        chains = json.loads(json_data)
        self.assertIsInstance(chains, list)
        self.assertGreater(len(chains), 0)
    
    def test_export_analytics_to_json(self):
        """Test exporting analytics to JSON"""
        import json
        
        json_data = self.engine.export_analytics_to_json()
        
        self.assertIsInstance(json_data, str)
        analytics = json.loads(json_data)
        self.assertIn('success_rate', analytics)
        self.assertIn('failure_analysis', analytics)
        self.assertIn('performance_metrics', analytics)
    
    def test_generate_summary_report(self):
        """Test generating summary report"""
        summary = self.engine.generate_summary_report(hours=24)
        
        self.assertIn('report_period', summary)
        self.assertIn('summary', summary)
        self.assertIn('success_rate_by_event_type', summary)
        self.assertIn('failure_analysis', summary)
        self.assertIn('performance_metrics', summary)
        
        self.assertEqual(summary['report_period']['hours'], 24)


if __name__ == '__main__':
    unittest.main(verbosity=2)