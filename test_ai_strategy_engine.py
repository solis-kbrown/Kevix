"""
Test Suite for AI Strategy Engine

Tests for:
- Target prioritization
- Attack chain generation
- Evasion technique selection
- Outcome recording
- Pattern analysis
- Strategy adaptation
"""

import unittest
import sys
import os
from datetime import datetime

# Add agent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

from ai_strategy_engine import (
    AIStrategyEngine,
    Target,
    TargetPriority,
    AttackStage,
    EvasionTechnique,
    AttackChain
)


class TestTargetPrioritization(unittest.TestCase):
    """Test target prioritization functionality"""
    
    def setUp(self):
        """Setup test engine"""
        self.engine = AIStrategyEngine()
    
    def test_add_target(self):
        """Test adding a target"""
        target = Target(
            target_id="test_001",
            hostname="test-server",
            ip_address="10.0.0.1",
            platform="windows",
            priority_score=0.8,
            vulnerability_score=0.85,
            value_score=0.9,
            accessibility_score=0.75,
            risk_score=0.6,
            last_scanned=datetime.now()
        )
        self.engine.add_target(target)
        
        self.assertEqual(len(self.engine.targets), 1)
        self.assertIn("test_001", self.engine.targets)
    
    def test_target_prioritization(self):
        """Test target prioritization ranking"""
        # Add targets with different scores
        high_target = Target(
            target_id="high_001",
            hostname="high-value",
            ip_address="10.0.0.1",
            platform="windows",
            priority_score=0.9,
            vulnerability_score=0.95,
            value_score=0.9,
            accessibility_score=0.8,
            risk_score=0.7,
            last_scanned=datetime.now()
        )
        
        low_target = Target(
            target_id="low_001",
            hostname="low-value",
            ip_address="10.0.0.2",
            platform="linux",
            priority_score=0.3,
            vulnerability_score=0.4,
            value_score=0.3,
            accessibility_score=0.5,
            risk_score=0.2,
            last_scanned=datetime.now()
        )
        
        self.engine.add_target(low_target)
        self.engine.add_target(high_target)
        
        # Prioritize
        prioritized = self.engine.prioritize_targets()
        
        # High value should be first
        self.assertEqual(prioritized[0].target_id, "high_001")
        self.assertEqual(prioritized[1].target_id, "low_001")
    
    def test_target_priority_levels(self):
        """Test target priority level assignment"""
        critical_target = Target(
            target_id="critical_001",
            hostname="critical",
            ip_address="10.0.0.1",
            platform="windows",
            priority_score=0.95,
            vulnerability_score=0.95,
            value_score=0.95,
            accessibility_score=0.9,
            risk_score=0.8,
            last_scanned=datetime.now()
        )
        
        self.engine.add_target(critical_target)
        
        self.assertEqual(critical_target.get_priority(), TargetPriority.CRITICAL)
    
    def test_update_target_score(self):
        """Test updating target scores"""
        target = Target(
            target_id="update_001",
            hostname="update-test",
            ip_address="10.0.0.1",
            platform="windows",
            priority_score=0.5,
            vulnerability_score=0.5,
            value_score=0.5,
            accessibility_score=0.5,
            risk_score=0.5,
            last_scanned=datetime.now()
        )
        self.engine.add_target(target)
        
        # Update scores
        self.engine.update_target_score("update_001", vulnerability_score=0.9)
        
        # Verify update
        updated_target = self.engine.targets["update_001"]
        self.assertEqual(updated_target.vulnerability_score, 0.9)
        self.assertGreater(updated_target.overall_score, 0.5)


class TestAttackChainGeneration(unittest.TestCase):
    """Test attack chain generation functionality"""
    
    def setUp(self):
        """Setup test engine and target"""
        self.engine = AIStrategyEngine()
        self.target = Target(
            target_id="chain_001",
            hostname="chain-test",
            ip_address="10.0.0.1",
            platform="windows",
            priority_score=0.8,
            vulnerability_score=0.85,
            value_score=0.9,
            accessibility_score=0.75,
            risk_score=0.6,
            last_scanned=datetime.now()
        )
        self.engine.add_target(self.target)
    
    def test_generate_attack_chain(self):
        """Test attack chain generation"""
        chain = self.engine.generate_attack_chain(self.target)
        
        self.assertIsInstance(chain, AttackChain)
        self.assertEqual(chain.target_id, "chain_001")
        self.assertGreater(len(chain.stages), 0)
        self.assertGreater(chain.success_probability, 0.0)
        self.assertGreater(chain.estimated_time, 0)
    
    def test_attack_chain_stages(self):
        """Test attack chain includes required stages"""
        chain = self.engine.generate_attack_chain(self.target)
        
        stage_types = [stage['stage'] for stage in chain.stages]
        
        # Should include reconnaissance
        self.assertIn(AttackStage.RECONNAISSANCE.value, stage_types)
        # Should include initial access
        self.assertIn(AttackStage.INITIAL_ACCESS.value, stage_types)
        # Should include defense evasion
        self.assertIn(AttackStage.DEFENSE_EVASION.value, stage_types)
    
    def test_windows_specific_stages(self):
        """Test Windows-specific stages"""
        windows_target = Target(
            target_id="win_001",
            hostname="win-test",
            ip_address="10.0.0.1",
            platform="windows",
            priority_score=0.7,
            vulnerability_score=0.75,
            value_score=0.8,
            accessibility_score=0.7,
            risk_score=0.5,
            last_scanned=datetime.now()
        )
        self.engine.add_target(windows_target)
        
        chain = self.engine.generate_attack_chain(windows_target)
        stages = chain.stages
        
        # Check for SMB exploit in initial access
        initial_access = [s for s in stages if s['stage'] == AttackStage.INITIAL_ACCESS.value]
        self.assertEqual(len(initial_access), 1)
        self.assertEqual(initial_access[0]['technique'], 'smb_exploit')
    
    def test_linux_specific_stages(self):
        """Test Linux-specific stages"""
        linux_target = Target(
            target_id="linux_001",
            hostname="linux-test",
            ip_address="10.0.0.2",
            platform="linux",
            priority_score=0.7,
            vulnerability_score=0.75,
            value_score=0.8,
            accessibility_score=0.7,
            risk_score=0.5,
            last_scanned=datetime.now()
        )
        self.engine.add_target(linux_target)
        
        chain = self.engine.generate_attack_chain(linux_target)
        stages = chain.stages
        
        # Check for SSH brute force in initial access
        initial_access = [s for s in stages if s['stage'] == AttackStage.INITIAL_ACCESS.value]
        self.assertEqual(len(initial_access), 1)
        self.assertEqual(initial_access[0]['technique'], 'ssh_brute_force')
    
    def test_high_value_exfiltration(self):
        """Test high-value targets include exfiltration"""
        high_value_target = Target(
            target_id="high_val_001",
            hostname="high-value",
            ip_address="10.0.0.1",
            platform="windows",
            priority_score=0.9,
            vulnerability_score=0.85,
            value_score=0.95,  # High value
            accessibility_score=0.75,
            risk_score=0.6,
            last_scanned=datetime.now()
        )
        self.engine.add_target(high_value_target)
        
        chain = self.engine.generate_attack_chain(high_value_target)
        stage_types = [stage['stage'] for stage in chain.stages]
        
        # Should include collection and exfiltration
        self.assertIn(AttackStage.COLLECTION.value, stage_types)
        self.assertIn(AttackStage.EXFILTRATION.value, stage_types)


class TestEvasionTechniqueSelection(unittest.TestCase):
    """Test evasion technique selection functionality"""
    
    def setUp(self):
        """Setup test engine and target"""
        self.engine = AIStrategyEngine()
        self.target = Target(
            target_id="evasion_001",
            hostname="evasion-test",
            ip_address="10.0.0.1",
            platform="windows",
            priority_score=0.8,
            vulnerability_score=0.85,
            value_score=0.9,
            accessibility_score=0.75,
            risk_score=0.6,
            last_scanned=datetime.now()
        )
        self.engine.add_target(self.target)
    
    def test_select_evasion_technique(self):
        """Test evasion technique selection"""
        technique = self.engine.select_evasion_technique(self.target)
        
        self.assertIsInstance(technique, EvasionTechnique)
        self.assertIn(technique, EvasionTechnique)
    
    def test_evasion_with_antivirus(self):
        """Test evasion selection with antivirus detected"""
        av_target = Target(
            target_id="av_001",
            hostname="av-test",
            ip_address="10.0.0.1",
            platform="windows",
            priority_score=0.7,
            vulnerability_score=0.75,
            value_score=0.8,
            accessibility_score=0.7,
            risk_score=0.5,
            last_scanned=datetime.now(),
            detected_defenses=['anti_virus']
        )
        self.engine.add_target(av_target)
        
        technique = self.engine.select_evasion_technique(av_target)
        
        # Should select AV-aware technique
        self.assertIn(technique, [
            EvasionTechnique.MEMORY_ONLY,
            EvasionTechnique.PROCESS_INJECTION,
            EvasionTechnique.POLYMORPHIC_CODE
        ])
    
    def test_record_evasion_result(self):
        """Test recording evasion results"""
        technique = EvasionTechnique.PROCESS_INJECTION.value
        
        # Record successful result
        self.engine.record_evasion_result(technique, success=True)
        self.engine.record_evasion_result(technique, success=True)
        self.engine.record_evasion_result(technique, success=False)
        
        # Check tracking
        self.assertEqual(self.engine.evasion_attempts[technique], 3)
        self.assertEqual(self.engine.evasion_successes[technique], 2)
        self.assertAlmostEqual(self.engine.evasion_success_rates[technique], 2/3)
    
    def test_evasion_success_rate_learning(self):
        """Test evasion learning from results"""
        technique1 = EvasionTechnique.MEMORY_ONLY.value
        technique2 = EvasionTechnique.PROCESS_INJECTION.value
        
        # Record many successful attempts for technique1
        for _ in range(10):
            self.engine.record_evasion_result(technique1, success=True)
        
        # Record failures for technique2
        for _ in range(10):
            self.engine.record_evasion_result(technique2, success=True)
        for _ in range(10):
            self.engine.record_evasion_result(technique2, success=False)
        
        # Technique1 should have higher success rate
        self.assertGreater(
            self.engine.evasion_success_rates[technique1],
            self.engine.evasion_success_rates[technique2]
        )


class TestOutcomeRecording(unittest.TestCase):
    """Test outcome recording and learning"""
    
    def setUp(self):
        """Setup test engine"""
        self.engine = AIStrategyEngine()
        
        # Add test target
        self.target = Target(
            target_id="outcome_001",
            hostname="outcome-test",
            ip_address="10.0.0.1",
            platform="windows",
            priority_score=0.8,
            vulnerability_score=0.85,
            value_score=0.9,
            accessibility_score=0.75,
            risk_score=0.6,
            last_scanned=datetime.now()
        )
        self.engine.add_target(self.target)
    
    def test_record_successful_outcome(self):
        """Test recording successful outcome"""
        chain = self.engine.generate_attack_chain(self.target)
        self.engine.record_outcome(chain.chain_id, success=True)
        
        self.assertEqual(self.engine.metrics.total_attempts, 1)
        self.assertEqual(self.engine.metrics.successful_attempts, 1)
        self.assertEqual(self.engine.metrics.failed_attempts, 0)
        self.assertEqual(self.engine.metrics.success_rate, 1.0)
    
    def test_record_failed_outcome(self):
        """Test recording failed outcome"""
        chain = self.engine.generate_attack_chain(self.target)
        self.engine.record_outcome(chain.chain_id, success=False)
        
        self.assertEqual(self.engine.metrics.total_attempts, 1)
        self.assertEqual(self.engine.metrics.successful_attempts, 0)
        self.assertEqual(self.engine.metrics.failed_attempts, 1)
        self.assertEqual(self.engine.metrics.success_rate, 0.0)
    
    def test_mixed_outcomes(self):
        """Test mixed success and failure outcomes"""
        chain1 = self.engine.generate_attack_chain(self.target)
        chain2 = self.engine.generate_attack_chain(self.target)
        chain3 = self.engine.generate_attack_chain(self.target)
        
        self.engine.record_outcome(chain1.chain_id, success=True)
        self.engine.record_outcome(chain2.chain_id, success=True)
        self.engine.record_outcome(chain3.chain_id, success=False)
        
        self.assertEqual(self.engine.metrics.total_attempts, 3)
        self.assertEqual(self.engine.metrics.successful_attempts, 2)
        self.assertEqual(self.engine.metrics.failed_attempts, 1)
        self.assertAlmostEqual(self.engine.metrics.success_rate, 2/3)


class TestPatternAnalysis(unittest.TestCase):
    """Test pattern analysis functionality"""
    
    def setUp(self):
        """Setup test engine with learning data"""
        self.engine = AIStrategyEngine()
        
        # Add target
        self.target = Target(
            target_id="analysis_001",
            hostname="analysis-test",
            ip_address="10.0.0.1",
            platform="windows",
            priority_score=0.8,
            vulnerability_score=0.85,
            value_score=0.9,
            accessibility_score=0.75,
            risk_score=0.6,
            last_scanned=datetime.now()
        )
        self.engine.add_target(self.target)
        
        # Generate and record multiple chains
        for i in range(10):
            chain = self.engine.generate_attack_chain(self.target)
            success = i % 2 == 0  # Alternate success/failure
            self.engine.record_outcome(chain.chain_id, success=success)
    
    def test_analyze_patterns(self):
        """Test pattern analysis"""
        analysis = self.engine.analyze_patterns()
        
        self.assertIn('total_outcomes', analysis)
        self.assertIn('successful', analysis)
        self.assertIn('failed', analysis)
        self.assertIn('success_rate', analysis)
        self.assertEqual(analysis['total_outcomes'], 10)
    
    def test_common_successful_stages(self):
        """Test identification of common successful stages"""
        analysis = self.engine.analyze_patterns()
        
        self.assertIn('common_successful_stages', analysis)
        self.assertIsInstance(analysis['common_successful_stages'], dict)
    
    def test_platform_analysis(self):
        """Test platform-specific success analysis"""
        analysis = self.engine.analyze_patterns()
        
        self.assertIn('target_platform_success', analysis)
        self.assertIn('windows', analysis['target_platform_success'])


class TestStrategyAdaptation(unittest.TestCase):
    """Test strategy adaptation functionality"""
    
    def setUp(self):
        """Setup test engine"""
        self.engine = AIStrategyEngine()
        
        # Add target
        self.target = Target(
            target_id="adapt_001",
            hostname="adapt-test",
            ip_address="10.0.0.1",
            platform="windows",
            priority_score=0.8,
            vulnerability_score=0.85,
            value_score=0.9,
            accessibility_score=0.75,
            risk_score=0.6,
            last_scanned=datetime.now()
        )
        self.engine.add_target(self.target)
    
    def test_adapt_strategy(self):
        """Test strategy adaptation"""
        # Generate 10 chains with outcomes
        for i in range(10):
            chain = self.engine.generate_attack_chain(self.target)
            success = i < 7  # 70% success rate
            self.engine.record_outcome(chain.chain_id, success=success)
        
        initial_version = self.engine.strategy_version
        initial_adaptations = self.engine.metrics.adaptation_count
        
        # Adapt
        self.engine.adapt_strategy()
        
        # Verify adaptation
        self.assertEqual(self.engine.strategy_version, initial_version + 1)
        self.assertEqual(self.engine.metrics.adaptation_count, initial_adaptations + 1)
        self.assertIsNotNone(self.engine.metrics.last_adaptation)
    
    def test_adaptation_requires_minimum_data(self):
        """Test adaptation requires minimum learning data"""
        # Only add 5 outcomes (less than minimum)
        for i in range(5):
            chain = self.engine.generate_attack_chain(self.target)
            self.engine.record_outcome(chain.chain_id, success=True)
        
        initial_version = self.engine.strategy_version
        
        # Adapt should not change version
        self.engine.adapt_strategy()
        
        self.assertEqual(self.engine.strategy_version, initial_version)
    
    def test_strategy_history(self):
        """Test strategy history tracking"""
        # Generate and record outcomes
        for i in range(10):
            chain = self.engine.generate_attack_chain(self.target)
            self.engine.record_outcome(chain.chain_id, success=True)
        
        # Adapt twice
        self.engine.adapt_strategy()
        self.engine.adapt_strategy()
        
        # Check history
        self.assertEqual(len(self.engine.strategy_history), 2)
        self.assertEqual(self.engine.strategy_history[0]['version'], 1)
        self.assertEqual(self.engine.strategy_history[1]['version'], 2)


class TestMetricsAndReporting(unittest.TestCase):
    """Test metrics and reporting functionality"""
    
    def setUp(self):
        """Setup test engine"""
        self.engine = AIStrategyEngine()
        
        # Add test target
        self.target = Target(
            target_id="metrics_001",
            hostname="metrics-test",
            ip_address="10.0.0.1",
            platform="windows",
            priority_score=0.8,
            vulnerability_score=0.85,
            value_score=0.9,
            accessibility_score=0.75,
            risk_score=0.6,
            last_scanned=datetime.now()
        )
        self.engine.add_target(self.target)
    
    def test_get_metrics(self):
        """Test metrics retrieval"""
        # Generate and record some chains
        for _ in range(5):
            chain = self.engine.generate_attack_chain(self.target)
            self.engine.record_outcome(chain.chain_id, success=True)
        
        metrics = self.engine.get_metrics()
        
        self.assertIn('total_attempts', metrics)
        self.assertIn('successful_attempts', metrics)
        self.assertIn('success_rate', metrics)
        self.assertIn('attack_chains_generated', metrics)
        self.assertEqual(metrics['total_attempts'], 5)
        self.assertEqual(metrics['successful_attempts'], 5)
    
    def test_get_target_summary(self):
        """Test target summary"""
        # Add multiple targets
        for i in range(3):
            target = Target(
                target_id=f"target_{i}",
                hostname=f"target-{i}",
                ip_address=f"10.0.0.{i+1}",
                platform="windows" if i % 2 == 0 else "linux",
                priority_score=0.5 + (i * 0.1),
                vulnerability_score=0.6 + (i * 0.1),
                value_score=0.7 if i == 2 else 0.4,
                accessibility_score=0.5 + (i * 0.1),
                risk_score=0.4 + (i * 0.1),
                last_scanned=datetime.now()
            )
            self.engine.add_target(target)
        
        summary = self.engine.get_target_summary()
        
        self.assertIn('total_targets', summary)
        self.assertIn('by_priority', summary)
        self.assertEqual(summary['total_targets'], 3)
    
    def test_get_attack_chains_summary(self):
        """Test attack chains summary"""
        # Generate multiple chains
        for _ in range(5):
            chain = self.engine.generate_attack_chain(self.target)
        
        summary = self.engine.get_attack_chains_summary()
        
        self.assertIn('total_chains', summary)
        self.assertIn('by_priority', summary)
        self.assertEqual(summary['total_chains'], 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)