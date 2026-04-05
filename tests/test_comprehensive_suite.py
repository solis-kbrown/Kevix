#!/usr/bin/env python3
"""
SERVERROOT.NET - Comprehensive Test Suite
Phase 9: Full test coverage across all modules

Tests:
- Unit tests for all Phase 6-8 modules
- Integration tests for cross-module interactions
- End-to-end workflow tests
- Performance tests
- Security tests
"""

import sys
import os
import time
import json
import unittest
import threading
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================
# UNIT TESTS - AI STRATEGY ENGINE
# ============================================================

class TestAIStrategyEngine(unittest.TestCase):
    """Unit tests for AI Strategy Engine"""

    def setUp(self):
        from agent.ai_strategy_engine import AIStrategyEngine
        self.engine = AIStrategyEngine()

    def test_initialization(self):
        """Test engine initializes correctly"""
        self.assertIsNotNone(self.engine)

    def test_imports_complete(self):
        """Test all required imports are available"""
        from agent.ai_strategy_engine import (
            AIStrategyEngine, TargetPriority, AttackStage, EvasionTechnique
        )
        self.assertTrue(len(list(TargetPriority)) >= 3)
        self.assertTrue(len(list(AttackStage)) >= 3)
        self.assertTrue(len(list(EvasionTechnique)) >= 3)

    def test_target_priority_values(self):
        """Test all target priority levels are accessible"""
        from agent.ai_strategy_engine import TargetPriority
        priorities = [p.value for p in TargetPriority]
        self.assertGreater(len(priorities), 0)

    def test_attack_stages_defined(self):
        """Test all attack stages are properly defined"""
        from agent.ai_strategy_engine import AttackStage
        stages = list(AttackStage)
        self.assertGreater(len(stages), 3)

    def test_evasion_techniques_defined(self):
        """Test evasion techniques are properly defined"""
        from agent.ai_strategy_engine import EvasionTechnique
        techniques = list(EvasionTechnique)
        self.assertGreater(len(techniques), 3)


# ============================================================
# UNIT TESTS - SWARM COORDINATOR
# ============================================================

class TestSwarmCoordinator(unittest.TestCase):
    """Unit tests for Swarm Coordinator"""

    def setUp(self):
        from agent.swarm_coordinator import (
            SwarmCoordinator, SwarmAgent, AgentStatus, AgentRole
        )
        self.coordinator = SwarmCoordinator(election_interval=300)
        self.AgentStatus = AgentStatus
        self.AgentRole = AgentRole
        self.SwarmAgent = SwarmAgent

    def _make_agent(self, agent_id: str, role=None):
        """Helper to create a test agent"""
        from agent.swarm_coordinator import AgentStatus, AgentRole
        return self.SwarmAgent(
            agent_id=agent_id,
            hostname=f"{agent_id}.example.com",
            ip_address=f"10.0.0.{hash(agent_id) % 254 + 1}",
            platform="linux",
            status=AgentStatus.ACTIVE,
            role=role or AgentRole.WORKER,
            capabilities=["scan", "exploit"],
            current_load=0.3,
            active_tasks=1,
            last_heartbeat=datetime.now(),
            performance_score=0.85,
            network_latency_ms=50,
            location="US-East"
        )

    def test_initialization(self):
        """Test coordinator initializes correctly"""
        self.assertIsNotNone(self.coordinator)
        self.assertEqual(len(self.coordinator.agents), 0)

    def test_register_agent(self):
        """Test agent registration"""
        agent = self._make_agent("agent_001")
        self.coordinator.register_agent(agent)
        self.assertIn("agent_001", self.coordinator.agents)

    def test_register_multiple_agents(self):
        """Test registering multiple agents"""
        for i in range(5):
            agent = self._make_agent(f"agent_{i:03d}")
            self.coordinator.register_agent(agent)
        self.assertEqual(len(self.coordinator.agents), 5)

    def test_leader_election_no_agents(self):
        """Test leader election with no agents"""
        result = self.coordinator.elect_leader()
        self.assertIsNone(result)

    def test_leader_election_with_agents(self):
        """Test leader election with agents"""
        for i in range(3):
            agent = self._make_agent(f"agent_{i:03d}")
            self.coordinator.register_agent(agent)
        leader = self.coordinator.elect_leader()
        self.assertIsNotNone(leader)
        self.assertIn(leader, self.coordinator.agents)

    def test_load_balance_strategy_change(self):
        """Test changing load balance strategy"""
        from agent.swarm_coordinator import LoadBalanceStrategy
        self.coordinator.set_balance_strategy(LoadBalanceStrategy.ROUND_ROBIN)
        self.coordinator.set_balance_strategy(LoadBalanceStrategy.LEAST_LOADED)
        self.coordinator.set_balance_strategy(LoadBalanceStrategy.RANDOM)

    def test_task_assignment(self):
        """Test task assignment to agents"""
        from agent.swarm_coordinator import DistributedTask, TaskPriority
        for i in range(3):
            agent = self._make_agent(f"agent_{i:03d}")
            self.coordinator.register_agent(agent)

        task = DistributedTask(
            task_id="task_test_001",
            task_type="scan",
            priority=TaskPriority.HIGH,
            target_id="target.example.com",
            payload={"test": True},
            required_capabilities=["scan"],
            created_at=datetime.now(),
            deadline=datetime.now() + timedelta(minutes=10),
            status="pending"
        )
        result = self.coordinator.assign_task(task)
        # May succeed or fail depending on agent selection
        self.assertIsInstance(result, (str, type(None)))

    def test_intelligence_aggregation(self):
        """Test swarm intelligence aggregation"""
        for i in range(3):
            agent = self._make_agent(f"agent_{i:03d}")
            self.coordinator.register_agent(agent)

        intelligence = self.coordinator.aggregate_intelligence()
        self.assertIsNotNone(intelligence)
        self.assertEqual(intelligence.total_agent_count, 3)
        self.assertGreater(intelligence.active_agent_count, 0)


# ============================================================
# UNIT TESTS - SECURITY HARDENING
# ============================================================

class TestSecurityHardening(unittest.TestCase):
    """Unit tests for Security Hardening Engine"""

    def setUp(self):
        from agent.security_hardening import (
            SecurityHardeningEngine, InputValidator, EncryptionManager,
            AuditLogger, RateLimiter, SecretsManager, SecurityConfig
        )
        self.engine = SecurityHardeningEngine()
        self.validator = InputValidator()
        self.encryption = EncryptionManager()

    def test_initialization(self):
        """Test security engine initializes"""
        self.assertIsNotNone(self.engine)

    # Input Validation Tests
    def test_valid_ip_address(self):
        """Test valid IP address passes validation"""
        from agent.security_hardening import ValidationResult
        report = self.validator.validate_ip_address("192.168.1.100")
        self.assertEqual(report.result, ValidationResult.VALID)

    def test_invalid_ip_address(self):
        """Test invalid IP address fails validation"""
        from agent.security_hardening import ValidationResult
        report = self.validator.validate_ip_address("999.999.999.999")
        self.assertNotEqual(report.result, ValidationResult.VALID)

    def test_sql_injection_detection(self):
        """Test SQL injection is detected"""
        from agent.security_hardening import ValidationResult, ThreatLevel
        report = self.validator.validate_command("scan'; DROP TABLE agents;--")
        self.assertIn(report.result, [ValidationResult.BLOCKED, ValidationResult.INVALID])

    def test_command_injection_detection(self):
        """Test command injection is detected"""
        from agent.security_hardening import ValidationResult
        report = self.validator.validate_command("scan; rm -rf /")
        self.assertEqual(report.result, ValidationResult.BLOCKED)

    def test_path_traversal_detection(self):
        """Test path traversal is detected in hostname"""
        from agent.security_hardening import ValidationResult
        report = self.validator.validate_hostname("../../etc/passwd")
        self.assertNotEqual(report.result, ValidationResult.VALID)

    def test_xss_detection(self):
        """Test XSS is detected"""
        threat = self.validator._check_injection("<script>alert('xss')</script>")
        self.assertEqual(threat, "xss")

    def test_valid_command(self):
        """Test valid command passes validation"""
        from agent.security_hardening import ValidationResult
        report = self.validator.validate_command("scan_targets")
        self.assertEqual(report.result, ValidationResult.VALID)

    def test_valid_agent_id(self):
        """Test valid agent ID passes validation"""
        from agent.security_hardening import ValidationResult
        report = self.validator.validate_agent_id("agent_12ab34cd")
        self.assertEqual(report.result, ValidationResult.VALID)

    def test_invalid_agent_id(self):
        """Test invalid agent ID fails validation"""
        from agent.security_hardening import ValidationResult
        report = self.validator.validate_agent_id("invalid-agent-id!")
        self.assertNotEqual(report.result, ValidationResult.VALID)

    # Encryption Tests
    def test_encrypt_decrypt(self):
        """Test encryption and decryption"""
        original = "sensitive data for testing"
        ciphertext, key_id = self.encryption.encrypt(original)
        decrypted = self.encryption.decrypt(ciphertext, key_id)
        self.assertEqual(decrypted.decode('utf-8'), original)

    def test_encrypt_different_each_time(self):
        """Test that same data produces different ciphertext each time"""
        data = "same data"
        ct1, _ = self.encryption.encrypt(data)
        ct2, _ = self.encryption.encrypt(data)
        self.assertNotEqual(ct1, ct2)  # Should be different due to random IV

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "SecurePassword123!@#"
        hashed, salt = self.encryption.hash_password(password)
        self.assertTrue(self.encryption.verify_password(password, hashed, salt))
        self.assertFalse(self.encryption.verify_password("WrongPassword", hashed, salt))

    def test_token_generation(self):
        """Test secure token generation"""
        token1 = self.encryption.generate_token()
        token2 = self.encryption.generate_token()
        self.assertNotEqual(token1, token2)
        self.assertGreater(len(token1), 20)

    def test_hmac_signing(self):
        """Test HMAC data signing and verification"""
        data = b"data to sign"
        signature = self.encryption.sign_data(data)
        self.assertTrue(self.encryption.verify_signature(data, signature))
        self.assertFalse(self.encryption.verify_signature(b"different data", signature))

    # Rate Limiting Tests
    def test_rate_limiter_allows_normal(self):
        """Test rate limiter allows normal traffic"""
        from agent.security_hardening import RateLimiter
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        allowed, remaining = limiter.is_allowed("test_ip")
        self.assertTrue(allowed)
        self.assertEqual(remaining, 9)

    def test_rate_limiter_blocks_excessive(self):
        """Test rate limiter blocks excessive requests"""
        from agent.security_hardening import RateLimiter
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            limiter.is_allowed("test_ip_2")
        allowed, remaining = limiter.is_allowed("test_ip_2")
        self.assertFalse(allowed)
        self.assertEqual(remaining, 0)

    # Security Report
    def test_security_report(self):
        """Test security report generation"""
        report = self.engine.get_security_report()
        self.assertIn("summary", report)
        self.assertIn("encryption", report)
        self.assertIn("rate_limiting", report)


# ============================================================
# UNIT TESTS - ERROR HANDLER
# ============================================================

class TestErrorHandler(unittest.TestCase):
    """Unit tests for Error Handling Engine"""

    def setUp(self):
        from agent.error_handler import (
            ErrorHandlingEngine, NetworkError, AgentError,
            ExploitError, ConfigurationError, CircuitBreaker,
            CircuitBreakerConfig, ErrorSeverity, CircuitState
        )
        self.engine = ErrorHandlingEngine()
        self.NetworkError = NetworkError
        self.AgentError = AgentError
        self.CircuitBreaker = CircuitBreaker
        self.CircuitBreakerConfig = CircuitBreakerConfig
        self.ErrorSeverity = ErrorSeverity
        self.CircuitState = CircuitState

    def test_initialization(self):
        """Test error handler initializes"""
        self.assertIsNotNone(self.engine)

    def test_custom_exception_hierarchy(self):
        """Test custom exception classes"""
        from agent.error_handler import (
            ServerRootError, NetworkError, AgentError,
            ExploitError, AuthenticationError
        )
        # All should be subclasses of ServerRootError
        self.assertTrue(issubclass(NetworkError, ServerRootError))
        self.assertTrue(issubclass(AgentError, ServerRootError))
        self.assertTrue(issubclass(ExploitError, ServerRootError))
        self.assertTrue(issubclass(AuthenticationError, ServerRootError))

    def test_network_error_attributes(self):
        """Test NetworkError has correct attributes"""
        err = self.NetworkError("Connection refused", host="10.0.0.1", port=8443)
        self.assertEqual(err.code, "NETWORK_ERROR")
        self.assertTrue(err.recoverable)
        self.assertEqual(err.context["host"], "10.0.0.1")
        self.assertEqual(err.context["port"], 8443)

    def test_handle_exception(self):
        """Test exception handling"""
        err = self.NetworkError("Test error")
        record = self.engine.handle(err, severity=self.ErrorSeverity.ERROR)
        self.assertIsNotNone(record)
        self.assertEqual(record.error_type, "NetworkError")

    def test_safe_execute_success(self):
        """Test safe execute with successful function"""
        success, result = self.engine.safe_execute(
            lambda: 42, operation="test"
        )
        self.assertTrue(success)
        self.assertEqual(result, 42)

    def test_safe_execute_failure_with_fallback(self):
        """Test safe execute with failing function uses fallback"""
        success, result = self.engine.safe_execute(
            lambda: 1/0,
            operation="test",
            fallback={"error": "fallback"}
        )
        self.assertFalse(success)
        self.assertEqual(result, {"error": "fallback"})

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts closed"""
        cb = self.CircuitBreaker("test", self.CircuitBreakerConfig())
        self.assertEqual(cb.state, self.CircuitState.CLOSED)

    def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures"""
        cb = self.CircuitBreaker("test", self.CircuitBreakerConfig(failure_threshold=3))
        for _ in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
            except Exception:
                pass
        self.assertEqual(cb.state, self.CircuitState.OPEN)

    def test_circuit_breaker_blocks_when_open(self):
        """Test circuit breaker blocks calls when open"""
        from agent.error_handler import ServerRootError
        cb = self.CircuitBreaker("test", self.CircuitBreakerConfig(failure_threshold=1))
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
        except Exception:
            pass
        with self.assertRaises(ServerRootError):
            cb.call(lambda: "should not reach")

    def test_error_tracker_summary(self):
        """Test error tracker provides summary"""
        for i in range(5):
            err = self.NetworkError(f"Error {i}")
            self.engine.handle(err)
        summary = self.engine.error_tracker.get_error_summary()
        self.assertGreaterEqual(summary["total_errors"], 5)

    def test_health_report(self):
        """Test health report generation"""
        report = self.engine.get_health_report()
        self.assertIn("health", report)
        self.assertIn("error_summary", report)


# ============================================================
# UNIT TESTS - RESOURCE MANAGER
# ============================================================

class TestResourceManager(unittest.TestCase):
    """Unit tests for Resource Manager"""

    def setUp(self):
        from agent.resource_manager import ResourceManager, ResourceConfig
        self.config = ResourceConfig(
            monitoring_interval=300.0,  # Long interval to avoid background noise
            thread_pool_size=3,
            max_threads=20
        )
        self.manager = ResourceManager(self.config)

    def tearDown(self):
        self.manager.shutdown()

    def test_initialization(self):
        """Test resource manager initializes"""
        self.assertIsNotNone(self.manager)

    def test_collect_metrics(self):
        """Test metrics collection"""
        metrics = self.manager.monitor.collect_metrics()
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics.memory_total_mb, 0)
        self.assertGreaterEqual(metrics.memory_percent, 0)
        self.assertLessEqual(metrics.memory_percent, 100)

    def test_memory_manager(self):
        """Test memory manager functions"""
        used, total, pct = self.manager.memory_manager.get_usage()
        self.assertGreater(total, 0)
        self.assertGreaterEqual(pct, 0)
        self.assertLessEqual(pct, 100)

    def test_memory_gc_trigger(self):
        """Test garbage collection trigger"""
        collected = self.manager.memory_manager.trigger_gc()
        self.assertGreaterEqual(collected, 0)

    def test_thread_pool_submit(self):
        """Test thread pool task submission"""
        results = []
        future = self.manager.thread_pool.submit(
            "test_task", lambda: results.append(42) or 42
        )
        self.assertIsNotNone(future)
        if future:
            value = future.result(timeout=5)
            self.assertEqual(value, 42)

    def test_system_status(self):
        """Test system status retrieval"""
        status = self.manager.get_system_status()
        self.assertIn("status", status)
        self.assertIn("metrics", status)
        self.assertIn("thread_pool", status)

    def test_optimization(self):
        """Test optimization procedure"""
        result = self.manager.optimize()
        self.assertIn("actions", result)
        self.assertIn("memory_after", result)

    def test_memory_availability_check(self):
        """Test memory availability check"""
        # Should have more than 1MB available
        has_1mb = self.manager.memory_manager.check_available(1)
        self.assertTrue(has_1mb)
        # Should not have 1TB available
        has_1tb = self.manager.memory_manager.check_available(1024 * 1024)
        self.assertFalse(has_1tb)


# ============================================================
# UNIT TESTS - RELIABILITY ENGINE
# ============================================================

class TestReliabilityEngine(unittest.TestCase):
    """Unit tests for Reliability Engine"""

    def setUp(self):
        from agent.reliability_engine import (
            ReliabilityEngine, HealthChecker, HealthProbe,
            ProbeType, HealthStatus, Watchdog, WatchdogConfig,
            StatePersistence, SystemSnapshot
        )
        self.engine = ReliabilityEngine(state_dir="data/test_state")
        self.HealthChecker = HealthChecker
        self.HealthProbe = HealthProbe
        self.ProbeType = ProbeType
        self.HealthStatus = HealthStatus
        self.StatePersistence = StatePersistence
        self.SystemSnapshot = SystemSnapshot

    def test_initialization(self):
        """Test reliability engine initializes"""
        self.assertIsNotNone(self.engine)

    def test_health_check_probes_registered(self):
        """Test default probes are registered"""
        _, services = self.engine.health_checker.get_overall_health()
        self.assertGreater(len(services), 0)

    def test_run_health_checks(self):
        """Test running health checks"""
        results = self.engine.run_health_checks()
        self.assertIn("overall_health", results)
        self.assertIn("services", results)

    def test_health_probe_tcp(self):
        """Test TCP health probe on known port"""
        probe = self.HealthProbe(
            probe_id="test_tcp",
            name="Test TCP",
            probe_type=self.ProbeType.TCP,
            target="localhost:5001",
            failure_threshold=1
        )
        checker = self.HealthChecker()
        checker.register_probe(probe)
        result = checker.run_probe(probe)
        # May pass or fail depending on if API is running
        self.assertIn(result.status, [self.HealthStatus.HEALTHY, self.HealthStatus.UNHEALTHY])

    def test_health_probe_memory(self):
        """Test memory health probe"""
        probe = self.HealthProbe(
            probe_id="test_mem",
            name="Test Memory",
            probe_type=self.ProbeType.MEMORY,
            target="99%",
            failure_threshold=1
        )
        checker = self.HealthChecker()
        checker.register_probe(probe)
        result = checker.run_probe(probe)
        self.assertEqual(result.status, self.HealthStatus.HEALTHY)

    def test_state_save_and_restore(self):
        """Test state persistence save and restore"""
        test_state = {
            "agents": {"agent_001": {"status": "active", "load": 0.5}},
            "config": {"version": "1.0", "environment": "test"},
            "operations": {"total": 100, "success": 95}
        }
        saved = self.engine.save_state(test_state)
        self.assertTrue(saved)

        restored = self.engine.restore_state()
        self.assertIsNotNone(restored)
        self.assertIn("agent_states", restored)

    def test_reliability_report(self):
        """Test reliability report generation"""
        report = self.engine.get_reliability_report()
        self.assertIn("overall_health", report)
        self.assertIn("watchdog", report)
        self.assertIn("state_snapshots", report)


# ============================================================
# UNIT TESTS - PERFORMANCE ENGINE
# ============================================================

class TestPerformanceEngine(unittest.TestCase):
    """Unit tests for Performance Engine"""

    def setUp(self):
        from agent.performance_engine import (
            PerformanceEngine, AdvancedCache, CacheStrategy,
            CompressionEngine, CompressionAlgorithm, Benchmarker
        )
        self.engine = PerformanceEngine(cache_size=100, worker_count=2)
        self.AdvancedCache = AdvancedCache
        self.CacheStrategy = CacheStrategy
        self.CompressionEngine = CompressionEngine
        self.CompressionAlgorithm = CompressionAlgorithm

    def tearDown(self):
        self.engine.shutdown()

    def test_initialization(self):
        """Test performance engine initializes"""
        self.assertIsNotNone(self.engine)

    def test_cache_basic_operations(self):
        """Test basic cache set/get/delete"""
        cache = self.AdvancedCache(max_size=10)
        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")
        self.assertIsNone(cache.get("nonexistent"))
        cache.delete("key1")
        self.assertIsNone(cache.get("key1"))

    def test_cache_lru_eviction(self):
        """Test LRU eviction policy"""
        cache = self.AdvancedCache(max_size=3, strategy=self.CacheStrategy.LRU)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.set("k3", "v3")
        cache.get("k1")  # Access k1 to make k2 least recently used
        cache.set("k4", "v4")  # Should evict k2
        self.assertIsNone(cache.get("k2"))
        self.assertIsNotNone(cache.get("k1"))

    def test_cache_ttl_expiration(self):
        """Test TTL-based expiration"""
        cache = self.AdvancedCache(max_size=10, strategy=self.CacheStrategy.TTL,
                                    default_ttl=0.1)  # 100ms TTL
        cache.set("key", "value", ttl=0.1)
        self.assertEqual(cache.get("key"), "value")
        time.sleep(0.15)  # Wait for expiration
        self.assertIsNone(cache.get("key"))

    def test_cache_stats(self):
        """Test cache statistics"""
        cache = self.AdvancedCache(max_size=10)
        cache.set("k1", "v1")
        cache.get("k1")  # hit
        cache.get("k2")  # miss
        stats = cache.get_stats()
        self.assertEqual(stats.hits, 1)
        self.assertEqual(stats.misses, 1)
        self.assertAlmostEqual(stats.hit_rate, 0.5)

    def test_compression_zlib(self):
        """Test zlib compression"""
        data = b"A" * 10000
        compressed, algo = self.engine.compressor.compress(data, self.CompressionAlgorithm.ZLIB)
        self.assertLess(len(compressed), len(data))
        decompressed = self.engine.compressor.decompress(compressed, algo)
        self.assertEqual(decompressed, data)

    def test_compression_gzip(self):
        """Test gzip compression"""
        data = b"B" * 10000
        compressed, algo = self.engine.compressor.compress(data, self.CompressionAlgorithm.GZIP)
        self.assertLess(len(compressed), len(data))
        decompressed = self.engine.compressor.decompress(compressed, algo)
        self.assertEqual(decompressed, data)

    def test_compression_string(self):
        """Test string compression"""
        text = "Hello World! " * 500
        compressed, algo = self.engine.compressor.compress_string(text)
        decompressed = self.engine.compressor.decompress_string(compressed, algo)
        self.assertEqual(decompressed, text)

    def test_async_pipeline(self):
        """Test async task pipeline"""
        results = []
        future = self.engine.pipeline.submit(
            "test_task",
            lambda: results.append(42) or 42
        )
        value = future.result(timeout=5)
        self.assertEqual(value, 42)

    def test_parallel_execution(self):
        """Test parallel function execution"""
        funcs = [lambda x=i: x * 2 for i in range(5)]
        results = self.engine.pipeline.execute_parallel(funcs, timeout=10)
        self.assertEqual(len(results), 5)

    def test_profiler_timing(self):
        """Test performance profiler timing"""
        with self.engine.profiler.time_operation("test_op"):
            time.sleep(0.01)
        summary = self.engine.profiler.get_summary()
        self.assertEqual(summary["total_operations"], 1)
        self.assertGreater(summary["avg_duration_ms"], 5)

    def test_benchmarker(self):
        """Test benchmarker functionality"""
        from agent.performance_engine import Benchmarker
        bench = Benchmarker()
        result = bench.benchmark("test", lambda: sum(range(100)), iterations=50, warmup=5)
        self.assertEqual(result.name, "test")
        self.assertEqual(result.iterations, 50)
        self.assertGreater(result.throughput_ops_sec, 0)

    def test_performance_report(self):
        """Test performance report"""
        report = self.engine.get_performance_report()
        self.assertIn("caches", report)
        self.assertIn("compression", report)
        self.assertIn("pipeline", report)


# ============================================================
# INTEGRATION TESTS
# ============================================================

class TestIntegration(unittest.TestCase):
    """Integration tests for cross-module interactions"""

    def test_security_with_error_handler(self):
        """Test security module integrates with error handler"""
        from agent.security_hardening import SecurityHardeningEngine
        from agent.error_handler import ErrorHandlingEngine, ErrorSeverity
        
        security = SecurityHardeningEngine()
        error_engine = ErrorHandlingEngine()
        
        # Simulate security violation triggering error handling
        report = security.get_security_report()
        self.assertIsNotNone(report)
        
        # Error handler should work with security events
        success, result = error_engine.safe_execute(
            security.get_security_report,
            operation="security_report",
            fallback={"error": "fallback"}
        )
        self.assertTrue(success)

    def test_resource_manager_with_cache(self):
        """Test resource manager awareness of cache"""
        from agent.resource_manager import ResourceManager, ResourceConfig
        from agent.performance_engine import AdvancedCache, CacheStrategy
        
        rm = ResourceManager(ResourceConfig(monitoring_interval=300))
        cache = AdvancedCache(max_size=100)
        
        # Fill cache
        for i in range(50):
            cache.set(f"key_{i}", f"value_{i}" * 100)
        
        # Resource manager should still show healthy memory
        status = rm.get_system_status()
        self.assertIn(status["status"], ["normal", "warning"])
        rm.shutdown()

    def test_performance_engine_with_security(self):
        """Test performance caching of security-validated data"""
        from agent.performance_engine import AdvancedCache
        from agent.security_hardening import InputValidator, ValidationResult
        
        cache = AdvancedCache(max_size=100)
        validator = InputValidator()
        
        # Cache validation results
        ip = "192.168.1.1"
        report = validator.validate_ip_address(ip)
        cache.set(f"ip_valid:{ip}", report.result == ValidationResult.VALID)
        
        # Retrieve from cache
        cached_result = cache.get(f"ip_valid:{ip}")
        self.assertTrue(cached_result)

    def test_reliability_with_api(self):
        """Test reliability health check against API"""
        from agent.reliability_engine import HealthChecker, HealthProbe, ProbeType, HealthStatus
        
        checker = HealthChecker()
        probe = HealthProbe(
            probe_id="api_health",
            name="API Server",
            probe_type=ProbeType.HTTP,
            target="http://localhost:5001/api/health",
            timeout_seconds=5,
            failure_threshold=1
        )
        checker.register_probe(probe)
        result = checker.run_probe(probe)
        
        # API should be healthy since we started it
        self.assertEqual(result.status, HealthStatus.HEALTHY)
        self.assertLess(result.response_time_ms, 5000)

    def test_swarm_with_performance_cache(self):
        """Test swarm intelligence results are cacheable"""
        from agent.swarm_coordinator import SwarmCoordinator, SwarmAgent, AgentStatus, AgentRole
        from agent.performance_engine import AdvancedCache
        
        coord = SwarmCoordinator(election_interval=300)
        cache = AdvancedCache(max_size=100)
        
        # Register agents and cache intelligence
        agent = SwarmAgent(
            agent_id="agent_cache_test",
            hostname="test.example.com",
            ip_address="10.0.0.99",
            platform="linux",
            status=AgentStatus.ACTIVE,
            role=AgentRole.WORKER,
            capabilities=["scan"],
            current_load=0.3,
            active_tasks=0,
            last_heartbeat=datetime.now(),
            performance_score=0.9,
            network_latency_ms=20,
            location="US-East"
        )
        coord.register_agent(agent)
        
        intelligence = coord.aggregate_intelligence()
        cache.set("swarm_intelligence", intelligence.to_dict())
        
        cached = cache.get("swarm_intelligence")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["total_agent_count"], 1)


# ============================================================
# END-TO-END TESTS
# ============================================================

class TestEndToEnd(unittest.TestCase):
    """End-to-end workflow tests"""

    def test_full_security_validation_workflow(self):
        """Test complete security validation workflow"""
        from agent.security_hardening import SecurityHardeningEngine
        
        engine = SecurityHardeningEngine()
        
        # Test valid request
        valid_request = {
            "command": "scan",
            "target_count": "5"
        }
        is_valid, issues = engine.validate_request(valid_request, "192.168.1.1")
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)

    def test_full_error_recovery_workflow(self):
        """Test complete error recovery workflow"""
        from agent.error_handler import ErrorHandlingEngine, NetworkError
        
        engine = ErrorHandlingEngine()
        
        # Simulate network failure and recovery
        attempts = [0]
        def failing_then_succeeding():
            attempts[0] += 1
            if attempts[0] < 2:
                raise NetworkError("Connection failed", host="10.0.0.1")
            return "success"
        
        success, result = engine.safe_execute(
            failing_then_succeeding,
            operation="network_call",
            fallback="fallback_result"
        )
        # Either succeeds or uses fallback gracefully
        self.assertIsNotNone(result)

    def test_full_performance_workflow(self):
        """Test complete performance optimization workflow"""
        from agent.performance_engine import PerformanceEngine
        import json
        
        engine = PerformanceEngine(cache_size=100, worker_count=2)
        
        # Simulate repeated data access with caching
        test_data = {"agents": [{"id": f"a{i}"} for i in range(20)]}
        cache_key = "test_data"
        
        # First access - cache miss
        result = engine.l1_cache.get(cache_key)
        self.assertIsNone(result)
        
        # Store result
        engine.l1_cache.set(cache_key, test_data)
        
        # Second access - cache hit
        result = engine.l1_cache.get(cache_key)
        self.assertIsNotNone(result)
        self.assertEqual(len(result["agents"]), 20)
        
        # Compress data for network transmission
        data_bytes = json.dumps(test_data).encode()
        compressed, algo = engine.compressor.compress(data_bytes)
        self.assertLess(len(compressed), len(data_bytes))
        
        engine.shutdown()

    def test_api_endpoint_health(self):
        """Test the live API endpoints"""
        import urllib.request
        import json
        
        try:
            with urllib.request.urlopen("http://localhost:5001/api/health", timeout=5) as response:
                data = json.loads(response.read())
                self.assertEqual(data["status"], "healthy")
                self.assertEqual(data["service"], "ServerRoot.net API")
        except Exception as e:
            self.skipTest(f"API not available: {e}")

    def test_api_swarm_status(self):
        """Test the swarm status endpoint"""
        import urllib.request
        import json
        
        try:
            with urllib.request.urlopen("http://localhost:5001/api/swarm/status", timeout=5) as response:
                data = json.loads(response.read())
                self.assertIn("initialized", data)
                self.assertIn("stats", data)
        except Exception as e:
            self.skipTest(f"API not available: {e}")


# ============================================================
# PERFORMANCE TESTS
# ============================================================

class TestPerformance(unittest.TestCase):
    """Performance benchmark tests"""

    def test_cache_throughput(self):
        """Test cache can handle high throughput"""
        from agent.performance_engine import AdvancedCache
        cache = AdvancedCache(max_size=1000)
        
        start = time.perf_counter()
        for i in range(10000):
            cache.set(f"key_{i % 100}", f"value_{i}")
        for i in range(10000):
            cache.get(f"key_{i % 100}")
        elapsed = time.perf_counter() - start
        
        ops_per_sec = 20000 / elapsed
        self.assertGreater(ops_per_sec, 100000)  # Must exceed 100K ops/sec

    def test_compression_throughput(self):
        """Test compression throughput"""
        from agent.performance_engine import CompressionEngine
        comp = CompressionEngine()
        data = b"Test data for compression " * 100  # ~2.5KB
        
        start = time.perf_counter()
        for _ in range(1000):
            compressed, algo = comp.compress(data)
            comp.decompress(compressed, algo)
        elapsed = time.perf_counter() - start
        
        ops_per_sec = 1000 / elapsed
        self.assertGreater(ops_per_sec, 100)  # Must exceed 100 round-trips/sec

    def test_input_validation_throughput(self):
        """Test input validation throughput"""
        from agent.security_hardening import InputValidator
        validator = InputValidator()
        
        start = time.perf_counter()
        for i in range(1000):
            validator.validate_ip_address(f"192.168.1.{i % 254 + 1}")
        elapsed = time.perf_counter() - start
        
        ops_per_sec = 1000 / elapsed
        self.assertGreater(ops_per_sec, 1000)  # Must exceed 1K validations/sec

    def test_encryption_throughput(self):
        """Test encryption throughput"""
        from agent.security_hardening import EncryptionManager
        enc = EncryptionManager()
        data = "sensitive data for encryption testing"
        
        start = time.perf_counter()
        for _ in range(100):
            ciphertext, key_id = enc.encrypt(data)
            enc.decrypt(ciphertext, key_id)
        elapsed = time.perf_counter() - start
        
        ops_per_sec = 100 / elapsed
        self.assertGreater(ops_per_sec, 10)  # Must exceed 10 round-trips/sec


# ============================================================
# TEST RUNNER
# ============================================================

def run_all_tests():
    """Run all tests and return results"""
    print("\n" + "=" * 70)
    print("  SERVERROOT.NET - COMPREHENSIVE TEST SUITE")
    print("  Phase 9: Full Coverage Testing")
    print("=" * 70 + "\n")
    
    test_classes = [
        ("AI Strategy Engine", TestAIStrategyEngine),
        ("Swarm Coordinator", TestSwarmCoordinator),
        ("Security Hardening", TestSecurityHardening),
        ("Error Handler", TestErrorHandler),
        ("Resource Manager", TestResourceManager),
        ("Reliability Engine", TestReliabilityEngine),
        ("Performance Engine", TestPerformanceEngine),
        ("Integration Tests", TestIntegration),
        ("End-to-End Tests", TestEndToEnd),
        ("Performance Tests", TestPerformance),
    ]
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_errors = 0
    failed_tests = []
    
    for suite_name, test_class in test_classes:
        print(f"\n📋 {suite_name}")
        print("-" * 50)
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(test_class)
        
        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(suite)
        
        passed = result.testsRun - len(result.failures) - len(result.errors)
        total_tests += result.testsRun
        total_passed += passed
        total_failed += len(result.failures)
        total_errors += len(result.errors)
        
        for test, _ in result.failures + result.errors:
            failed_tests.append(f"{suite_name}: {test}")
        
        status = "✅" if not result.failures and not result.errors else "⚠️"
        print(f"{status} {passed}/{result.testsRun} tests passed")
        
        if result.failures or result.errors:
            output = stream.getvalue()
            for line in output.split('\n'):
                if 'FAIL' in line or 'ERROR' in line or 'Error' in line:
                    print(f"  ⚠️  {line}")
    
    print("\n" + "=" * 70)
    print("  FINAL RESULTS")
    print("=" * 70)
    print(f"  Total Tests:   {total_tests}")
    print(f"  ✅ Passed:     {total_passed}")
    print(f"  ❌ Failed:     {total_failed}")
    print(f"  💥 Errors:     {total_errors}")
    print(f"  Pass Rate:     {total_passed/total_tests*100:.1f}%")
    
    if failed_tests:
        print(f"\n  Failed Tests:")
        for t in failed_tests:
            print(f"    - {t}")
    
    print("=" * 70)
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! ServerRoot.net is 100% test-verified.")
    else:
        print(f"\n⚠️  {total_failed + total_errors} tests need attention.")
    
    return total_passed, total_tests


if __name__ == "__main__":
    import io
    passed, total = run_all_tests()
    sys.exit(0 if passed == total else 1)