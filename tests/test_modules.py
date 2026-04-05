#!/usr/bin/env python3
"""
ServerRoot.net - Phase 9 Comprehensive Test Suite
All APIs verified against actual implementation. No hangs.
"""
import sys, os, time, datetime, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── Framework ────────────────────────────────────────────────────────────────
passed = failed = errors = 0
failures = []
start_time = time.time()

def test(name, func):
    global passed, failed, errors
    try:
        r = func()
        if r is False:
            failed += 1; failures.append((name, "Returned False"))
            print(f"  ✗ {name}: Returned False")
        else:
            passed += 1; print(f"  ✓ {name}")
    except AssertionError as e:
        failed += 1; failures.append((name, str(e)))
        print(f"  ✗ {name}: Assert: {e}")
    except Exception as e:
        errors += 1; failures.append((name, f"{type(e).__name__}: {e}"))
        print(f"  ✗ {name}: {type(e).__name__}: {e}")

def section(t): print(f"\n{'═'*60}\n  {t}\n{'═'*60}")
def sub(t):     print(f"\n  ── {t}")

# ═══════════════════════════════════════════════════════════
# 1. SECURITY HARDENING
# ═══════════════════════════════════════════════════════════
section("1. SECURITY HARDENING")
from agent.security_hardening import (
    InputValidator, EncryptionManager, RateLimiter,
    SecretsManager, AuditLogger, ValidationResult, AuditEventType
)
v = InputValidator()
enc = EncryptionManager()

sub("Input Validation")
test("Valid IPv4",            lambda: v.validate_ip_address("192.168.1.1").result == ValidationResult.VALID)
test("Valid IPv4 class B",     lambda: v.validate_ip_address("172.16.0.1").result == ValidationResult.VALID)
test("Invalid IP (999.x)",   lambda: v.validate_ip_address("999.1.1.1").result != ValidationResult.VALID)
test("Empty IP fails",        lambda: v.validate_ip_address("").result != ValidationResult.VALID)
test("Valid hostname",        lambda: v.validate_hostname("example.com").result == ValidationResult.VALID)
test("Cmd inject (;) blocked",  lambda: v.validate_command("scan; rm -rf /").result == ValidationResult.BLOCKED)
test("Cmd inject (|) blocked",  lambda: v.validate_command("scan | cat /etc/passwd").result == ValidationResult.BLOCKED)
test("Cmd inject (`) blocked",  lambda: v.validate_command("`whoami`").result == ValidationResult.BLOCKED)
test("Valid command passes",    lambda: v.validate_command("scan_network").result == ValidationResult.VALID)
test("Valid agent_id passes",   lambda: v.validate_agent_id("agent_ab123456").result == ValidationResult.VALID)
test("Invalid agent_id fails",  lambda: v.validate_agent_id("bad!agent@#$").result != ValidationResult.VALID)
test("SQL injection detected",  lambda: v._check_injection("'; DROP TABLE agents; --") is not None)
# XSS returns 'command_injection' (any non-None is a detection)
test("XSS detected",            lambda: v._check_injection("<script>alert(1)</script>") is not None)
test("Path traversal detected", lambda: v._check_injection("../../etc/passwd") is not None)
test("Clean string passes",     lambda: v._check_injection("normal_input_123") is None)

sub("Encryption")
test("AES encrypt/decrypt",       lambda: enc.decrypt(*enc.encrypt("secret data")).decode() == "secret data")
test("Encrypt bytes",             lambda: enc.decrypt(*enc.encrypt(b"bytes data")).decode() == "bytes data")
test("Encrypt empty string",      lambda: enc.decrypt(*enc.encrypt("")).decode() == "")
test("Unique ciphertexts per encrypt", lambda: enc.encrypt("same")[0] != enc.encrypt("same")[0])
test("PW hash + verify (OK)",     lambda: enc.verify_password("TestPass!", *enc.hash_password("TestPass!")))
test("PW hash + verify (wrong)",  lambda: not enc.verify_password("Wrong", *enc.hash_password("TestPass!")))
test("HMAC sign + verify",        lambda: enc.verify_signature(b"data", enc.sign_data(b"data")))
test("HMAC tamper detection",     lambda: not enc.verify_signature(b"tampered", enc.sign_data(b"original")))
test("Token ≥ 32 chars",          lambda: len(enc.generate_token()) >= 32)
test("Tokens are unique",         lambda: enc.generate_token() != enc.generate_token())

sub("Rate Limiting")
lim = RateLimiter(max_requests=5, window_seconds=60)
test("Allows initial request",    lambda: lim.is_allowed(f"ip_{time.time()}")[0] == True)

def _rate_block():
    ip = f"blk_{time.time()}"
    for _ in range(5): lim.is_allowed(ip)
    return lim.is_allowed(ip)[0] == False
test("Blocks after threshold",    _rate_block)

sub("Secrets Manager")
sec = SecretsManager(enc)
test("Store + retrieve",       lambda: (sec.store_secret("db_pass","S3cr3t!") or True) and sec.get_secret("db_pass") == "S3cr3t!")
test("Missing → None",         lambda: sec.get_secret("no_such_key_xyz") is None)
test("Overwrite works",        lambda: (sec.store_secret("k","v1") or True) and (sec.store_secret("k","v2") or True) and sec.get_secret("k") == "v2")

sub("Audit Logger")
# AuditLogger.log(event_type, actor, target, action, result, metadata=None, ip_address=None)
audit = AuditLogger()
test("log() executes",       lambda: audit.log(AuditEventType.AUTH_SUCCESS,"tester","system","login","success") is not None)
test("get_events() is list", lambda: isinstance(audit.get_events(), list))
test("Event retrievable",    lambda: len(audit.get_events()) > 0)

# ═══════════════════════════════════════════════════════════
# 2. ERROR HANDLING
# ═══════════════════════════════════════════════════════════
section("2. ERROR HANDLING")
from agent.error_handler import (
    ServerRootError, NetworkError, AgentError, ExploitError,
    ConfigurationError, AuthenticationError, ResourceError,
    SwarmError, StealthError, C2Error,
    CircuitBreaker, CircuitBreakerConfig, CircuitState,
    ErrorHandlingEngine, ErrorTracker
)

sub("Exception Hierarchy")
for cls in [NetworkError, AgentError, ExploitError, ConfigurationError,
            AuthenticationError, ResourceError, SwarmError, StealthError, C2Error]:
    test(f"{cls.__name__} is ServerRootError", lambda c=cls: issubclass(c, ServerRootError))

def _net_raise():
    try: raise NetworkError("conn refused")
    except ServerRootError as e: return "conn refused" in str(e)
    return False
test("NetworkError caught as ServerRootError", _net_raise)

def _agent_raise():
    try: raise AgentError("agent_001", "offline")
    except AgentError: return True
    return False
test("AgentError with agent_id", _agent_raise)

sub("Circuit Breaker — uses call(func) to track failures")
# State via .state property (not ._state directly, but both work)
test("Starts CLOSED",        lambda: CircuitBreaker("s")._state == CircuitState.CLOSED)
test("State property works", lambda: CircuitBreaker("s").state == CircuitState.CLOSED)

def _cb_open():
    # Trigger failures via cb.call() with a failing function
    cb = CircuitBreaker("s", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=999))
    def bad(): raise ValueError("fail")
    for _ in range(3):
        try: cb.call(bad)
        except: pass
    return cb.state == CircuitState.OPEN
test("Opens after 3 call() failures", _cb_open)

def _cb_blocks():
    cb = CircuitBreaker("s", CircuitBreakerConfig(failure_threshold=2, recovery_timeout=999))
    def bad(): raise ValueError("fail")
    for _ in range(2):
        try: cb.call(bad)
        except: pass
    # Now circuit is OPEN - next call should raise ServerRootError
    try:
        cb.call(lambda: "ok")
        return False  # Should have raised
    except ServerRootError:
        return True
    except Exception:
        return False
test("OPEN circuit raises ServerRootError", _cb_blocks)

def _cb_allows_ok():
    cb = CircuitBreaker("s")
    result = cb.call(lambda: 42)
    return result == 42
test("CLOSED circuit allows and returns result", _cb_allows_ok)

sub("Error Tracker")
def _tracker():
    # Methods: record(exception, severity, context), get_error_summary()
    t = ErrorTracker()
    try: raise NetworkError("err")
    except Exception as e: t.record(e, context={"op": "test"})
    s = t.get_error_summary()
    return isinstance(s, dict) and s.get("total_errors", 0) >= 1
test("ErrorTracker record + get_error_summary()", _tracker)

sub("ErrorHandlingEngine — safe_execute → (success, result)")
def _safe_ok():
    s, r = ErrorHandlingEngine().safe_execute(lambda: 42, fallback=0)
    return s == True and r == 42
test("safe_execute success → (True, 42)", _safe_ok)

def _safe_fb():
    s, r = ErrorHandlingEngine().safe_execute(lambda: 1/0, fallback="fb")
    return s == False and r == "fb"
test("safe_execute exception → (False, fallback)", _safe_fb)

test("get_health_report() is dict", lambda: isinstance(ErrorHandlingEngine().get_health_report(), dict))

# ═══════════════════════════════════════════════════════════
# 3. PERFORMANCE ENGINE
# ═══════════════════════════════════════════════════════════
section("3. PERFORMANCE ENGINE")
from agent.performance_engine import (
    AdvancedCache, CompressionEngine, CompressionAlgorithm,
    PerformanceEngine, Benchmarker, PerformanceProfiler
)

sub("AdvancedCache")
test("set/get basic",    lambda: (lambda c: c.set("k","v") or c.get("k") == "v")(AdvancedCache(100)))
test("miss → None",      lambda: AdvancedCache(100).get("nope") is None)

def _overwrite():
    c = AdvancedCache(100); c.set("k","v1"); c.set("k","v2"); return c.get("k") == "v2"
test("Overwrite works", _overwrite)

def _ttl():
    c = AdvancedCache(100, default_ttl=0.05); c.set("k","v"); time.sleep(0.1); return c.get("k") is None
test("TTL expiry", _ttl)

def _lru():
    c = AdvancedCache(3)
    for i in range(4): c.set(str(i), i)
    return len(c._cache) <= 3
test("LRU eviction bounds size", _lru)

def _stats():
    c = AdvancedCache(100); c.set("x",1); c.get("x"); c.get("y")
    s = c.get_stats()
    # Returns CacheStats dataclass with .hits attribute
    return hasattr(s, "hits") and s.hits >= 1
test("Stats: hits/misses tracked", _stats)

def _throughput():
    c = AdvancedCache(10000); n = 50000; t0 = time.time()
    for i in range(n): c.set(f"k{i}",i); c.get(f"k{i}")
    ops = n*2/(time.time()-t0)
    print(f"      Cache: {ops:,.0f} ops/sec")
    return ops > 100000
test("Throughput > 100K ops/sec", _throughput)

def _manual_cache():
    # AdvancedCache has no @cached decorator - test manual memoization pattern
    c = AdvancedCache(100); calls = [0]
    def fn(x):
        cached = c.get(f"fn_{x}")
        if cached is not None: return cached
        calls[0] += 1
        result = x * 2
        c.set(f"fn_{x}", result)
        return result
    fn(5); fn(5)  # second call hits cache
    return calls[0] == 1
test("Manual cache memoization avoids double-call", _manual_cache)

sub("CompressionEngine")
def _zlib():
    comp = CompressionEngine(); d = b"hello "*100
    c, a = comp.compress(d, CompressionAlgorithm.ZLIB)
    return comp.decompress(c, a) == d
test("ZLIB roundtrip", _zlib)

def _gzip():
    comp = CompressionEngine(); d = b"fox jumped "*50
    c, a = comp.compress(d, CompressionAlgorithm.GZIP)
    return comp.decompress(c, a) == d
test("GZIP roundtrip", _gzip)

def _ratio():
    comp = CompressionEngine(); d = b"A"*10000
    c, a = comp.compress(d, CompressionAlgorithm.ZLIB)
    ratio = len(c)/len(d)
    print(f"      Compression: {(1-ratio)*100:.1f}% reduction")
    return ratio < 0.05
test(">95% compression on repetitive data", _ratio)

def _small():
    comp = CompressionEngine(); d = b"hi"
    c, a = comp.compress(d); return comp.decompress(c, a) == d
test("Handles small data", _small)

def _comp_tp():
    comp = CompressionEngine(); d = b"benchmark "*100; n = 500; t0 = time.time()
    for _ in range(n):
        c, a = comp.compress(d); comp.decompress(c, a)
    ops = n/(time.time()-t0)
    print(f"      Compression: {ops:,.0f} ops/sec")
    return ops > 200
test("Compression throughput > 200 ops/sec", _comp_tp)

sub("PerformanceEngine (l1_cache, l2_cache, result_cache)")
def _pe_l1():
    pe = PerformanceEngine()
    pe.l1_cache.set("k", {"v":1})
    return pe.l1_cache.get("k") == {"v":1}
test("L1 cache store/retrieve", _pe_l1)

def _pe_l2():
    pe = PerformanceEngine()
    pe.l2_cache.set("k", [1,2,3])
    return pe.l2_cache.get("k") == [1,2,3]
test("L2 cache store/retrieve", _pe_l2)

def _pe_result_cache():
    pe = PerformanceEngine()
    pe.result_cache.set("result_key", 42)
    return pe.result_cache.get("result_key") == 42
test("Result cache store/retrieve", _pe_result_cache)

def _pe_report():
    pe = PerformanceEngine()
    r = pe.get_performance_report()
    return isinstance(r, dict)
test("get_performance_report() returns dict", _pe_report)

sub("Benchmarker — result.throughput_ops_sec")
def _bench():
    r = Benchmarker().benchmark("t", lambda: sum(range(100)), iterations=100)
    # BenchmarkResult has throughput_ops_sec (not ops_per_second)
    return hasattr(r, "throughput_ops_sec") and r.throughput_ops_sec > 0
test("benchmark() result.throughput_ops_sec > 0", _bench)

sub("PerformanceProfiler — time_operation() + get_summary()")
def _profiler():
    prof = PerformanceProfiler()
    with prof.time_operation("test_block"):
        x = sum(range(1000))
    s = prof.get_summary()
    return isinstance(s, dict) and "total_operations" in s
test("time_operation() + get_summary()", _profiler)

def _profiler_slowest():
    prof = PerformanceProfiler()
    with prof.time_operation("op_a"): time.sleep(0.01)
    with prof.time_operation("op_b"): time.sleep(0.02)
    slowest = prof.get_slowest_operations(limit=1)
    return len(slowest) == 1
test("get_slowest_operations(1) returns 1 result", _profiler_slowest)

# ═══════════════════════════════════════════════════════════
# 4. RESOURCE MANAGER
# ═══════════════════════════════════════════════════════════
section("4. RESOURCE MANAGER")
from agent.resource_manager import (
    ResourceConfig, ResourceMonitor, MemoryManager,
    ThreadPoolManager, ConnectionPoolManager
)

sub("ResourceConfig — fields: memory_warning_pct, max_threads, etc.")
test("Valid defaults",    lambda: ResourceConfig().memory_warning_pct > 0 and ResourceConfig().max_threads > 0)
test("Custom max_threads", lambda: ResourceConfig(max_threads=20).max_threads == 20)

sub("ResourceMonitor (no background thread)")
def _collect():
    m = ResourceMonitor(ResourceConfig()).collect_metrics()
    return 0 <= m.cpu_percent <= 100 and 0 <= m.memory_percent <= 100
test("collect_metrics(): CPU+mem in [0,100]", _collect)

def _latest():
    mon = ResourceMonitor(ResourceConfig()); mon.collect_metrics()
    return mon.get_latest_metrics() is not None
test("get_latest_metrics() after collect", _latest)

def _trends():
    mon = ResourceMonitor(ResourceConfig())
    for _ in range(3): mon.collect_metrics()
    trends = mon.get_resource_trends()
    return isinstance(trends, dict)
test("get_resource_trends() after 3 collects", _trends)

sub("MemoryManager")
def _mem_usage():
    # get_usage returns (used_mb, total_mb, pct) tuple
    mm = MemoryManager(ResourceConfig())
    usage = mm.get_usage()
    return usage is not None
test("get_usage() returns data", _mem_usage)

test("check_available(100) is bool", lambda: isinstance(MemoryManager(ResourceConfig()).check_available(100), bool))

def _process_mem():
    return MemoryManager(ResourceConfig()).get_process_memory() > 0
test("get_process_memory() > 0", _process_mem)

sub("ThreadPoolManager — submit(task_id, func)")
def _tp():
    tp = ThreadPoolManager(ResourceConfig())
    f = tp.submit("t1", lambda: 42)
    if f is None: return False  # Thread limit reached
    r = f.result(timeout=5); tp.shutdown(wait=False)
    return r == 42
test("submit('task_id', fn) → result=42", _tp)

def _tp_stats():
    tp = ThreadPoolManager(ResourceConfig())
    s = tp.get_stats(); tp.shutdown(wait=False)
    return isinstance(s, dict)
test("get_stats() returns dict", _tp_stats)

sub("ConnectionPoolManager")
def _conn():
    cp = ConnectionPoolManager(ResourceConfig())
    cid = cp.register_connection("host1", 8080)
    return isinstance(cid, str) and len(cid) > 0
test("register_connection() returns ID", _conn)

def _conn_rel():
    cp = ConnectionPoolManager(ResourceConfig())
    cid = cp.register_connection("host2", 9090)
    cp.use_connection(cid)
    cp.release_connection(cid)
    return True
test("use + release_connection() no error", _conn_rel)

def _conn_stats():
    cp = ConnectionPoolManager(ResourceConfig())
    s = cp.get_stats()
    return isinstance(s, dict)
test("get_stats() returns dict", _conn_stats)

# ═══════════════════════════════════════════════════════════
# 5. RELIABILITY ENGINE
# ═══════════════════════════════════════════════════════════
section("5. RELIABILITY ENGINE")
from agent.reliability_engine import (
    ReliabilityEngine, HealthChecker, HealthProbe, ProbeType,
    Watchdog, WatchdogConfig, StatePersistence, HealthStatus,
    SystemSnapshot
)

sub("HealthProbe — (probe_id, name, probe_type, target, ..., custom_check)")
def _probe():
    p = HealthProbe("p1","test",ProbeType.CUSTOM,"localhost",
                    custom_check=lambda: (True,"OK"))
    return p.name == "test" and p.probe_type == ProbeType.CUSTOM
test("HealthProbe creation", _probe)

def _probe_reg():
    hc = HealthChecker()
    p = HealthProbe("p2","mem",ProbeType.MEMORY,"system",
                    custom_check=lambda: (True,"OK"))
    hc.register_probe(p)
    return "p2" in hc._probes
test("register_probe() stores probe", _probe_reg)

def _probe_run():
    hc = HealthChecker()
    p = HealthProbe("p3","healthy",ProbeType.CUSTOM,"localhost",
                    custom_check=lambda: (True,"OK"))
    hc.register_probe(p)
    r = hc.run_probe(p)
    return r is not None
test("run_probe() returns HealthCheckResult", _probe_run)

def _check_all():
    hc = HealthChecker()
    p = HealthProbe("p4","cp",ProbeType.CUSTOM,"localhost",
                    custom_check=lambda: (True,"OK"))
    hc.register_probe(p)
    return isinstance(hc.check_all(), dict)
test("check_all() returns dict", _check_all)

def _overall():
    hc = HealthChecker()
    r = hc.get_overall_health()
    status = r[0] if isinstance(r, tuple) else r
    return status is not None
test("get_overall_health() returns status", _overall)

sub("Watchdog — watch(name, check_func, restart_func=None)")
def _wd_reg():
    wd = Watchdog(); wd.watch("c", lambda: True, lambda: None)
    return "c" in wd._watched
test("watch() registers component", _wd_reg)

def _wd_healthy():
    wd = Watchdog(); restarted = [False]
    wd.watch("svc", lambda: True, lambda: restarted.__setitem__(0, True))
    alive, _ = wd.check_component("svc")
    return alive == True and restarted[0] == False
test("Healthy component: alive=True, no restart", _wd_healthy)

def _wd_fails():
    wd = Watchdog()
    wd.watch("sick", lambda: False)
    alive, _ = wd.check_component("sick")
    return alive == False
test("Unhealthy component: alive=False", _wd_fails)

def _wd_restart():
    # attempt_restart with zero delay
    cfg = WatchdogConfig(restart_delay=0.0)
    wd = Watchdog(cfg); restarted = [False]
    wd.watch("svc2", lambda: False, lambda: restarted.__setitem__(0, True))
    result = wd.attempt_restart("svc2")
    return result == True and restarted[0] == True
test("attempt_restart() calls restart_func", _wd_restart)

sub("StatePersistence")
def _save():
    import datetime
    sp = StatePersistence("data/test_state")
    snap = SystemSnapshot(
        snapshot_id="snap1",
        timestamp=datetime.datetime.now(),
        agent_states={"v": "1.0"},
        config_state={"n": 5},
        operation_state={}
    )
    sp.save_snapshot(snap)
    loaded = sp.load_snapshot("snap1")
    return isinstance(loaded, dict) and loaded["agent_states"] == {"v": "1.0"}
test("save + load snapshot", _save)

def _list():
    import datetime
    sp = StatePersistence("data/test_state")
    snap = SystemSnapshot(
        snapshot_id="snap2",
        timestamp=datetime.datetime.now(),
        agent_states={"x": 1},
        config_state={},
        operation_state={}
    )
    sp.save_snapshot(snap)
    return isinstance(sp.list_snapshots(), list) and len(sp.list_snapshots()) > 0
test("list_snapshots() returns non-empty list", _list)

test("Missing snapshot → None", lambda: StatePersistence("data/test_state").load_snapshot("missing_xyz_999") is None)

sub("ReliabilityEngine")
def _re():
    re = ReliabilityEngine(state_dir="data/test_re")
    return all(hasattr(re, a) for a in ["health_checker","watchdog","state_persistence"])
test("Init: all 3 components present", _re)

# ═══════════════════════════════════════════════════════════
# 6. SWARM COORDINATOR
# ═══════════════════════════════════════════════════════════
section("6. SWARM COORDINATOR")
from agent.swarm_coordinator import (
    SwarmCoordinator, SwarmAgent, AgentRole, AgentStatus,
    LoadBalanceStrategy, TaskPriority, DistributedTask
)
from datetime import datetime as dt

def _agent(aid, role=AgentRole.WORKER, load=0.3, plat="linux"):
    return SwarmAgent(
        agent_id=aid, hostname=f"host-{aid[:8]}",
        ip_address=f"10.0.0.{abs(hash(aid))%254+1}", platform=plat,
        status=AgentStatus.ACTIVE, role=role,
        capabilities=["scan","exploit"], current_load=load, active_tasks=0,
        last_heartbeat=dt.now(), performance_score=0.8,
        network_latency_ms=10.0, location="us-east"
    )

def _task(tid=None, caps=None):
    return DistributedTask(
        task_id=tid or str(uuid.uuid4()), task_type="scan",
        priority=TaskPriority.HIGH, target_id="192.168.1.1",
        payload={}, required_capabilities=caps or ["scan"],
        created_at=dt.now(), deadline=None, status="pending"
    )

sub("Init & Registration")
test("init: agents is dict",       lambda: isinstance(SwarmCoordinator().agents, dict))

def _reg():
    sc = SwarmCoordinator(); sc.register_agent(_agent("a1"))
    return "a1" in sc.agents
test("register_agent() stores agent", _reg)

def _reg5():
    sc = SwarmCoordinator()
    for i in range(5): sc.register_agent(_agent(f"r{i}"))
    return len(sc.agents) == 5
test("Register 5 agents", _reg5)

def _auto():
    sc = SwarmCoordinator(); sc.register_agent(_agent("first"))
    return sc.leader_id == "first"
test("Auto-election on first registration", _auto)

def _multi_plat():
    sc = SwarmCoordinator()
    for p in ["linux","windows","router","macos"]:
        sc.register_agent(_agent(f"a_{p}", plat=p))
    return len(sc.agents) == 4
test("Register 4 platforms", _multi_plat)

sub("Leader Election")
def _elect():
    sc = SwarmCoordinator()
    for i in range(3): sc.register_agent(_agent(f"el{i}"))
    sc.elect_leader()
    return sc.leader_id in sc.agents
test("elect_leader() assigns valid leader", _elect)

sub("Load Balancing")
def _strategies():
    sc = SwarmCoordinator()
    for i in range(3): sc.register_agent(_agent(f"lb{i}"))
    for s in LoadBalanceStrategy: sc.set_balance_strategy(s)
    return True
test("All 5 LoadBalanceStrategy values settable", _strategies)

def _least_loaded():
    sc = SwarmCoordinator()
    sc.register_agent(_agent("heavy", load=0.9))
    sc.register_agent(_agent("light", load=0.1))
    sc.set_balance_strategy(LoadBalanceStrategy.LEAST_LOADED)
    return sc.assign_task(_task()) == "light"
test("LEAST_LOADED picks lightest agent", _least_loaded)

sub("Task Assignment")
def _assign():
    sc = SwarmCoordinator(); sc.register_agent(_agent("ta"))
    return sc.assign_task(_task()) == "ta"
test("assign_task() → correct agent", _assign)

def _tracked():
    sc = SwarmCoordinator(); sc.register_agent(_agent("tr"))
    t = _task("task_track_001")
    sc.assign_task(t)
    return "task_track_001" in sc.tasks
test("Task tracked in sc.tasks", _tracked)

sub("Intelligence & Coordination")
def _intel():
    sc = SwarmCoordinator()
    for i in range(3): sc.register_agent(_agent(f"i{i}"))
    return sc.aggregate_intelligence() is not None
test("aggregate_intelligence() returns data", _intel)

def _load_sum():
    sc = SwarmCoordinator()
    sc.register_agent(_agent("s1", load=0.3)); sc.register_agent(_agent("s2", load=0.7))
    s = sc.get_load_summary()
    return isinstance(s, dict) and "total_agents" in s and "average_load" in s
test("get_load_summary() has expected keys", _load_sum)

def _path():
    sc = SwarmCoordinator()
    sc.register_agent(_agent("src")); sc.register_agent(_agent("dst"))
    return sc.establish_command_path("src","dst") is not None
test("establish_command_path() creates path", _path)

def _attack():
    sc = SwarmCoordinator(); sc.register_agent(_agent("atk"))
    aid = sc.create_distributed_attack("exploit","10.0.0.5",{"m":"bf"},TaskPriority.HIGH)
    return isinstance(aid, str) and len(aid) > 0
test("create_distributed_attack() returns task ID", _attack)

def _attack_sum():
    sc = SwarmCoordinator(); sc.register_agent(_agent("as"))
    sc.create_distributed_attack("scan","10.0.0.1",{},TaskPriority.MEDIUM)
    return isinstance(sc.get_attack_summary(), dict)
test("get_attack_summary() returns dict", _attack_sum)

def _path_sum():
    sc = SwarmCoordinator()
    sc.register_agent(_agent("ps")); sc.register_agent(_agent("pd"))
    sc.establish_command_path("ps","pd")
    return isinstance(sc.get_path_summary(), dict)
test("get_path_summary() returns dict", _path_sum)

# ═══════════════════════════════════════════════════════════
# 7. INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════
section("7. INTEGRATION TESTS")

sub("Security + Error Handler")
def _sec_err():
    from agent.security_hardening import InputValidator, ValidationResult
    from agent.error_handler import ErrorHandlingEngine, AuthenticationError
    v2 = InputValidator(); eng = ErrorHandlingEngine()
    def fn(ip):
        r = v2.validate_ip_address(ip)
        if r.result != ValidationResult.VALID: raise AuthenticationError("bad ip")
        return True
    s, r = eng.safe_execute(lambda: fn("999.9.9.9"), fallback="blocked")
    return s == False and r == "blocked"
test("Security validate → AuthError → safe_execute fallback", _sec_err)

sub("Cache + Compression")
def _cache_comp():
    c = AdvancedCache(100); comp = CompressionEngine()
    d = b"payload "*500
    compressed, algo = comp.compress(d)
    c.set("blob", (compressed, algo.value))
    cb, av = c.get("blob")
    return comp.decompress(cb, CompressionAlgorithm(av)) == d
test("Compress → cache → retrieve → decompress", _cache_comp)

sub("Swarm + Performance Cache")
def _swarm_cache():
    sc = SwarmCoordinator(); cache = AdvancedCache(1000)
    for i in range(8):
        a = _agent(f"sp{i}", load=i*0.05)
        sc.register_agent(a)
        cache.set(f"agent_{i}", {"load": a.current_load})
    s = sc.get_load_summary()
    cache.set("summary", s)
    return sc.leader_id is not None and cache.get("summary") == s and len(sc.agents) == 8
test("Swarm 8 agents + cache summary", _swarm_cache)

sub("Reliability + State Persistence")
def _rel_persist():
    import datetime
    sp = StatePersistence("data/test_state")
    sc = SwarmCoordinator()
    for i in range(3): sc.register_agent(_agent(f"rp{i}"))
    snap = SystemSnapshot(
        snapshot_id="swarm_persist",
        timestamp=datetime.datetime.now(),
        agent_states={"leader": sc.leader_id, "count": len(sc.agents)},
        config_state={},
        operation_state={}
    )
    sp.save_snapshot(snap)
    r = sp.load_snapshot("swarm_persist")
    return r["agent_states"]["leader"] == sc.leader_id and r["agent_states"]["count"] == 3
test("Persist swarm state → restore", _rel_persist)

sub("Full Stack")
def _full_stack():
    from agent.security_hardening import InputValidator, EncryptionManager, ValidationResult
    from agent.error_handler import ErrorHandlingEngine
    v2 = InputValidator(); enc2 = EncryptionManager()
    cache = AdvancedCache(100); sc = SwarmCoordinator()
    ip = "192.168.1.50"
    assert v2.validate_ip_address(ip).result == ValidationResult.VALID
    ct, iv = enc2.encrypt(f"target:{ip}")
    cache.set("secure_target", (ct, iv))
    dec = enc2.decrypt(*cache.get("secure_target")).decode()
    assert dec == f"target:{ip}"
    for i in range(3): sc.register_agent(_agent(f"fs{i}"))
    return sc.leader_id is not None
test("validate → encrypt → cache → swarm", _full_stack)

# ═══════════════════════════════════════════════════════════
# 8. LIVE API TESTS
# ═══════════════════════════════════════════════════════════
section("8. LIVE API TESTS (http://localhost:5001)")
import urllib.request, json

def _get(path):
    try:
        with urllib.request.urlopen(f"http://localhost:5001{path}", timeout=3) as r:
            return json.loads(r.read().decode())
    except Exception: return None

# Initialize swarm with 8 agents first
def _post(path, data=None):
    try:
        body = json.dumps(data or {}).encode()
        req = urllib.request.Request(
            f"http://localhost:5001{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            return json.loads(r.read().decode())
    except Exception: return None

_post("/api/swarm/init", {"agent_count": 8})

health = _get("/api/health")
status = _get("/api/swarm/status")
agents = _get("/api/swarm/agents")

test("GET /api/health responds",            lambda: health is not None)
test("status == 'healthy'",                 lambda: (health or {}).get("status") == "healthy")
test("GET /api/swarm/status responds",      lambda: status is not None)
test("8 agents initialized",               lambda: (status or {}).get("stats", {}).get("total_agents", 0) == 8)
test("GET /api/swarm/agents → list",       lambda: isinstance((agents or {}).get("agents"), list))
test("GET /api/swarm/intelligence",        lambda: _get("/api/swarm/intelligence") is not None)
test("GET /api/swarm/stats",               lambda: _get("/api/swarm/stats") is not None)
test("GET /api/swarm/operations",          lambda: _get("/api/swarm/operations") is not None)

# ═══════════════════════════════════════════════════════════
# FINAL REPORT
# ═══════════════════════════════════════════════════════════
elapsed = time.time() - start_time
total = passed + failed + errors
pct = passed / max(total, 1) * 100

print(f"\n{'═'*60}")
print(f"  SERVERROOT.NET — PHASE 9 COMPLETE")
print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'═'*60}")
print(f"  Tests   : {total}")
print(f"  ✓ Pass  : {passed}  ({pct:.1f}%)")
print(f"  ✗ Fail  : {failed + errors}")
print(f"  ⏱ Time  : {elapsed:.2f}s")
print(f"{'═'*60}")

if failures:
    print("\n  FAILURES:")
    for n, r in failures:
        print(f"  ✗ {n}\n    → {r}")

if pct >= 95:   print(f"\n  🎯 EXCELLENT — {pct:.1f}% — PRODUCTION READY")
elif pct >= 80: print(f"\n  ⚠  GOOD — {pct:.1f}% — Minor issues")
else:           print(f"\n  ✗  NEEDS WORK — {pct:.1f}%")
print(f"{'═'*60}\n")

os.makedirs("tests", exist_ok=True)
with open("tests/test_results.md", "w") as f:
    f.write(f"# ServerRoot.net — Phase 9 Test Results\n\n")
    f.write(f"**Date**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write(f"| Metric | Value |\n|--------|-------|\n")
    f.write(f"| Total Tests | {total} |\n")
    f.write(f"| Passed | {passed} ({pct:.1f}%) |\n")
    f.write(f"| Failed | {failed} |\n| Errors | {errors} |\n")
    f.write(f"| Duration | {elapsed:.2f}s |\n\n")
    f.write("## Modules Tested\n\n")
    for i, m in enumerate(["Security Hardening","Error Handler","Performance Engine",
                            "Resource Manager","Reliability Engine","Swarm Coordinator",
                            "Integration Tests","Live API Tests"], 1):
        f.write(f"{i}. {m}\n")
    if failures:
        f.write("\n## Failures\n\n")
        for n, r in failures: f.write(f"- **{n}**: {r}\n")

sys.exit(0 if (failed + errors) == 0 else 1)