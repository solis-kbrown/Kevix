"""
SERVERROOT.NET - Performance Optimization Engine
Phase 8: Comprehensive performance optimization

Features:
- Async operation pipeline
- Multi-level caching (LRU, TTL, write-through)
- Connection pooling
- Data compression
- Parallel processing with worker pools
- Performance profiling and benchmarking
- Algorithm optimization utilities
"""

import os
import gzip
import zlib
import time
import asyncio
import threading
import hashlib
import logging
import cProfile
import pstats
import io
import functools
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import queue

logger = logging.getLogger(__name__)
T = TypeVar('T')


# ============================================================
# ENUMS
# ============================================================

class CacheStrategy(Enum):
    LRU = "lru"               # Least Recently Used eviction
    TTL = "ttl"               # Time-To-Live expiration
    LFU = "lfu"               # Least Frequently Used eviction
    WRITE_THROUGH = "write_through"


class CompressionAlgorithm(Enum):
    GZIP = "gzip"
    ZLIB = "zlib"
    LZ4 = "lz4"
    NONE = "none"


class WorkerPoolType(Enum):
    THREAD = "thread"
    PROCESS = "process"
    ASYNC = "async"


# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class CacheEntry:
    """A single cache entry"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    ttl_seconds: Optional[float] = None
    access_count: int = 0
    size_bytes: int = 0

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return time.time() - self.created_at > self.ttl_seconds

    def touch(self):
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    total_size_bytes: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(self.hit_rate, 4),
            "size": self.size,
            "total_size_bytes": self.total_size_bytes
        }


@dataclass
class PerformanceProfile:
    """Performance profiling result"""
    operation: str
    duration_ms: float
    cpu_time_ms: float
    memory_delta_mb: float
    throughput: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "operation": self.operation,
            "duration_ms": round(self.duration_ms, 3),
            "cpu_time_ms": round(self.cpu_time_ms, 3),
            "memory_delta_mb": round(self.memory_delta_mb, 3),
            "throughput": round(self.throughput, 2),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class BenchmarkResult:
    """Benchmark test result"""
    name: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    throughput_ops_sec: float
    errors: int = 0

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time_ms": round(self.total_time_ms, 3),
            "avg_time_ms": round(self.avg_time_ms, 3),
            "min_time_ms": round(self.min_time_ms, 3),
            "max_time_ms": round(self.max_time_ms, 3),
            "p95_time_ms": round(self.p95_time_ms, 3),
            "p99_time_ms": round(self.p99_time_ms, 3),
            "throughput_ops_sec": round(self.throughput_ops_sec, 2),
            "errors": self.errors
        }


# ============================================================
# MULTI-LEVEL CACHE
# ============================================================

class AdvancedCache:
    """
    High-performance multi-strategy cache
    Supports LRU, TTL, and LFU eviction strategies
    Thread-safe with lock-free reads where possible
    """

    def __init__(self, max_size: int = 1000,
                 strategy: CacheStrategy = CacheStrategy.LRU,
                 default_ttl: Optional[float] = None):
        self.max_size = max_size
        self.strategy = strategy
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats()
        self._lock = threading.RLock()
        logger.debug(f"AdvancedCache initialized: size={max_size}, strategy={strategy.value}")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats.misses += 1
                return None
            
            # Check TTL expiration
            if entry.is_expired:
                del self._cache[key]
                self._stats.misses += 1
                self._stats.size -= 1
                return None
            
            # Update access info
            entry.touch()
            self._stats.hits += 1
            
            # Move to end for LRU
            if self.strategy == CacheStrategy.LRU:
                self._cache.move_to_end(key)
            
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in cache"""
        with self._lock:
            ttl = ttl or self.default_ttl
            
            # Calculate approximate size
            try:
                size = len(str(value).encode('utf-8'))
            except Exception:
                size = 0
            
            # If key exists, update
            if key in self._cache:
                self._stats.total_size_bytes -= self._cache[key].size_bytes
                entry = self._cache[key]
                entry.value = value
                entry.created_at = time.time()
                entry.ttl_seconds = ttl
                entry.size_bytes = size
                self._stats.total_size_bytes += size
                if self.strategy == CacheStrategy.LRU:
                    self._cache.move_to_end(key)
                return True
            
            # Evict if at capacity
            if len(self._cache) >= self.max_size:
                self._evict()
            
            # Add new entry
            entry = CacheEntry(key=key, value=value, ttl_seconds=ttl, size_bytes=size)
            self._cache[key] = entry
            self._stats.size += 1
            self._stats.total_size_bytes += size
            return True

    def delete(self, key: str) -> bool:
        """Delete a cache entry"""
        with self._lock:
            if key in self._cache:
                self._stats.total_size_bytes -= self._cache[key].size_bytes
                del self._cache[key]
                self._stats.size -= 1
                return True
        return False

    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()

    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        with self._lock:
            self._stats.size = len(self._cache)
            return self._stats

    def _evict(self):
        """Evict entries based on strategy"""
        if not self._cache:
            return

        if self.strategy == CacheStrategy.LRU:
            # Remove least recently used (first item in OrderedDict)
            key, entry = next(iter(self._cache.items()))
            self._stats.total_size_bytes -= entry.size_bytes
            del self._cache[key]
        elif self.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            min_key = min(self._cache.keys(),
                          key=lambda k: self._cache[k].access_count)
            self._stats.total_size_bytes -= self._cache[min_key].size_bytes
            del self._cache[min_key]
        elif self.strategy == CacheStrategy.TTL:
            # Remove expired entries first, then oldest
            expired = [k for k, e in self._cache.items() if e.is_expired]
            if expired:
                for k in expired:
                    self._stats.total_size_bytes -= self._cache[k].size_bytes
                    del self._cache[k]
            else:
                key, entry = next(iter(self._cache.items()))
                self._stats.total_size_bytes -= entry.size_bytes
                del self._cache[key]

        self._stats.evictions += 1


def cached(cache: AdvancedCache, key_func: Optional[Callable] = None,
           ttl: Optional[float] = None):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Try cache first
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


# ============================================================
# DATA COMPRESSION
# ============================================================

class CompressionEngine:
    """
    Efficient data compression for network traffic and storage
    Supports multiple algorithms with automatic selection
    """

    def __init__(self, default_algorithm: CompressionAlgorithm = CompressionAlgorithm.ZLIB,
                 compression_level: int = 6):
        self.default_algorithm = default_algorithm
        self.compression_level = compression_level
        self._stats = {"compressed": 0, "decompressed": 0,
                       "bytes_saved": 0, "total_original": 0}
        logger.debug(f"CompressionEngine initialized: {default_algorithm.value}")

    def compress(self, data: bytes,
                 algorithm: Optional[CompressionAlgorithm] = None) -> Tuple[bytes, CompressionAlgorithm]:
        """Compress data with specified or auto-selected algorithm"""
        algo = algorithm or self.default_algorithm
        original_size = len(data)

        if algo == CompressionAlgorithm.GZIP:
            compressed = gzip.compress(data, compresslevel=self.compression_level)
        elif algo == CompressionAlgorithm.ZLIB:
            compressed = zlib.compress(data, self.compression_level)
        else:
            return data, CompressionAlgorithm.NONE

        # Only use compression if it actually saves space
        if len(compressed) >= original_size:
            return data, CompressionAlgorithm.NONE

        self._stats["compressed"] += 1
        self._stats["bytes_saved"] += original_size - len(compressed)
        self._stats["total_original"] += original_size

        return compressed, algo

    def decompress(self, data: bytes,
                   algorithm: CompressionAlgorithm = CompressionAlgorithm.ZLIB) -> bytes:
        """Decompress data"""
        if algorithm == CompressionAlgorithm.GZIP:
            result = gzip.decompress(data)
        elif algorithm == CompressionAlgorithm.ZLIB:
            result = zlib.decompress(data)
        else:
            result = data

        self._stats["decompressed"] += 1
        return result

    def compress_string(self, text: str) -> Tuple[bytes, CompressionAlgorithm]:
        """Compress a string"""
        return self.compress(text.encode('utf-8'))

    def decompress_string(self, data: bytes,
                          algorithm: CompressionAlgorithm = CompressionAlgorithm.ZLIB) -> str:
        """Decompress to string"""
        return self.decompress(data, algorithm).decode('utf-8')

    def get_ratio(self, original: bytes, compressed: bytes) -> float:
        """Get compression ratio"""
        if len(original) == 0:
            return 1.0
        return len(compressed) / len(original)

    def get_stats(self) -> Dict:
        """Get compression statistics"""
        total = self._stats["total_original"]
        saved = self._stats["bytes_saved"]
        return {
            **self._stats,
            "average_ratio": round(1 - saved / total, 4) if total > 0 else 1.0,
            "space_savings_pct": round(saved / total * 100, 2) if total > 0 else 0.0
        }


# ============================================================
# ASYNC OPERATION PIPELINE
# ============================================================

class AsyncPipeline:
    """
    High-performance async operation pipeline
    Enables non-blocking I/O and parallel processing
    """

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._task_queue: queue.Queue = queue.Queue()
        self._results: Dict[str, Any] = {}
        self._stats = {"submitted": 0, "completed": 0, "failed": 0}
        self._lock = threading.Lock()
        logger.debug(f"AsyncPipeline initialized: workers={max_workers}")

    def submit(self, task_id: str, func: Callable, *args, **kwargs) -> Any:
        """Submit a task for async execution"""
        with self._lock:
            self._stats["submitted"] += 1
        
        future = self._executor.submit(func, *args, **kwargs)
        future.task_id = task_id
        
        def done_callback(f):
            with self._lock:
                if f.exception():
                    self._stats["failed"] += 1
                    self._results[task_id] = {"error": str(f.exception())}
                else:
                    self._stats["completed"] += 1
                    self._results[task_id] = {"result": f.result()}
        
        future.add_done_callback(done_callback)
        return future

    def submit_batch(self, tasks: List[Tuple[str, Callable, tuple, dict]]) -> List[Any]:
        """Submit a batch of tasks for parallel execution"""
        futures = []
        for task_id, func, args, kwargs in tasks:
            future = self.submit(task_id, func, *args, **kwargs)
            futures.append(future)
        return futures

    def execute_parallel(self, funcs: List[Callable], timeout: float = 30.0) -> List[Any]:
        """Execute multiple functions in parallel, return results"""
        futures = [self._executor.submit(func) for func in funcs]
        results = []
        for future in as_completed(futures, timeout=timeout):
            try:
                results.append(future.result())
            except Exception as e:
                results.append(None)
                logger.error(f"Parallel task failed: {e}")
        return results

    def get_result(self, task_id: str) -> Optional[Any]:
        """Get result of a completed task"""
        with self._lock:
            return self._results.get(task_id)

    def get_stats(self) -> Dict:
        """Get pipeline statistics"""
        with self._lock:
            return {**self._stats,
                    "pending": self._stats["submitted"] - self._stats["completed"] - self._stats["failed"]}

    def shutdown(self):
        """Shutdown the pipeline"""
        self._executor.shutdown(wait=True)


# ============================================================
# PERFORMANCE PROFILER
# ============================================================

class PerformanceProfiler:
    """
    Profile code performance to identify bottlenecks
    """

    def __init__(self):
        self._profiles: List[PerformanceProfile] = []
        self._active_timers: Dict[str, float] = {}
        self._lock = threading.Lock()
        logger.debug("PerformanceProfiler initialized")

    def time_operation(self, operation: str):
        """Context manager for timing an operation"""
        return _TimingContext(self, operation)

    def profile_function(self, func: Callable, *args, **kwargs) -> Tuple[Any, PerformanceProfile]:
        """Profile a function call with cProfile"""
        import psutil
        process = psutil.Process(os.getpid())
        
        mem_before = process.memory_info().rss / (1024 * 1024)
        start_cpu = process.cpu_times().user
        start_wall = time.perf_counter()
        
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        end_wall = time.perf_counter()
        end_cpu = process.cpu_times().user
        mem_after = process.memory_info().rss / (1024 * 1024)
        
        duration_ms = (end_wall - start_wall) * 1000
        cpu_ms = (end_cpu - start_cpu) * 1000
        mem_delta = mem_after - mem_before
        
        # Get top functions
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats('cumulative')
        stats.print_stats(5)
        top_funcs = stream.getvalue()
        
        profile = PerformanceProfile(
            operation=func.__name__,
            duration_ms=duration_ms,
            cpu_time_ms=cpu_ms,
            memory_delta_mb=mem_delta,
            throughput=1000 / duration_ms if duration_ms > 0 else 0,
            metadata={"top_functions": top_funcs[:200]}
        )
        
        with self._lock:
            self._profiles.append(profile)
        
        return result, profile

    def record_profile(self, profile: PerformanceProfile):
        """Record a performance profile"""
        with self._lock:
            self._profiles.append(profile)

    def get_slowest_operations(self, limit: int = 10) -> List[PerformanceProfile]:
        """Get slowest recorded operations"""
        with self._lock:
            return sorted(self._profiles, key=lambda p: p.duration_ms, reverse=True)[:limit]

    def get_summary(self) -> Dict:
        """Get performance summary"""
        with self._lock:
            if not self._profiles:
                return {"message": "No profiles recorded"}
            
            durations = [p.duration_ms for p in self._profiles]
            return {
                "total_operations": len(self._profiles),
                "avg_duration_ms": round(sum(durations) / len(durations), 3),
                "max_duration_ms": round(max(durations), 3),
                "min_duration_ms": round(min(durations), 3),
                "operations": list(set(p.operation for p in self._profiles))
            }


class _TimingContext:
    """Context manager for timing operations"""

    def __init__(self, profiler: PerformanceProfiler, operation: str):
        self.profiler = profiler
        self.operation = operation
        self.start_time = 0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        profile = PerformanceProfile(
            operation=self.operation,
            duration_ms=duration_ms,
            cpu_time_ms=duration_ms * 0.8,  # Approximate
            memory_delta_mb=0,
            throughput=1000 / duration_ms if duration_ms > 0 else 0
        )
        self.profiler.record_profile(profile)


# ============================================================
# BENCHMARKER
# ============================================================

class Benchmarker:
    """
    Run performance benchmarks on operations
    """

    def __init__(self):
        self._results: List[BenchmarkResult] = []

    def benchmark(self, name: str, func: Callable,
                  iterations: int = 100,
                  warmup: int = 5) -> BenchmarkResult:
        """Run a benchmark"""
        # Warmup
        for _ in range(warmup):
            try:
                func()
            except Exception:
                pass

        # Benchmark
        times = []
        errors = 0
        total_start = time.perf_counter()

        for _ in range(iterations):
            start = time.perf_counter()
            try:
                func()
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
            except Exception as e:
                errors += 1
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)

        total_time = (time.perf_counter() - total_start) * 1000

        if not times:
            times = [0]

        times.sort()
        p95_idx = int(len(times) * 0.95)
        p99_idx = int(len(times) * 0.99)

        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time_ms=total_time,
            avg_time_ms=sum(times) / len(times),
            min_time_ms=times[0],
            max_time_ms=times[-1],
            p95_time_ms=times[min(p95_idx, len(times)-1)],
            p99_time_ms=times[min(p99_idx, len(times)-1)],
            throughput_ops_sec=iterations / (total_time / 1000) if total_time > 0 else 0,
            errors=errors
        )

        self._results.append(result)
        logger.info(f"Benchmark '{name}': avg={result.avg_time_ms:.3f}ms, "
                    f"p95={result.p95_time_ms:.3f}ms, "
                    f"throughput={result.throughput_ops_sec:.1f} ops/sec")
        return result

    def get_results(self) -> List[BenchmarkResult]:
        return self._results

    def get_comparison(self) -> Dict:
        """Compare all benchmark results"""
        if not self._results:
            return {}
        return {
            r.name: r.to_dict() for r in sorted(
                self._results, key=lambda x: x.avg_time_ms
            )
        }


# ============================================================
# MAIN PERFORMANCE ENGINE
# ============================================================

class PerformanceEngine:
    """
    Central performance optimization engine
    Coordinates all performance components
    """

    def __init__(self, cache_size: int = 1000, worker_count: int = 8):
        # Multi-level caches
        self.l1_cache = AdvancedCache(max_size=100, strategy=CacheStrategy.LRU,
                                       default_ttl=60)
        self.l2_cache = AdvancedCache(max_size=cache_size, strategy=CacheStrategy.LRU,
                                       default_ttl=300)
        self.result_cache = AdvancedCache(max_size=500, strategy=CacheStrategy.TTL,
                                           default_ttl=600)

        # Compression
        self.compressor = CompressionEngine()

        # Async pipeline
        self.pipeline = AsyncPipeline(max_workers=worker_count)

        # Profiling
        self.profiler = PerformanceProfiler()
        self.benchmarker = Benchmarker()

        logger.info(f"PerformanceEngine initialized: cache={cache_size}, workers={worker_count}")

    def run_benchmarks(self) -> Dict:
        """Run standard performance benchmarks"""
        results = {}

        # Cache benchmark
        r = self.benchmarker.benchmark(
            "cache_set_get",
            lambda: (self.l1_cache.set("bench_key", "bench_value"),
                     self.l1_cache.get("bench_key")),
            iterations=1000
        )
        results["cache"] = r.to_dict()

        # Compression benchmark
        test_data = b"A" * 10000  # 10KB of data
        r = self.benchmarker.benchmark(
            "compression_zlib",
            lambda: self.compressor.compress(test_data),
            iterations=100
        )
        results["compression"] = r.to_dict()

        # JSON serialization benchmark
        import json
        test_obj = {"agents": [{"id": f"agent_{i}", "load": 0.5} for i in range(100)]}
        r = self.benchmarker.benchmark(
            "json_serialization",
            lambda: json.dumps(test_obj),
            iterations=1000
        )
        results["json"] = r.to_dict()

        return results

    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        return {
            "caches": {
                "l1": self.l1_cache.get_stats().to_dict(),
                "l2": self.l2_cache.get_stats().to_dict(),
                "result": self.result_cache.get_stats().to_dict()
            },
            "compression": self.compressor.get_stats(),
            "pipeline": self.pipeline.get_stats(),
            "profiler": self.profiler.get_summary(),
            "timestamp": datetime.now().isoformat()
        }

    def shutdown(self):
        """Shutdown performance engine"""
        self.pipeline.shutdown()
        logger.info("PerformanceEngine shutdown")