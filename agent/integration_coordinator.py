"""
Integration Coordinator - Bridges all critical path components
Connects Monitoring, Communication, and Dashboard systems
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Import critical path components
from agent.monitoring_system import MonitoringSystem, HealthStatus, AlertSeverity
from agent.communication_system import CommunicationSystem, MessageType
from agent.dashboard_ui import DashboardUI, DashboardConfig, AgentStatus, SystemMetrics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationState(Enum):
    """Integration coordinator states"""
    INITIALIZING = "initializing"
    CONNECTING = "connecting"
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    FAILED = "failed"

@dataclass
class IntegrationMetrics:
    """Integration coordinator metrics"""
    uptime: float = 0.0
    messages_processed: int = 0
    alerts_generated: int = 0
    dashboard_updates: int = 0
    last_heartbeat: str = ""
    coordination_errors: int = 0

class IntegrationCoordinator:
    """
    Integrates Monitoring, Communication, and Dashboard systems
    Provides unified interface and data flow between components
    """
    
    def __init__(self, agent_id: str, c2_server: str, c2_port: int = 4444):
        self.agent_id = agent_id
        self.c2_server = c2_server
        self.c2_port = c2_port
        self.state = IntegrationState.INITIALIZING
        self.metrics = IntegrationMetrics()
        self.start_time = time.time()
        
        # Component instances
        self.monitoring_system: Optional[MonitoringSystem] = None
        self.communication_system: Optional[CommunicationSystem] = None
        self.dashboard: Optional[DashboardUI] = None
        
        # Data synchronization
        self.sync_enabled = True
        self.sync_interval = 5.0
        self._sync_task = None
        self._running = False
        
        logger.info(f"IntegrationCoordinator initialized for agent {agent_id}")
    
    async def initialize(self, enable_dashboard: bool = True):
        """Initialize all critical path components"""
        logger.info("🔧 Initializing critical path components...")
        
        try:
            # Initialize Monitoring System
            logger.info("   📊 Initializing Monitoring System...")
            self.monitoring_system = MonitoringSystem(
                agent_id=self.agent_id,
                c2_server=self.c2_server
            )
            # Monitoring system initializes in __init__
            logger.info("   ✅ Monitoring System initialized")
            
            # Initialize Communication System
            logger.info("   📡 Initializing Communication System...")
            self.communication_system = CommunicationSystem(
                agent_id=self.agent_id,
                c2_server=self.c2_server,
                c2_port=self.c2_port
            )
            # Communication system initializes in __init__
            logger.info("   ✅ Communication System initialized")
            
            # Initialize Dashboard (if enabled)
            if enable_dashboard:
                logger.info("   🎨 Initializing Dashboard UI...")
                config = DashboardConfig(
                    host="0.0.0.0",
                    port=8080,
                    refresh_interval=2,
                    max_history_points=100
                )
                self.dashboard = DashboardUI(config)
                logger.info("   ✅ Dashboard UI initialized")
            
            # Setup data synchronization
            self._setup_data_sync()
            
            self.state = IntegrationState.OPERATIONAL
            logger.info("✅ All critical path components initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            self.state = IntegrationState.FAILED
            return False
    
    def _setup_data_sync(self):
        """Setup data synchronization between components"""
        
        # Register monitoring callbacks
        if self.monitoring_system:
            # MonitoringSystem uses add_alert_callback
            self.monitoring_system.add_alert_callback(self._on_alert)
        
        # Register communication callbacks
        if self.communication_system:
            self.communication_system.register_message_handler(MessageType.HEARTBEAT, self._on_heartbeat_message)
            self.communication_system.register_message_handler(MessageType.STATUS_REPORT, self._on_status_message)
            self.communication_system.register_message_handler(MessageType.COMMAND, self._on_command_message)
        
        logger.info("✅ Data synchronization configured")
    
    def _on_health_check(self, status: HealthStatus, metrics: Dict):
        """Handle health check results from monitoring system"""
        # This will be called manually during sync
        pass
    
    def _on_alert(self, level: AlertSeverity, message: str, source: str):
        """Handle alerts from monitoring system"""
        # Forward to dashboard
        if self.dashboard:
            self.dashboard.add_alert(level.value, message, source)
            self.metrics.alerts_generated += 1
        
        # Forward via communication if critical
        if level in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            if self.communication_system:
                asyncio.create_task(
                    self.communication_system.send_message(
                        MessageType.ALERT,
                        {
                            'level': level.value,
                            'message': message,
                            'source': source,
                            'timestamp': datetime.now().isoformat()
                        }
                    )
                )
    
    async def _on_heartbeat_message(self, message: Dict):
        """Handle heartbeat messages from communication system"""
        self.metrics.last_heartbeat = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.debug(f"❤️  Heartbeat received from {message.get('sender_id')}")
    
    async def _on_status_message(self, message: Dict):
        """Handle status update messages from communication system"""
        sender_id = message.get('sender_id')
        status_data = message.get('payload', {})
        
        # Update dashboard with remote agent status
        if self.dashboard and status_data:
            agent_status = AgentStatus(
                agent_id=sender_id,
                hostname=status_data.get('hostname', 'unknown'),
                ip_address=status_data.get('ip_address', '0.0.0.0'),
                platform=status_data.get('platform', 'unknown'),
                status=status_data.get('status', 'unknown'),
                cpu_usage=status_data.get('cpu_usage', 0.0),
                memory_usage=status_data.get('memory_usage', 0.0),
                disk_usage=status_data.get('disk_usage', 0.0),
                network_latency=status_data.get('network_latency', 0.0),
                last_heartbeat=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                uptime=status_data.get('uptime', 0.0),
                mission=status_data.get('mission', 'unknown'),
                targets_scanned=status_data.get('targets_scanned', 0),
                exploits_used=status_data.get('exploits_used', 0),
                deployments_completed=status_data.get('deployments_completed', 0)
            )
            self.dashboard.update_agent_status(agent_status)
        
        self.metrics.messages_processed += 1
    
    async def _on_command_message(self, message: Dict):
        """Handle command messages from communication system"""
        command = message.get('payload', {}).get('command')
        logger.info(f"📨 Command received: {command}")
        
        # Process command (extend as needed)
        if command == 'status':
            await self.send_status_report()
        elif command == 'heartbeat':
            await self.send_heartbeat()
        elif command == 'shutdown':
            logger.warning("⚠️  Shutdown command received")
            await self.shutdown()
    
    async def start_synchronization(self):
        """Start automatic data synchronization"""
        if not self._running:
            self._running = True
            self._sync_task = asyncio.create_task(self._sync_loop())
            logger.info("🔄 Data synchronization started")
    
    async def stop_synchronization(self):
        """Stop data synchronization"""
        if self._running:
            self._running = False
            if self._sync_task:
                self._sync_task.cancel()
                try:
                    await self._sync_task
                except asyncio.CancelledError:
                    pass
            logger.info("⏹️  Data synchronization stopped")
    
    async def _sync_loop(self):
        """Main synchronization loop"""
        while self._running:
            try:
                if self.sync_enabled:
                    await self._perform_sync()
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"❌ Sync error: {e}")
                self.metrics.coordination_errors += 1
                await asyncio.sleep(1)
    
    async def _perform_sync(self):
        """Perform data synchronization"""
        # Collect health metrics
        if self.monitoring_system:
            health_status = self.monitoring_system.get_health_status()
            metrics = self.monitoring_system.get_current_metrics()
            self._update_dashboard_health(metrics)
        
        # Send heartbeat via communication
        if self.communication_system:
            asyncio.create_task(self.send_heartbeat())
        
        # Update metrics
        self.metrics.uptime = time.time() - self.start_time
    
    def _update_dashboard_health(self, metrics: Dict):
        """Update dashboard with health metrics"""
        if self.dashboard:
            agent_status = AgentStatus(
                agent_id=self.agent_id,
                hostname=metrics.get('hostname', 'unknown'),
                ip_address=metrics.get('ip_address', '0.0.0.0'),
                platform=metrics.get('platform', 'unknown'),
                status='active',
                cpu_usage=metrics.get('cpu_percent', 0.0),
                memory_usage=metrics.get('memory_percent', 0.0),
                disk_usage=metrics.get('disk_percent', 0.0),
                network_latency=metrics.get('network_latency', 0.0),
                last_heartbeat=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                uptime=time.time() - self.start_time,
                mission='monitoring',
                targets_scanned=metrics.get('targets_scanned', 0),
                exploits_used=metrics.get('exploits_used', 0),
                deployments_completed=metrics.get('deployments_completed', 0)
            )
            self.dashboard.update_agent_status(agent_status)
    
    async def send_heartbeat(self):
        """Send heartbeat via communication system"""
        if self.communication_system:
            await self.communication_system.send_message(
                MessageType.HEARTBEAT,
                {'timestamp': datetime.now().isoformat()}
            )
    
    async def send_status_report(self):
        """Send status report to C2"""
        if self.communication_system:
            status_report = {
                'state': self.state.value,
                'uptime': self.metrics.uptime,
                'messages_processed': self.metrics.messages_processed,
                'alerts_generated': self.metrics.alerts_generated,
                'dashboard_updates': self.metrics.dashboard_updates,
                'coordination_errors': self.metrics.coordination_errors,
                'health_status': self.monitoring_system.get_health_status().value if self.monitoring_system else 'unknown'
            }
            
            await self.communication_system.send_message(
                MessageType.STATUS_UPDATE,
                status_report
            )
    
    async def get_dashboard_html(self) -> Optional[str]:
        """Get current dashboard HTML"""
        if self.dashboard:
            return self.dashboard.generate_dashboard_html()
        return None
    
    async def get_api_data(self) -> Optional[Dict]:
        """Get current API data"""
        if self.dashboard:
            return self.dashboard.get_api_data()
        return None
    
    async def start_dashboard_server(self):
        """Start dashboard UI server"""
        if self.dashboard:
            return await self.dashboard.start_dashboard_server()
        return None
    
    async def stop_dashboard_server(self, runner):
        """Stop dashboard UI server"""
        if self.dashboard and runner:
            await self.dashboard.stop_dashboard_server(runner)
    
    def add_custom_alert(self, level: str, message: str, source: Optional[str] = None):
        """Add custom alert to dashboard"""
        if self.dashboard:
            self.dashboard.add_alert(level, message, source)
    
    def get_integration_status(self) -> Dict:
        """Get integration coordinator status"""
        return {
            'state': self.state.value,
            'uptime': self.metrics.uptime,
            'messages_processed': self.metrics.messages_processed,
            'alerts_generated': self.metrics.alerts_generated,
            'dashboard_updates': self.metrics.dashboard_updates,
            'coordination_errors': self.metrics.coordination_errors,
            'last_heartbeat': self.metrics.last_heartbeat,
            'monitoring_system_initialized': self.monitoring_system is not None,
            'communication_system_initialized': self.communication_system is not None,
            'dashboard_initialized': self.dashboard is not None
        }
    
    async def shutdown(self):
        """Shutdown all components gracefully"""
        logger.info("🛑 Shutting down Integration Coordinator...")
        
        try:
            # Stop synchronization
            await self.stop_synchronization()
            
            # Stop dashboard
            if self.dashboard:
                logger.info("   Stopping dashboard...")
            
            # Stop communication
            if self.communication_system:
                logger.info("   Stopping communication system...")
            
            # Stop monitoring
            if self.monitoring_system:
                logger.info("   Stopping monitoring system...")
                self.monitoring_system.stop_monitoring()
            
            self.state = IntegrationState.FAILED
            logger.info("✅ Integration Coordinator shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

# Convenience functions
async def create_integration_coordinator(agent_id: str, c2_server: str, c2_port: int = 4444, enable_dashboard: bool = True) -> IntegrationCoordinator:
    """Initialize and start integration coordinator"""
    coordinator = IntegrationCoordinator(agent_id, c2_server, c2_port)
    
    if await coordinator.initialize(enable_dashboard):
        await coordinator.start_synchronization()
        return coordinator
    
    return None

if __name__ == "__main__":
    async def main():
        print("🚀 ServerRoot.net Integration Coordinator - Starting...")
        
        # Create coordinator
        coordinator = await create_integration_coordinator(
            agent_id="test_coordinator_001",
            c2_server="localhost",
            c2_port=4444,
            enable_dashboard=True
        )
        
        if coordinator:
            print("✅ Integration Coordinator operational")
            print(f"📊 Status: {coordinator.get_integration_status()}")
            
            # Add sample alerts
            coordinator.add_custom_alert("info", "Integration Coordinator started", coordinator.agent_id)
            coordinator.add_custom_alert("info", "All systems nominal", coordinator.agent_id)
            
            # Start dashboard server
            try:
                runner = await coordinator.start_dashboard_server()
                print(f"🌐 Dashboard available at http://0.0.0.0:8080")
                
                # Save static dashboard
                html = await coordinator.get_dashboard_html()
                if html:
                    with open('/workspace/integration_dashboard.html', 'w') as f:
                        f.write(html)
                    print("📁 Static dashboard saved to /workspace/integration_dashboard.html")
                
                # Keep running
                print("\n✅ Integration Coordinator is running. Press Ctrl+C to stop.")
                while True:
                    await asyncio.sleep(1)
                    
            except KeyboardInterrupt:
                print("\n🛑 Stopping...")
                await coordinator.shutdown()
        else:
            print("❌ Failed to initialize Integration Coordinator")
    
    asyncio.run(main())