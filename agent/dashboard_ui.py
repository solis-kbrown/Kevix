"""
ServerRoot.net Dashboard & Monitoring UI
Real-time monitoring and control interface for autonomous swarm defense system
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    host: str = "0.0.0.0"
    port: int = 8080
    refresh_interval: int = 2  # seconds
    max_history_points: int = 1000
    enable_alerts: bool = True
    enable_realtime: bool = True

@dataclass
class SystemMetrics:
    """System-wide metrics"""
    total_agents: int = 0
    active_agents: int = 0
    compromised_hosts: int = 0
    network_segments: int = 0
    total_scans: int = 0
    active_exploits: int = 0
    successful_deployments: int = 0
    failed_deployments: int = 0
    uptime_seconds: float = 0.0
    avg_cpu_usage: float = 0.0
    avg_memory_usage: float = 0.0

@dataclass
class AgentStatus:
    """Individual agent status"""
    agent_id: str
    hostname: str
    ip_address: str
    platform: str
    status: str  # active, offline, degraded, compromised
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    last_heartbeat: str
    uptime: float
    mission: str
    targets_scanned: int
    exploits_used: int
    deployments_completed: int

class DashboardUI:
    """Main dashboard UI class"""
    
    def __init__(self, config: DashboardConfig):
        self.config = config
        self.system_metrics = SystemMetrics()
        self.agents: Dict[str, AgentStatus] = {}
        self.alerts: List[Dict] = []
        self.metrics_history: List[Dict] = []
        self.start_time = time.time()
        self._running = False
        
        # HTML templates
        self._generate_html_templates()
    
    def _generate_html_templates(self):
        """Generate HTML templates for the dashboard"""
        self.base_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ServerRoot.net - Autonomous Swarm Defense Dashboard</title>
    <style>
        *{{margin: 0; padding: 0; box-sizing: border-box;}}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0e27, #1a1f3a);
            color: #e0e6ed;
            min-height: 100vh;
        }}
        
        .dashboard {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            padding: 20px 0;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            color: #8899aa;
            font-size: 1.1em;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .metric-card {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(0,212,255,0.2);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s;
        }}
        
        .metric-card:hover {{
            border-color: rgba(0,212,255,0.5);
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0,212,255,0.2);
        }}
        
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #00d4ff;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            color: #8899aa;
            font-size: 0.9em;
        }}
        
        .main-content {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .panel {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(0,212,255,0.2);
            border-radius: 10px;
            padding: 20px;
        }}
        
        .panel-header {{
            font-size: 1.3em;
            color: #00ff88;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(0,255,136,0.2);
        }}
        
        .agents-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .agents-table th, .agents-table td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        
        .agents-table th {{
            color: #00ff88;
            font-weight: bold;
        }}
        
        .status-active {{color: #00ff88;}}
        .status-offline {{color: #ff4444;}}
        .status-degraded {{color: #ffaa00;}}
        .status-compromised {{color: #ff0066;}}
        
        .alert-item {{
            background: rgba(255,68,68,0.1);
            border-left: 3px solid #ff4444;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
        }}
        
        .alert-warning {{
            background: rgba(255,170,0,0.1);
            border-left-color: #ffaa00;
        }}
        
        .alert-info {{
            background: rgba(0,212,255,0.1);
            border-left-color: #00d4ff;
        }}
        
        .chart-container {{
            height: 200px;
            margin-top: 15px;
            position: relative;
        }}
        
        .refresh-info {{
            text-align: center;
            color: #8899aa;
            padding: 15px;
            font-size: 0.9em;
        }}
        
        @keyframes pulse {{
            0% {{opacity: 1;}}
            50% {{opacity: 0.5;}}
            100% {{opacity: 1;}}
        }}
        
        .live-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00ff88;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>ServerRoot.net</h1>
            <div class="subtitle"><span class="live-indicator"></span>Autonomous Swarm Defense System</div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" id="total-agents">{total_agents}</div>
                <div class="metric-label">Total Agents</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="active-agents">{active_agents}</div>
                <div class="metric-label">Active Agents</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="compromised-hosts">{compromised_hosts}</div>
                <div class="metric-label">Compromised Hosts</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="network-segments">{network_segments}</div>
                <div class="metric-label">Network Segments</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="successful-deployments">{successful_deployments}</div>
                <div class="metric-label">Successful Deployments</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="uptime">{uptime}</div>
                <div class="metric-label">System Uptime</div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="panel">
                <div class="panel-header">Active Agents</div>
                <table class="agents-table">
                    <thead>
                        <tr>
                            <th>Agent ID</th>
                            <th>Hostname</th>
                            <th>IP Address</th>
                            <th>Platform</th>
                            <th>Status</th>
                            <th>CPU</th>
                            <th>Memory</th>
                            <th>Mission</th>
                        </tr>
                    </thead>
                    <tbody id="agents-table-body">
                        {agents_table_content}
                    </tbody>
                </table>
            </div>
            
            <div class="panel">
                <div class="panel-header">System Metrics</div>
                <div class="chart-container">
                    <canvas id="metricsChart"></canvas>
                </div>
                
                <div class="panel-header" style="margin-top: 30px;">Recent Alerts</div>
                <div id="alerts-container">
                    {alerts_content}
                </div>
            </div>
        </div>
        
        <div class="panel">
            <div class="panel-header">Detailed Operations Summary</div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; text-align: center;">
                <div>
                    <div class="metric-value" style="font-size: 1.5em;">{total_scans}</div>
                    <div class="metric-label">Total Scans</div>
                </div>
                <div>
                    <div class="metric-value" style="font-size: 1.5em;">{active_exploits}</div>
                    <div class="metric-label">Active Exploits</div>
                </div>
                <div>
                    <div class="metric-value" style="font-size: 1.5em; color: #00ff88;">{successful_deployments}</div>
                    <div class="metric-label">Deployments</div>
                </div>
                <div>
                    <div class="metric-value" style="font-size: 1.5em; color: #ff4444;">{failed_deployments}</div>
                    <div class="metric-label">Failures</div>
                </div>
                <div>
                    <div class="metric-value" style="font-size: 1.5em;">{avg_cpu_usage:.1f}%</div>
                    <div class="metric-label">Avg CPU</div>
                </div>
                <div>
                    <div class="metric-value" style="font-size: 1.5em;">{avg_memory_usage:.1f}%</div>
                    <div class="metric-label">Avg Memory</div>
                </div>
            </div>
        </div>
        
        <div class="refresh-info">
            Last updated: {last_updated} | Auto-refresh: {refresh_interval}s | {total_agents} agents reporting
        </div>
    </div>
    
    <script>
        // Chart configuration
        const ctx = document.getElementById('metricsChart').getContext('2d');
        const metricsChart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {chart_labels},
                datasets: [
                    {{
                        label: 'Active Agents',
                        data: {chart_active_agents},
                        borderColor: '#00ff88',
                        backgroundColor: 'rgba(0, 255, 136, 0.1)',
                        fill: true,
                        tension: 0.4
                    }},
                    {{
                        label: 'Compromised Hosts',
                        data: {chart_compromised_hosts},
                        borderColor: '#ff0066',
                        backgroundColor: 'rgba(255, 0, 102, 0.1)',
                        fill: true,
                        tension: 0.4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        labels: {{
                            color: '#8899aa'
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{
                            color: '#667788'
                        }},
                        grid: {{
                            color: 'rgba(255,255,255,0.05)'
                        }}
                    }},
                    y: {{
                        ticks: {{
                            color: '#667788'
                        }},
                        grid: {{
                            color: 'rgba(255,255,255,0.05)'
                        }}
                    }}
                }}
            }}
        }});
        
        // Auto-refresh
        setTimeout(function() {{
            location.reload();
        }}, {refresh_interval} * 1000);
    </script>
</body>
</html>"""
    
    def update_agent_status(self, status: AgentStatus):
        """Update individual agent status"""
        self.agents[status.agent_id] = status
        self._recalculate_system_metrics()
    
    def _recalculate_system_metrics(self):
        """Recalculate system-wide metrics from agent status"""
        active_count = sum(1 for agent in self.agents.values() if agent.status == "active")
        
        self.system_metrics.total_agents = len(self.agents)
        self.system_metrics.active_agents = active_count
        self.system_metrics.compromised_hosts = sum(1 for agent in self.agents.values() 
                                                    if agent.status == "compromised")
        self.system_metrics.uptime_seconds = time.time() - self.start_time
        
        # Calculate averages
        if self.agents:
            self.system_metrics.avg_cpu_usage = sum(agent.cpu_usage for agent in self.agents.values()) / len(self.agents)
            self.system_metrics.avg_memory_usage = sum(agent.memory_usage for agent in self.agents.values()) / len(self.agents)
        
        # Store history
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.metrics_history.append({
            'timestamp': timestamp,
            'active_agents': self.system_metrics.active_agents,
            'compromised_hosts': self.system_metrics.compromised_hosts,
            'total_agents': self.system_metrics.total_agents
        })
        
        # Limit history size
        if len(self.metrics_history) > self.config.max_history_points:
            self.metrics_history = self.metrics_history[-self.config.max_history_points:]
    
    def add_alert(self, level: str, message: str, agent_id: Optional[str] = None):
        """Add an alert to the system"""
        alert = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'level': level,
            'message': message,
            'agent_id': agent_id
        }
        self.alerts.insert(0, alert)
        
        # Limit alerts
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]
        
        logger.warning(f"ALERT [{level}]: {message}")
    
    def generate_dashboard_html(self) -> str:
        """Generate the complete dashboard HTML"""
        # Format uptime
        uptime_hours = int(self.system_metrics.uptime_seconds // 3600)
        uptime_minutes = int((self.system_metrics.uptime_seconds % 3600) // 60)
        uptime_str = f"{uptime_hours}h {uptime_minutes}m"
        
        # Generate agents table content
        agents_table_content = ""
        for agent in sorted(self.agents.values(), key=lambda x: x.agent_id):
            status_class = f"status-{agent.status}"
            agents_table_content += f"""
                <tr>
                    <td style="font-family: monospace;">{agent.agent_id[:12]}...</td>
                    <td>{agent.hostname}</td>
                    <td style="font-family: monospace;">{agent.ip_address}</td>
                    <td>{agent.platform}</td>
                    <td class="{status_class}">{agent.status.upper()}</td>
                    <td>{agent.cpu_usage:.1f}%</td>
                    <td>{agent.memory_usage:.1f}%</td>
                    <td>{agent.mission}</td>
                </tr>
            """
        
        if not self.agents:
            agents_table_content = '<tr><td colspan="8" style="text-align: center; color: #8899aa; padding: 40px;">No agents currently reporting. System is initializing...</td></tr>'
        
        # Generate alerts content
        alerts_content = ""
        for alert in self.alerts[:10]:
            alert_class = "alert-warning" if alert['level'] == 'warning' else "alert-info"
            agent_info = f"[{alert['agent_id'][:8]}...]" if alert['agent_id'] else ""
            alerts_content += f"""
                <div class="alert-item {alert_class}">
                    <div style="font-size: 0.85em; color: #8899aa;">{alert['timestamp']} {agent_info}</div>
                    <div>{alert['message']}</div>
                </div>
            """
        
        if not self.alerts:
            alerts_content = '<div style="text-align: center; color: #8899aa; padding: 20px;">No alerts</div>'
        
        # Prepare chart data
        chart_labels = [h['timestamp'] for h in self.metrics_history[-20:]]
        chart_activeagents = [h['active_agents'] for h in self.metrics_history[-20:]]
        chart_compromisedhosts = [h['compromised_hosts'] for h in self.metrics_history[-20:]]
        
        # Build HTML
        html = self.base_template.format(
            total_agents=self.system_metrics.total_agents,
            active_agents=self.system_metrics.active_agents,
            compromised_hosts=self.system_metrics.compromised_hosts,
            network_segments=self.system_metrics.network_segments,
            successful_deployments=self.system_metrics.successful_deployments,
            uptime=uptime_str,
            avg_cpu_usage=self.system_metrics.avg_cpu_usage,
            avg_memory_usage=self.system_metrics.avg_memory_usage,
            total_scans=self.system_metrics.total_scans,
            active_exploits=self.system_metrics.active_exploits,
            failed_deployments=self.system_metrics.failed_deployments,
            agents_table_content=agents_table_content,
            alerts_content=alerts_content,
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            refresh_interval=self.config.refresh_interval,
            chart_labels=json.dumps(chart_labels),
            chart_active_agents=json.dumps(chart_activeagents),
            chart_compromised_hosts=json.dumps(chart_compromisedhosts)
        )
        
        return html
    
    def get_api_data(self) -> Dict:
        """Get API data for programmatic access"""
        return {
            'system_metrics': asdict(self.system_metrics),
            'agents': {agent_id: asdict(agent) for agent_id, agent in self.agents.items()},
            'alerts': self.alerts,
            'metrics_history': self.metrics_history,
            'last_updated': datetime.now().isoformat()
        }
    
    async def start_dashboard_server(self):
        """Start the dashboard HTTP server"""
        import aiohttp.web
        
        self._running = True
        app = aiohttp.web.Application()
        
        # Routes
        app.router.add_get('/', self._handle_dashboard)
        app.router.add_get('/api/data', self._handle_api)
        app.router.add_get('/api/health', self._handle_health)
        
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        
        site = aiohttp.web.TCPSite(runner, self.config.host, self.config.port)
        await site.start()
        
        logger.info(f"Dashboard UI started at http://{self.config.host}:{self.config.port}")
        logger.info(f"API endpoint: http://{self.config.host}:{self.config.port}/api/data")
        
        return runner
    
    async def _handle_dashboard(self, request):
        """Handle dashboard page request"""
        html = self.generate_dashboard_html()
        return aiohttp.web.Response(text=html, content_type='text/html')
    
    async def _handle_api(self, request):
        """Handle API data request"""
        data = self.get_api_data()
        return aiohttp.web.Response(text=json.dumps(data, indent=2), content_type='application/json')
    
    async def _handle_health(self, request):
        """Handle health check request"""
        return aiohttp.web.Response(text='{"status": "healthy"}', content_type='application/json')
    
    async def stop_dashboard_server(self, runner):
        """Stop the dashboard server"""
        await runner.cleanup()
        self._running = False
        logger.info("Dashboard UI stopped")

class WebDashboardServer:
    """Simple web dashboard server"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.dashboard = None
        self.runner = None
    
    def initialize(self, dashboard: DashboardUI):
        """Initialize with dashboard instance"""
        self.dashboard = dashboard
    
    async def start(self):
        """Start the web server"""
        if self.dashboard:
            self.runner = await self.dashboard.start_dashboard_server()
            return True
        return False
    
    async def stop(self):
        """Stop the web server"""
        if self.runner and self.dashboard:
            await self.dashboard.stop_dashboard_server(self.runner)

# Convenience functions
def create_dashboard() -> DashboardUI:
    """Create a new dashboard instance"""
    config = DashboardConfig()
    return DashboardUI(config)

def create_mock_agents(count: int = 5) -> List[AgentStatus]:
    """Create mock agent data for testing"""
    mock_agents = []
    platforms = ['Windows', 'Linux', 'macOS']
    missions = ['Scanning', 'Exploiting', 'Deploying', 'Monitoring', 'Patrolling']
    statuses = ['active', 'active', 'active', 'degraded', 'compromised']
    
    for i in range(count):
        agent = AgentStatus(
            agent_id=f"agent_{hashlib.md5(f'agent{i}'.encode()).hexdigest()}",
            hostname=f"host-{i:03d}",
            ip_address=f"192.168.1.{100 + i}",
            platform=platforms[i % len(platforms)],
            status=statuses[i % len(statuses)],
            cpu_usage=20.0 + (i * 5.0),
            memory_usage=40.0 + (i * 3.0),
            disk_usage=50.0 + (i * 2.0),
            network_latency=5.0 + (i * 1.5),
            last_heartbeat=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            uptime=3600.0 * (i + 1),
            mission=missions[i % len(missions)],
            targets_scanned=10 * (i + 1),
            exploits_used=5 * (i + 1),
            deployments_completed=3 * (i + 1)
        )
        mock_agents.append(agent)
    
    return mock_agents

if __name__ == "__main__":
    # Test the dashboard with mock data
    async def main():
        print("🚀 ServerRoot.net Dashboard UI - Initializing...")
        
        # Create dashboard
        dashboard = create_dashboard()
        
        # Add some sample alerts
        dashboard.add_alert("warning", "Agent agent_xxx experiencing high CPU usage", "agent_xxx")
        dashboard.add_alert("info", "New agent joined the swarm: agent_yyy", "agent_yyy")
        dashboard.add_alert("warning", "Network latency detected in segment 192.168.2.0/24", None)
        
        # Add mock agents
        mock_agents = create_mock_agents(8)
        for agent in mock_agents:
            dashboard.update_agent_status(agent)
        
        # Start server
        runner = await dashboard.start_dashboard_server()
        
        # Generate HTML file
        html_content = dashboard.generate_dashboard_html()
        with open('/workspace/index.html', 'w') as f:
            f.write(html_content)
        
        print(f"✅ Dashboard UI running at http://{dashboard.config.host}:{dashboard.config.port}")
        print(f"✅ Static HTML saved to /workspace/index.html")
        print(f"✅ Monitoring {len(dashboard.agents)} agents")
        print(f"✅ Press Ctrl+C to stop")
        
        try:
            # Keep running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down dashboard...")
            await dashboard.stop_dashboard_server(runner)
    
    asyncio.run(main())