"""
Reporting Engine - Advanced Reporting & Analytics for ServerRoot.net

This module provides comprehensive reporting and analytics:
- Detailed execution logs
- Timeline visualization
- Attack chain reconstruction
- Success/failure analytics
- Performance benchmarking
- PDF/CSV export
"""

import json
import csv
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import threading
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ReportingEngine')


class LogLevel(Enum):
    """Log levels for execution logging"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    """Event types for execution tracking"""
    TARGET_DISCOVERY = "target_discovery"
    ATTACK_INITIATED = "attack_initiated"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"
    ATTACK_COMPLETED = "attack_completed"
    PERSISTENCE_ESTABLISHED = "persistence_established"
    EVASION_TRIGGERED = "evasion_triggered"
    DATA_EXFILTRATED = "data_exfiltrated"
    ERROR_OCCURRED = "error_occurred"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"


@dataclass
class LogEntry:
    """Single log entry"""
    timestamp: datetime
    level: LogLevel
    event_type: EventType
    agent_id: str
    target_id: Optional[str] = None
    chain_id: Optional[str] = None
    message: str = ""
    details: Dict = field(default_factory=dict)
    duration_ms: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'event_type': self.event_type.value,
            'agent_id': self.agent_id,
            'target_id': self.target_id,
            'chain_id': self.chain_id,
            'message': self.message,
            'details': self.details,
            'duration_ms': self.duration_ms
        }


@dataclass
class TimelineEvent:
    """Timeline visualization event"""
    timestamp: datetime
    event_type: str
    title: str
    description: str
    duration: Optional[int] = None  # milliseconds
    status: str = "success"  # success, failure, warning, info
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'title': self.title,
            'description': self.description,
            'duration': self.duration,
            'status': self.status,
            'metadata': self.metadata
        }


@dataclass
class AttackChainReconstruction:
    """Reconstructed attack chain with execution data"""
    chain_id: str
    target_id: str
    target_hostname: str
    target_platform: str
    planned_stages: List[Dict]
    executed_stages: List[Dict]
    start_time: datetime
    end_time: Optional[datetime]
    total_duration_ms: Optional[int]
    success: bool
    failure_point: Optional[str] = None
    deviations: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'chain_id': self.chain_id,
            'target_id': self.target_id,
            'target_hostname': self.target_hostname,
            'target_platform': self.target_platform,
            'planned_stages': self.planned_stages,
            'executed_stages': self.executed_stages,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_duration_ms': self.total_duration_ms,
            'success': self.success,
            'failure_point': self.failure_point,
            'deviations': self.deviations
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_duration_ms: int = 0
    average_duration_ms: float = 0.0
    min_duration_ms: int = float('inf')
    max_duration_ms: int = 0
    success_rate: float = 0.0
    
    def calculate(self, durations: List[int], successes: List[bool]):
        """Calculate metrics from data"""
        self.total_operations = len(durations)
        self.successful_operations = sum(successes)
        self.failed_operations = self.total_operations - self.successful_operations
        self.total_duration_ms = sum(durations)
        
        if self.total_operations > 0:
            self.average_duration_ms = self.total_duration_ms / self.total_operations
            self.min_duration_ms = min(durations)
            self.max_duration_ms = max(durations)
            self.success_rate = self.successful_operations / self.total_operations


@dataclass
class TimeRange:
    """Time range for filtering"""
    start: datetime
    end: datetime


class ReportingEngine:
    """
    Advanced Reporting and Analytics Engine
    
    Features:
    - Detailed execution logging
    - Timeline visualization
    - Attack chain reconstruction
    - Success/failure analytics
    - Performance benchmarking
    - PDF/CSV export
    """
    
    def __init__(self, max_log_entries: int = 100000):
        """Initialize Reporting Engine"""
        self.max_log_entries = max_log_entries
        self.logs: List[LogEntry] = []
        self.attack_chains: Dict[str, Dict] = {}  # chain_id -> chain data
        self.targets: Dict[str, Dict] = {}  # target_id -> target data
        
        # Performance tracking
        self.operation_durations: List[Tuple[str, int, bool]] = []  # (operation_type, duration, success)
        self.performance_metrics: Dict[str, PerformanceMetrics] = defaultdict(PerformanceMetrics)
        
        # Threading
        self.lock = threading.Lock()
        
        logger.info("Reporting Engine initialized")
    
    # ==================== EXECUTION LOGGING ====================
    
    def log(self, level: LogLevel, event_type: EventType, agent_id: str,
            message: str, target_id: Optional[str] = None,
            chain_id: Optional[str] = None, details: Dict = None,
            duration_ms: Optional[int] = None):
        """
        Log an event
        
        Args:
            level: Log level
            event_type: Event type
            agent_id: Agent that generated the event
            message: Log message
            target_id: Related target ID
            chain_id: Related attack chain ID
            details: Additional details
            duration_ms: Operation duration in milliseconds
        """
        with self.lock:
            entry = LogEntry(
                timestamp=datetime.now(),
                level=level,
                event_type=event_type,
                agent_id=agent_id,
                target_id=target_id,
                chain_id=chain_id,
                message=message,
                details=details or {},
                duration_ms=duration_ms
            )
            
            self.logs.append(entry)
            
            # Trim if exceeding max
            if len(self.logs) > self.max_log_entries:
                self.logs = self.logs[-self.max_log_entries:]
            
            # Track duration for performance
            if duration_ms is not None:
                operation_type = event_type.value
                success = level != LogLevel.ERROR and level != LogLevel.CRITICAL
                self.operation_durations.append((operation_type, duration_ms, success))
            
            logger.debug(f"[{level.value}] {event_type.value}: {message}")
    
    def get_logs(self, level: Optional[LogLevel] = None,
                 event_type: Optional[EventType] = None,
                 agent_id: Optional[str] = None,
                 target_id: Optional[str] = None,
                 chain_id: Optional[str] = None,
                 time_range: Optional[TimeRange] = None,
                 limit: Optional[int] = None) -> List[LogEntry]:
        """
        Get filtered logs
        
        Args:
            level: Filter by log level
            event_type: Filter by event type
            agent_id: Filter by agent ID
            target_id: Filter by target ID
            chain_id: Filter by chain ID
            time_range: Filter by time range
            limit: Limit number of results
            
        Returns:
            Filtered log entries
        """
        with self.lock:
            filtered = self.logs
            
            if level is not None:
                filtered = [log for log in filtered if log.level == level]
            
            if event_type is not None:
                filtered = [log for log in filtered if log.event_type == event_type]
            
            if agent_id is not None:
                filtered = [log for log in filtered if log.agent_id == agent_id]
            
            if target_id is not None:
                filtered = [log for log in filtered if log.target_id == target_id]
            
            if chain_id is not None:
                filtered = [log for log in filtered if log.chain_id == chain_id]
            
            if time_range is not None:
                filtered = [
                    log for log in filtered
                    if time_range.start <= log.timestamp <= time_range.end
                ]
            
            if limit is not None:
                filtered = filtered[-limit:]
            
            return filtered
    
    def get_logs_by_agent(self, agent_id: str, hours: int = 24) -> List[LogEntry]:
        """Get logs for specific agent within time window"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        time_range = TimeRange(start=start_time, end=end_time)
        return self.get_logs(agent_id=agent_id, time_range=time_range)
    
    # ==================== TIMELINE VISUALIZATION ====================
    
    def generate_timeline(self, time_range: Optional[TimeRange] = None,
                         agent_id: Optional[str] = None,
                         target_id: Optional[str] = None,
                         chain_id: Optional[str] = None) -> List[TimelineEvent]:
        """
        Generate timeline visualization
        
        Args:
            time_range: Time range to include
            agent_id: Filter by agent ID
            target_id: Filter by target ID
            chain_id: Filter by chain ID
            
        Returns:
            List of timeline events
        """
        with self.lock:
            logs = self.get_logs(
                time_range=time_range,
                agent_id=agent_id,
                target_id=target_id,
                chain_id=chain_id
            )
            
            timeline_events = []
            
            for log in logs:
                # Determine status based on level
                if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                    status = "failure"
                elif log.level == LogLevel.WARNING:
                    status = "warning"
                else:
                    status = "success"
                
                # Generate title
                title = log.event_type.value.replace('_', ' ').title()
                
                # Generate description
                description = f"{log.message}"
                if log.duration_ms:
                    description += f" ({log.duration_ms}ms)"
                
                event = TimelineEvent(
                    timestamp=log.timestamp,
                    event_type=log.event_type.value,
                    title=title,
                    description=description,
                    duration=log.duration_ms,
                    status=status,
                    metadata={
                        'agent_id': log.agent_id,
                        'target_id': log.target_id,
                        'chain_id': log.chain_id,
                        'level': log.level.value,
                        'details': log.details
                    }
                )
                timeline_events.append(event)
            
            # Sort by timestamp
            timeline_events.sort(key=lambda e: e.timestamp)
            
            return timeline_events
    
    def get_chain_timeline(self, chain_id: str) -> List[TimelineEvent]:
        """Get timeline for specific attack chain"""
        return self.generate_timeline(chain_id=chain_id)
    
    def get_agent_timeline(self, agent_id: str, hours: int = 24) -> List[TimelineEvent]:
        """Get timeline for specific agent"""
        return self.generate_timeline(agent_id=agent_id)
    
    # ==================== ATTACK CHAIN RECONSTRUCTION ====================
    
    def register_attack_chain(self, chain_id: str, target_id: str,
                              target_hostname: str, target_platform: str,
                              planned_stages: List[Dict]):
        """
        Register a new attack chain
        
        Args:
            chain_id: Chain ID
            target_id: Target ID
            target_hostname: Target hostname
            target_platform: Target platform
            planned_stages: List of planned stages
        """
        with self.lock:
            self.attack_chains[chain_id] = {
                'chain_id': chain_id,
                'target_id': target_id,
                'target_hostname': target_hostname,
                'target_platform': target_platform,
                'planned_stages': planned_stages,
                'executed_stages': [],
                'start_time': datetime.now(),
                'end_time': None,
                'success': False
            }
    
    def mark_stage_completed(self, chain_id: str, stage_name: str,
                            success: bool, duration_ms: int, details: Dict = None):
        """
        Mark a stage as completed
        
        Args:
            chain_id: Chain ID
            stage_name: Stage name
            success: Whether stage succeeded
            duration_ms: Stage duration
            details: Additional details
        """
        with self.lock:
            if chain_id not in self.attack_chains:
                logger.warning(f"Unknown chain ID: {chain_id}")
                return
            
            stage_data = {
                'stage_name': stage_name,
                'success': success,
                'duration_ms': duration_ms,
                'timestamp': datetime.now().isoformat(),
                'details': details or {}
            }
            
            self.attack_chains[chain_id]['executed_stages'].append(stage_data)
    
    def mark_chain_completed(self, chain_id: str, success: bool, failure_point: Optional[str] = None):
        """
        Mark attack chain as completed
        
        Args:
            chain_id: Chain ID
            success: Whether chain succeeded
            failure_point: Point of failure if failed
        """
        with self.lock:
            if chain_id not in self.attack_chains:
                logger.warning(f"Unknown chain ID: {chain_id}")
                return
            
            chain = self.attack_chains[chain_id]
            chain['end_time'] = datetime.now()
            chain['success'] = success
            
            if failure_point:
                chain['failure_point'] = failure_point
    
    def reconstruct_chain(self, chain_id: str) -> Optional[AttackChainReconstruction]:
        """
        Reconstruct attack chain with execution data
        
        Args:
            chain_id: Chain ID
            
        Returns:
            AttackChainReconstruction object or None
        """
        with self.lock:
            if chain_id not in self.attack_chains:
                return None
            
            chain_data = self.attack_chains[chain_id]
            
            start_time = chain_data['start_time']
            end_time = chain_data['end_time']
            
            total_duration_ms = None
            if end_time:
                delta = end_time - start_time
                total_duration_ms = int(delta.total_seconds() * 1000)
            
            # Find deviations (planned but not executed stages)
            planned_stages = chain_data['planned_stages']
            executed_stage_names = [s['stage_name'] for s in chain_data['executed_stages']]
            
            deviations = []
            for stage in planned_stages:
                stage_name = stage.get('stage', '')
                if stage_name not in executed_stage_names:
                    deviations.append({
                        'stage': stage_name,
                        'reason': 'not_executed'
                    })
            
            reconstruction = AttackChainReconstruction(
                chain_id=chain_id,
                target_id=chain_data['target_id'],
                target_hostname=chain_data['target_hostname'],
                target_platform=chain_data['target_platform'],
                planned_stages=planned_stages,
                executed_stages=chain_data['executed_stages'],
                start_time=start_time,
                end_time=end_time,
                total_duration_ms=total_duration_ms,
                success=chain_data['success'],
                failure_point=chain_data.get('failure_point'),
                deviations=deviations
            )
            
            return reconstruction
    
    def get_all_chains(self) -> List[Dict]:
        """Get all attack chains"""
        with self.lock:
            return list(self.attack_chains.values())
    
    # ==================== SUCCESS/FAILURE ANALYTICS ====================
    
    def calculate_success_rate(self, time_range: Optional[TimeRange] = None,
                              by_event_type: bool = False) -> Dict:
        """
        Calculate success rates
        
        Args:
            time_range: Time range to analyze
            by_event_type: Break down by event type
            
        Returns:
            Success rate statistics
        """
        with self.lock:
            logs = self.get_logs(time_range=time_range)
            
            if not logs:
                return {'total': 0, 'success': 0, 'failure': 0, 'rate': 0.0}
            
            error_levels = {LogLevel.ERROR, LogLevel.CRITICAL}
            
            if by_event_type:
                by_type = defaultdict(lambda: {'total': 0, 'success': 0, 'failure': 0})
                
                for log in logs:
                    event_type = log.event_type.value
                    by_type[event_type]['total'] += 1
                    
                    if log.level in error_levels:
                        by_type[event_type]['failure'] += 1
                    else:
                        by_type[event_type]['success'] += 1
                
                # Calculate rates
                result = {}
                for event_type, counts in by_type.items():
                    rate = counts['success'] / counts['total'] if counts['total'] > 0 else 0.0
                    result[event_type] = {
                        'total': counts['total'],
                        'success': counts['success'],
                        'failure': counts['failure'],
                        'rate': rate
                    }
                
                return result
            else:
                total = len(logs)
                failures = sum(1 for log in logs if log.level in error_levels)
                successes = total - failures
                rate = successes / total if total > 0 else 0.0
                
                return {
                    'total': total,
                    'success': successes,
                    'failure': failures,
                    'rate': rate
                }
    
    def get_failure_analysis(self, time_range: Optional[TimeRange] = None) -> Dict:
        """
        Analyze failures
        
        Args:
            time_range: Time range to analyze
            
        Returns:
            Failure analysis
        """
        with self.lock:
            error_levels = {LogLevel.ERROR, LogLevel.CRITICAL}
            logs = self.get_logs(time_range=time_range)
            error_logs = [log for log in logs if log.level in error_levels]
            
            if not error_logs:
                return {'total_failures': 0, 'by_event_type': {}, 'by_target': {}, 'common_messages': []}
            
            # Group by event type
            by_event_type = Counter(log.event_type.value for log in error_logs)
            
            # Group by target
            by_target = Counter(log.target_id for log in error_logs if log.target_id)
            
            # Common error messages (top 10)
            messages = [log.message for log in error_logs]
            common_messages = Counter(messages).most_common(10)
            
            return {
                'total_failures': len(error_logs),
                'by_event_type': dict(by_event_type),
                'by_target': dict(by_target),
                'common_messages': [{'message': msg, 'count': count} for msg, count in common_messages]
            }
    
    def get_target_analytics(self, target_id: str) -> Dict:
        """
        Get analytics for specific target
        
        Args:
            target_id: Target ID
            
        Returns:
            Target analytics
        """
        with self.lock:
            logs = self.get_logs(target_id=target_id)
            
            if not logs:
                return {'target_id': target_id, 'total_events': 0}
            
            # Count by event type
            by_event_type = Counter(log.event_type.value for log in logs)
            
            # Count by level
            by_level = Counter(log.level.value for log in logs)
            
            # Get chains
            chains = [chain for chain in self.attack_chains.values() if chain['target_id'] == target_id]
            
            # Success rate
            successful_chains = sum(1 for chain in chains if chain['success'])
            chain_success_rate = successful_chains / len(chains) if chains else 0.0
            
            return {
                'target_id': target_id,
                'total_events': len(logs),
                'by_event_type': dict(by_event_type),
                'by_level': dict(by_level),
                'total_chains': len(chains),
                'successful_chains': successful_chains,
                'chain_success_rate': chain_success_rate,
                'first_event': logs[0].timestamp.isoformat() if logs else None,
                'last_event': logs[-1].timestamp.isoformat() if logs else None
            }
    
    # ==================== PERFORMANCE BENCHMARKING ====================
    
    def update_performance_metrics(self):
        """Update performance metrics from collected data"""
        with self.lock:
            # Group by operation type
            by_type = defaultdict(lambda: {'durations': [], 'successes': []})
            
            for op_type, duration, success in self.operation_durations:
                by_type[op_type]['durations'].append(duration)
                by_type[op_type]['successes'].append(success)
            
            # Calculate metrics for each type
            for op_type, data in by_type.items():
                metrics = PerformanceMetrics()
                metrics.calculate(data['durations'], data['successes'])
                self.performance_metrics[op_type] = metrics
    
    def get_performance_metrics(self, operation_type: Optional[str] = None) -> Dict:
        """
        Get performance metrics
        
        Args:
            operation_type: Specific operation type, or None for summary
            
        Returns:
            Performance metrics
        """
        self.update_performance_metrics()
        
        with self.lock:
            if operation_type is not None:
                if operation_type in self.performance_metrics:
                    metrics = self.performance_metrics[operation_type]
                    return {
                        'operation_type': operation_type,
                        'total_operations': metrics.total_operations,
                        'successful_operations': metrics.successful_operations,
                        'failed_operations': metrics.failed_operations,
                        'total_duration_ms': metrics.total_duration_ms,
                        'average_duration_ms': metrics.average_duration_ms,
                        'min_duration_ms': metrics.min_duration_ms,
                        'max_duration_ms': metrics.max_duration_ms,
                        'success_rate': metrics.success_rate
                    }
                else:
                    return {'operation_type': operation_type, 'message': 'No data available'}
            else:
                # Summary of all operations
                result = {}
                for op_type, metrics in self.performance_metrics.items():
                    result[op_type] = {
                        'total_operations': metrics.total_operations,
                        'average_duration_ms': metrics.average_duration_ms,
                        'success_rate': metrics.success_rate
                    }
                return result
    
    def compare_performance(self, operation_types: List[str]) -> Dict:
        """
        Compare performance between operation types
        
        Args:
            operation_types: List of operation types to compare
            
        Returns:
            Comparison results
        """
        self.update_performance_metrics()
        
        with self.lock:
            comparison = {}
            
            for op_type in operation_types:
                if op_type in self.performance_metrics:
                    metrics = self.performance_metrics[op_type]
                    comparison[op_type] = {
                        'avg_duration_ms': metrics.average_duration_ms,
                        'success_rate': metrics.success_rate,
                        'total_ops': metrics.total_operations
                    }
            
            return comparison
    
    # ==================== EXPORT FUNCTIONS ====================
    
    def export_logs_to_csv(self, time_range: Optional[TimeRange] = None,
                          **filters) -> str:
        """
        Export logs to CSV format
        
        Args:
            time_range: Time range to export
            **filters: Additional filters
            
        Returns:
            CSV string
        """
        logs = self.get_logs(time_range=time_range, **filters)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'timestamp', 'level', 'event_type', 'agent_id',
            'target_id', 'chain_id', 'message', 'duration_ms'
        ])
        
        # Rows
        for log in logs:
            writer.writerow([
                log.timestamp.isoformat(),
                log.level.value,
                log.event_type.value,
                log.agent_id,
                log.target_id or '',
                log.chain_id or '',
                log.message,
                log.duration_ms or ''
            ])
        
        return output.getvalue()
    
    def export_timeline_to_csv(self, time_range: Optional[TimeRange] = None,
                              **filters) -> str:
        """
        Export timeline to CSV format
        
        Args:
            time_range: Time range to export
            **filters: Additional filters
            
        Returns:
            CSV string
        """
        timeline = self.generate_timeline(time_range=time_range, **filters)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'timestamp', 'event_type', 'title', 'description',
            'duration_ms', 'status'
        ])
        
        # Rows
        for event in timeline:
            writer.writerow([
                event.timestamp.isoformat(),
                event.event_type,
                event.title,
                event.description,
                event.duration or '',
                event.status
            ])
        
        return output.getvalue()
    
    def export_chains_to_json(self) -> str:
        """
        Export all chains to JSON format
        
        Returns:
            JSON string
        """
        with self.lock:
            chains = [chain for chain in self.attack_chains.values()]
            return json.dumps(chains, indent=2, default=str)
    
    def export_analytics_to_json(self, time_range: Optional[TimeRange] = None) -> str:
        """
        Export analytics to JSON format
        
        Args:
            time_range: Time range to analyze
            
        Returns:
            JSON string
        """
        success_rate = self.calculate_success_rate(time_range=time_range)
        failure_analysis = self.get_failure_analysis(time_range=time_range)
        performance = self.get_performance_metrics()
        
        analytics = {
            'success_rate': success_rate,
            'failure_analysis': failure_analysis,
            'performance_metrics': performance,
            'export_time': datetime.now().isoformat()
        }
        
        return json.dumps(analytics, indent=2)
    
    def generate_summary_report(self, hours: int = 24) -> Dict:
        """
        Generate summary report for time period
        
        Args:
            hours: Number of hours to include
            
        Returns:
            Summary report
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        time_range = TimeRange(start=start_time, end=end_time)
        
        success_rate = self.calculate_success_rate(time_range=time_range, by_event_type=True)
        failure_analysis = self.get_failure_analysis(time_range=time_range)
        performance = self.get_performance_metrics()
        
        logs = self.get_logs(time_range=time_range)
        agents = set(log.agent_id for log in logs)
        targets = set(log.target_id for log in logs if log.target_id)
        
        return {
            'report_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'hours': hours
            },
            'summary': {
                'total_events': len(logs),
                'unique_agents': len(agents),
                'unique_targets': len(targets),
                'total_chains': len(self.attack_chains)
            },
            'success_rate_by_event_type': success_rate,
            'failure_analysis': failure_analysis,
            'performance_metrics': performance,
            'generation_time': datetime.now().isoformat()
        }


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Create Reporting Engine
    engine = ReportingEngine()
    
    # Register an attack chain
    engine.register_attack_chain(
        chain_id="chain_001",
        target_id="target_001",
        target_hostname="server-prod-01",
        target_platform="windows",
        planned_stages=[
            {'stage': 'reconnaissance', 'technique': 'network_scan', 'duration': 5},
            {'stage': 'initial_access', 'technique': 'smb_exploit', 'duration': 10},
            {'stage': 'defense_evasion', 'technique': 'process_injection', 'duration': 8},
            {'stage': 'privilege_escalation', 'technique': 'privilege_escalation', 'duration': 15}
        ]
    )
    
    # Log events
    engine.log(
        level=LogLevel.INFO,
        event_type=EventType.ATTACK_INITIATED,
        agent_id="agent_001",
        message="Attack chain initiated",
        target_id="target_001",
        chain_id="chain_001"
    )
    
    # Mark stage completed
    engine.mark_stage_completed(
        chain_id="chain_001",
        stage_name="reconnaissance",
        success=True,
        duration_ms=5000
    )
    
    engine.mark_stage_completed(
        chain_id="chain_001",
        stage_name="initial_access",
        success=True,
        duration_ms=10000
    )
    
    # Mark some stages as failed
    engine.mark_stage_completed(
        chain_id="chain_001",
        stage_name="defense_evasion",
        success=False,
        duration_ms=8000
    )
    
    # Mark chain completed
    engine.mark_chain_completed(
        chain_id="chain_001",
        success=False,
        failure_point="defense_evasion"
    )
    
    # Generate timeline
    timeline = engine.generate_timeline()
    print(f"Timeline Events: {len(timeline)}")
    
    # Reconstruct chain
    reconstruction = engine.reconstruct_chain("chain_001")
    if reconstruction:
        print(f"\nChain Reconstruction:")
        print(f"Target: {reconstruction.target_hostname}")
        print(f"Success: {reconstruction.success}")
        print(f"Total Duration: {reconstruction.total_duration_ms}ms")
        print(f"Failure Point: {reconstruction.failure_point}")
        print(f"Executed Stages: {len(reconstruction.executed_stages)}")
    
    # Calculate success rate
    success_rate = engine.calculate_success_rate()
    print(f"\nSuccess Rate: {success_rate['rate']:.2%}")
    
    # Performance metrics
    engine.update_performance_metrics()
    perf = engine.get_performance_metrics()
    print(f"\nPerformance Metrics: {perf}")
    
    # Generate summary report
    summary = engine.generate_summary_report(hours=24)
    print(f"\nSummary Report: {summary}")
    
    print("\nReporting Engine demo complete!")