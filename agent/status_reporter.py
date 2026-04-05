"""
Status Reporter - Feeds agent status to dashboard
"""

import json
import time
from typing import Dict, Optional
from datetime import datetime
from agent.dashboard_ui import AgentStatus

class StatusReporter:
    """Reports agent status to dashboard"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.hostname = self._get_hostname()
        self.ip_address = self._get_ip_address()
        self.platform = self._get_platform()
    
    def _get_hostname(self) -> str:
        """Get system hostname"""
        import socket
        try:
            return socket.gethostname()
        except:
            return "unknown"
    
    def _get_ip_address(self) -> str:
        """Get primary IP address"""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"
    
    def _get_platform(self) -> str:
        """Get platform name"""
        import platform
        return platform.system()
    
    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except:
            return 0.0
    
    def _get_memory_usage(self) -> float:
        """Get memory usage percentage"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except:
            return 0.0
    
    def _get_disk_usage(self) -> float:
        """Get disk usage percentage"""
        try:
            import psutil
            return psutil.disk_usage('/').percent
        except:
            return 0.0
    
    def _get_network_latency(self) -> float:
        """Get estimated network latency"""
        # This would be measured via actual network checks
        return 5.0
    
    def generate_status_report(self, agent_metrics: Dict) -> AgentStatus:
        """Generate status report for dashboard"""
        return AgentStatus(
            agent_id=self.agent_id,
            hostname=self.hostname,
            ip_address=self.ip_address,
            platform=self.platform,
            status="active",
            cpu_usage=self._get_cpu_usage(),
            memory_usage=self._get_memory_usage(),
            disk_usage=self._get_disk_usage(),
            network_latency=self._get_network_latency(),
            last_heartbeat=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            uptime=time.time() - agent_metrics.get('start_time', time.time()),
            mission=agent_metrics.get('current_mission', 'autonomous'),
            targets_scanned=agent_metrics.get('targets_scanned', 0),
            exploits_used=agent_metrics.get('targets_exploited', 0),
            deployments_completed=agent_metrics.get('agents_deployed', 0)
        )
    
    def get_system_metrics(self) -> Dict:
        """Get system metrics dictionary"""
        return {
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'platform': self.platform,
            'cpu_percent': self._get_cpu_usage(),
            'memory_percent': self._get_memory_usage(),
            'disk_percent': self._get_disk_usage(),
            'network_latency': self._get_network_latency(),
            'timestamp': datetime.now().isoformat()
        }