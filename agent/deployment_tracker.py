"""
Deployment Tracker - Monitors deployment queue and metrics
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import threading
import time

logger = logging.getLogger(__name__)

class DeploymentStatus(Enum):
    """Deployment status"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"

class DeploymentTracker:
    """Tracks deployment operations and metrics"""
    
    def __init__(self):
        self.deployment_queue: List[Dict] = []
        self.deployment_history: List[Dict] = []
        self.metrics = {
            'total_deployments': 0,
            'successful_deployments': 0,
            'failed_deployments': 0,
            'pending_deployments': 0,
            'in_progress_deployments': 0,
            'success_rate': 0.0,
            'average_deployment_time': 0.0
        }
        self.lock = threading.Lock()
        self.start_time = datetime.now()
    
    def queue_deployment(self, target: str, platform: str, priority: int = 5) -> str:
        """Queue a new deployment"""
        deployment_id = f"deploy_{int(time.time() * 1000)}"
        
        deployment = {
            'deployment_id': deployment_id,
            'target': target,
            'platform': platform,
            'status': DeploymentStatus.QUEUED.value,
            'priority': priority,
            'queued_at': datetime.now(),
            'started_at': None,
            'completed_at': None,
            'retry_count': 0,
            'max_retries': 3,
            'error_message': None
        }
        
        with self.lock:
            self.deployment_queue.append(deployment)
            self.metrics['total_deployments'] += 1
            self.metrics['pending_deployments'] += 1
        
        logger.info(f"Deployment queued: {deployment_id} -> {target}")
        return deployment_id
    
    def start_deployment(self, deployment_id: str) -> bool:
        """Mark deployment as started"""
        with self.lock:
            for deployment in self.deployment_queue:
                if deployment['deployment_id'] == deployment_id:
                    deployment['status'] = DeploymentStatus.IN_PROGRESS.value
                    deployment['started_at'] = datetime.now()
                    deployment['retry_count'] += 1
                    self.metrics['pending_deployments'] -= 1
                    self.metrics['in_progress_deployments'] += 1
                    return True
        return False
    
    def complete_deployment(self, deployment_id: str, success: bool, error_message: Optional[str] = None) -> bool:
        """Mark deployment as completed"""
        with self.lock:
            for deployment in self.deployment_queue:
                if deployment['deployment_id'] == deployment_id:
                    deployment['status'] = DeploymentStatus.SUCCESS.value if success else DeploymentStatus.FAILED.value
                    deployment['completed_at'] = datetime.now()
                    deployment['error_message'] = error_message
                    self.metrics['in_progress_deployments'] -= 1
                    
                    if success:
                        self.metrics['successful_deployments'] += 1
                        logger.info(f"Deployment completed successfully: {deployment_id}")
                        
                        # Move to history
                        self.deployment_history.append(deployment)
                        self.deployment_queue.remove(deployment)
                    else:
                        # Check if retry is possible BEFORE counting as failed
                        if deployment['retry_count'] < deployment['max_retries']:
                            deployment['status'] = DeploymentStatus.RETRYING.value
                            deployment['retry_count'] += 1
                            self.metrics['pending_deployments'] += 1
                            logger.info(f"Scheduling retry for deployment: {deployment_id} (attempt {deployment['retry_count']})")
                        else:
                            # Max retries reached, count as failed
                            self.metrics['failed_deployments'] += 1
                            logger.warning(f"Deployment failed after {deployment['retry_count']} attempts: {deployment_id} - {error_message}")
                            
                            # Move to history
                            self.deployment_history.append(deployment)
                            self.deployment_queue.remove(deployment)
                    
                    # Update success rate
                    self._update_metrics()
                    
                    return True
        return False
    
    def _update_metrics(self):
        """Update deployment metrics"""
        total = self.metrics['successful_deployments'] + self.metrics['failed_deployments']
        if total > 0:
            self.metrics['success_rate'] = round(
                (self.metrics['successful_deployments'] / total) * 100, 2
            )
        
        # Calculate average deployment time
        completed = [d for d in self.deployment_history if d['completed_at'] and d['started_at']]
        if completed:
            total_time = sum([(d['completed_at'] - d['started_at']).total_seconds() for d in completed])
            self.metrics['average_deployment_time'] = round(total_time / len(completed), 2)
    
    def get_queue_status(self) -> Dict:
        """Get current queue status"""
        with self.lock:
            return {
                'pending_count': len([d for d in self.deployment_queue if d['status'] == DeploymentStatus.QUEUED.value]),
                'in_progress_count': len([d for d in self.deployment_queue if d['status'] == DeploymentStatus.IN_PROGRESS.value]),
                'retrying_count': len([d for d in self.deployment_queue if d['status'] == DeploymentStatus.RETRYING.value]),
                'total_in_queue': len(self.deployment_queue)
            }
    
    def get_deployment_metrics(self) -> Dict:
        """Get deployment metrics"""
        with self.lock:
            return {
                **self.metrics,
                'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
                'deployments_per_hour': round(
                    self.metrics['total_deployments'] / max(1, (datetime.now() - self.start_time).total_seconds() / 3600),
                    2
                )
            }
    
    def get_recent_deployments(self, count: int = 10) -> List[Dict]:
        """Get recent deployments"""
        with self.lock:
            return sorted(
                self.deployment_history,
                key=lambda x: x['completed_at'] or datetime.min,
                reverse=True
            )[:count]
    
    def get_failed_deployments(self) -> List[Dict]:
        """Get failed deployments that may need attention"""
        with self.lock:
            return [d for d in self.deployment_history if d['status'] == DeploymentStatus.FAILED.value]