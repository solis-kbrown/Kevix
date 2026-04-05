"""
Persistence Helper Module
Helper functions to integrate persistence manager with autonomous swarm agents
"""

import logging

try:
    from persistence_manager import PersistenceManager
    PERSISTENCE_AVAILABLE = True
except ImportError:
    PERSISTENCE_AVAILABLE = False

logger = logging.getLogger(__name__)


def activate_persistence(agent):
    """
    Activate unstoppable persistence for an agent
    
    Args:
        agent: SwarmAgent instance with persistence_manager attribute
    """
    if not PERSISTENCE_AVAILABLE:
        logger.warning("Persistence manager not available")
        return False
    
    if not hasattr(agent, 'persistence_manager') or agent.persistence_manager is None:
        logger.warning(f"Agent {agent.agent_id} has no persistence manager")
        return False
    
    try:
        # Install persistence mechanisms
        if agent.persistence_manager.install_persistence():
            logger.info(f"[{agent.agent_id}] ✅ Unstoppable persistence installed")
            
            # Start health monitoring
            if not agent.persistence_manager.is_running:
                agent.persistence_manager.start_health_monitoring()
                logger.info(f"[{agent.agent_id}] ❤️ Self-healing activated")
            
            return True
        else:
            logger.warning(f"[{agent.agent_id}] Failed to install persistence")
            return False
            
    except Exception as e:
        logger.error(f"[{agent.agent_id}] Error activating persistence: {e}")
        return False


def deactivate_persistence(agent):
    """
    Deactivate persistence for an agent (usually not called in production)
    
    Args:
        agent: SwarmAgent instance with persistence_manager attribute
    """
    if not hasattr(agent, 'persistence_manager') or agent.persistence_manager is None:
        return
    
    try:
        agent.persistence_manager.stop_health_monitoring()
        logger.info(f"[{agent.agent_id}] Persistence deactivated")
    except Exception as e:
        logger.error(f"[{agent.agent_id}] Error deactivating persistence: {e}")


def ensure_unstoppable(agent):
    """
    Ensure agent is unstoppable - verify persistence is active
    
    Args:
        agent: SwarmAgent instance
        
    Returns:
        bool: True if agent is unstoppable, False otherwise
    """
    if not hasattr(agent, 'persistence_manager') or agent.persistence_manager is None:
        return False
    
    try:
        # Check if health monitoring is running
        if not agent.persistence_manager.is_running:
            agent.persistence_manager.start_health_monitoring()
            logger.info(f"[{agent.agent_id}] 🔧 Restarted health monitoring")
        
        return True
    except Exception as e:
        logger.error(f"[{agent.agent_id}] Error ensuring unstoppable: {e}")
        return False


def get_persistence_status(agent):
    """
    Get current persistence status of an agent
    
    Args:
        agent: SwarmAgent instance
        
    Returns:
        dict: Persistence status information
    """
    status = {
        'agent_id': agent.agent_id,
        'persistence_available': PERSISTENCE_AVAILABLE,
        'manager_initialized': hasattr(agent, 'persistence_manager') and agent.persistence_manager is not None,
        'health_monitoring_running': False,
        'persistence_installed': False
    }
    
    if status['manager_initialized']:
        try:
            status['health_monitoring_running'] = agent.persistence_manager.is_running
            # Note: persistence installation status would need to be tracked by PersistenceManager
            status['persistence_installed'] = True  # Assuming installed if manager exists
        except Exception as e:
            logger.error(f"[{agent.agent_id}] Error getting persistence status: {e}")
    
    return status