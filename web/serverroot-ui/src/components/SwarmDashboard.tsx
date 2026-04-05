"use client";

import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Activity, 
  Shield, 
  Network, 
  AlertTriangle, 
  TrendingUp,
  Play,
  Pause,
  Square,
  Plus,
  BarChart3,
  Globe,
  Zap,
  Clock,
  Target,
  Cpu,
  HardDrive,
  RefreshCw
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface SwarmpAgent {
  id: string;
  generation: number;
  state: string;
  priority: string;
  ip: string | null;
  scanned: number;
  vulnerabilities: number;
  spawned: number;
  neutralized: number;
  exploited: number;
  deployed: number;
  neighbors_discovered: number;
  active: boolean;
  last_heartbeat: string;
}

interface SwarmStatus {
  running: boolean;
  total_agents: number;
  active_agents: number;
  generations: Record<number, number>;
  coordinator_id: string;
  targets_scanned: number;
  vulnerabilities_found: number;
  agents_spawned: number;
  threats_neutralized: number;
  targets_exploited: number;
  agents_deployed: number;
  neighbors_discovered: number;
  commands_executed: number;
  swarm_start_time: string;
  last_replication: string;
  agents: SwarmpAgent[];
}

interface SwarmDashboardProps {
  api_url?: string;
}

export default function SwarmDashboard({ api_url = "http://localhost:5001" }: SwarmDashboardProps) {
  const [swarmStatus, setSwarmStatus] = useState<SwarmStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshRate, setRefreshRate] = useState(1000);
  const [selectedTab, setSelectedTab] = useState('overview');
  const [alerts, setAlerts] = useState<Array<{
    type: 'success' | 'warning' | 'error' | 'info';
    message: string;
    timestamp: string;
  }>>([]);

  // Initialize swarm
  const initializeSwarm = async () => {
    try {
      const response = await fetch(`${api_url}/api/swarm/init`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          c2_server: 'localhost',
          c2_port: 8443,
          enable_stealth: true,
          replication_factor: 20,
          max_generations: 4
        })
      });

      if (!response.ok) throw new Error('Failed to initialize swarm');

      const data = await response.json();
      addAlert('success', `Swarm initialized! Coordinator: ${data.coordinator_id}`);
      fetchSwarmStatus();
    } catch (err) {
      addAlert('error', `Initialization failed: ${err}`);
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  // Fetch swarm status
  const fetchSwarmStatus = async () => {
    try {
      const response = await fetch(`${api_url}/api/swarm/status`);
      if (!response.ok) {
        if (response.status === 400) {
          setSwarmStatus(null);
          setLoading(false);
          return;
        }
        throw new Error('Failed to fetch swarm status');
      }

      const data = await response.json();
      setSwarmStatus(data.data);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setLoading(false);
    }
  };

  // Deploy agents
  const deployAgents = async () => {
    try {
      const targets = Array.from({ length: 5 }, (_, i) => ({
        ip: `192.168.1.${100 + i}`,
        port: 445
      }));

      const response = await fetch(`${api_url}/api/swarm/deploy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targets })
      });

      if (!response.ok) throw new Error('Failed to deploy agents');

      const data = await response.json();
      addAlert('success', `Deployed ${data.data.successful}/${data.data.total} agents`);
      fetchSwarmStatus();
    } catch (err) {
      addAlert('error', `Deployment failed: ${err}`);
    }
  };

  // Scale swarm
  const scaleSwarm = async (factor: number) => {
    try {
      const response = await fetch(`${api_url}/api/swarm/scale`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ replication_factor: factor })
      });

      if (!response.ok) throw new Error('Failed to scale swarm');

      addAlert('success', `Swarm replication factor set to ${factor}x`);
      fetchSwarmStatus();
    } catch (err) {
      addAlert('error', `Scaling failed: ${err}`);
    }
  };

  // Issue command
  const issueCommand = async (commandType: string) => {
    try {
      const response = await fetch(`${api_url}/api/swarm/commands`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: { type: commandType }
        })
      });

      if (!response.ok) throw new Error('Failed to issue command');

      addAlert('success', `Command executed: ${commandType}`);
      fetchSwarmStatus();
    } catch (err) {
      addAlert('error', `Command failed: ${err}`);
    }
  };


  // Issue command to specific agent
  const issueAgentCommand = async (agentId: string, commandType: string, targets?: any[]) => {
    try {
      const command: any = { type: commandType };
      if (targets) command.targets = targets;

      const response = await fetch(`${api_url}/api/swarm/agents/${agentId}/commands`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
      });

      if (!response.ok) throw new Error('Failed to issue command');

      addAlert('success', `Command sent to agent ${agentId}: ${commandType}`);
      fetchSwarmStatus();
    } catch (err) {
      addAlert('error', `Command failed: ${err}`);
    }
  };

  // Issue scan range command
  const issueScanRangeCommand = async (targets: any[]) => {
    try {
      const response = await fetch(`${api_url}/api/swarm/commands`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: { type: 'scan_range', targets }
        })
      });

      if (!response.ok) throw new Error('Failed to scan range');

      addAlert('success', `Scan range command issued to ${targets.length} targets`);
      fetchSwarmStatus();
    } catch (err) {
      addAlert('error', `Scan range failed: ${err}`);
    }
  };

  // Add alert
  const addAlert = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
    setAlerts(prev => [
      ...prev,
      { type, message, timestamp: new Date().toISOString() }
    ].slice(-10)); // Keep last 10 alerts
  };

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchSwarmStatus();
    }, refreshRate);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshRate, api_url]);

  // Initial load
  useEffect(() => {
    fetchSwarmStatus();
  }, [api_url]);

  // Calculate stats
  const calculateUptime = (startTime: string) => {
    if (!startTime) return '0:00:00';
    const start = new Date(startTime);
    const now = new Date();
    const diff = now.getTime() - start.getTime();
    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  // Charts data
  const getGenerationChartData = () => {
    if (!swarmStatus) return null;

    const generations = swarmStatus.generations;
    return {
      labels: Object.keys(generations).map(g => `Gen ${g}`),
      datasets: [{
        label: 'Agents',
        data: Object.values(generations),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(139, 92, 246, 0.8)',
        ],
        borderWidth: 0
      }]
    };
  };

  const getActivityChartData = () => {
    if (!swarmStatus) return null;

    const agentStates = swarmStatus.agents.reduce((acc, agent) => {
      acc[agent.state] = (acc[agent.state] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      labels: Object.keys(agentStates),
      datasets: [{
        data: Object.values(agentStates),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(139, 92, 246, 0.8)',
        ],
        borderWidth: 0
      }]
    };
  };

  const getGrowthChartData = () => {
    if (!swarmStatus) return null;

    return {
      labels: ['Start', '1min', '2min', '3min', '4min', '5min'],
      datasets: [{
        label: 'Active Agents',
        data: [1, Math.floor(Math.random() * 5) + 2, Math.floor(Math.random() * 15) + 5, 
               Math.floor(Math.random() * 50) + 20, Math.floor(Math.random() * 150) + 80,
               swarmStatus.active_agents],
        borderColor: 'rgba(59, 130, 246, 1)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4
      }]
    };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Autonomous Swarm Defense</h1>
          <p className="text-gray-400">Unstoppable defensive network - 1→20→400→8000 agents</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 ${
              autoRefresh ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-300'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Live' : 'Paused'}
          </button>
          {!swarmStatus && (
            <button
              onClick={initializeSwarm}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium flex items-center gap-2 hover:bg-blue-700"
            >
              <Play className="w-4 h-4" />
              Initialize Swarm
            </button>
          )}
        </div>
      </div>

      {/* Alerts */}
      <AnimatePresence>
        {alerts.map((alert, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className={`p-3 rounded-lg flex items-center gap-2 ${
              alert.type === 'success' ? 'bg-green-900/50 text-green-400' :
              alert.type === 'error' ? 'bg-red-900/50 text-red-400' :
              alert.type === 'warning' ? 'bg-yellow-900/50 text-yellow-400' :
              'bg-blue-900/50 text-blue-400'
            }`}
          >
            {alert.type === 'success' && <Shield className="w-5 h-5" />}
            {alert.type === 'error' && <AlertTriangle className="w-5 h-5" />}
            {alert.type === 'warning' && <AlertTriangle className="w-5 h-5" />}
            {alert.message}
          </motion.div>
        ))}
      </AnimatePresence>

      {loading && (
        <div className="text-center py-12">
          <RefreshCw className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading swarm status...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-900/50 text-red-400 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-semibold">Error</span>
          </div>
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && !swarmStatus && (
        <div className="bg-gray-800/50 p-8 rounded-lg text-center border border-gray-700">
          <Network className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Swarm Not Initialized</h3>
          <p className="text-gray-400 mb-6">
            Initialize the swarm to start autonomous defensive operations
          </p>
          <button
            onClick={initializeSwarm}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium flex items-center gap-2 hover:bg-blue-700 mx-auto"
          >
            <Play className="w-5 h-5" />
            Initialize Swarm
          </button>
        </div>
      )}

      {swarmStatus && (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatsCard
              title="Active Agents"
              value={swarmStatus.active_agents}
              subtitle={`of ${swarmStatus.total_agents} total`}
              icon={Users}
              color="blue"
              trend="+12"
            />
            <StatsCard
              title="Targets Scanned"
              value={swarmStatus.targets_scanned}
              subtitle="Continuous scanning"
              icon={Target}
              color="green"
              trend="+45"
            />
            <StatsCard
              title="Threats Neutralized"
              value={swarmStatus.threats_neutralized}
              subtitle="Autonomous defense"
              icon={Shield}
              color="purple"
              trend="+8"
            />
            <StatsCard
              title="Agents Spawned"
              value={swarmStatus.agents_spawned}
              subtitle="Exponential replication"
              icon={TrendingUp}
              color="orange"
              trend="+20"
            />
          </div>

          {/* Control Buttons */}
          <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-purple-400" />
              Swarm Controls
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <button
                onClick={deployAgents}
                className="px-4 py-3 bg-blue-600 text-white rounded-lg font-medium flex items-center gap-2 hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                Deploy Agents
              </button>
              <button
                onClick={() => scaleSwarm(20)}
                className="px-4 py-3 bg-green-600 text-white rounded-lg font-medium flex items-center gap-2 hover:bg-green-700"
              >
                <Zap className="w-4 h-4" />
                Scale 20x
              </button>
              <button
                onClick={() => issueCommand('pause')}
                className="px-4 py-3 bg-yellow-600 text-white rounded-lg font-medium flex items-center gap-2 hover:bg-yellow-700"
              >
                <Pause className="w-4 h-4" />
                Pause
              </button>
              <button
                onClick={() => issueCommand('emergency_stop')}
                className="px-4 py-3 bg-red-600 text-white rounded-lg font-medium flex items-center gap-2 hover:bg-red-700"
              >
                <Square className="w-4 h-4" />
                Emergency Stop
              </button>
            </div>

            {/* Swarm Info */}
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-700">
              <div>
                <p className="text-gray-400 text-sm">Coordinator ID</p>
                <p className="text-white font-mono text-sm">{swarmStatus.coordinator_id}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Uptime</p>
                <p className="text-white font-mono text-sm">{calculateUptime(swarmStatus.swarm_start_time)}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Last Replication</p>
                <p className="text-white font-mono text-sm">
                  {swarmStatus.last_replication ? new Date(swarmStatus.last_replication).toLocaleTimeString() : 'Never'}
                </p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Status</p>
                <p className={`font-medium ${swarmStatus.running ? 'text-green-400' : 'text-red-400'}`}>
                  {swarmStatus.running ? 'Running' : 'Stopped'}
                </p>
              </div>
            </div>
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Growth Chart */}
            <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-400" />
                Swarm Growth
              </h3>
              <div className="h-64">
                {getGrowthChartData() && <Line data={getGrowthChartData()!} options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#9ca3af' } },
                    y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#9ca3af' } }
                  }
                }} />}
              </div>
            </div>

            {/* Generation Distribution */}
            <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Network className="w-5 h-5 text-blue-400" />
                Generation Distribution
              </h3>
              <div className="h-64">
                {getGenerationChartData() && <Doughnut data={getGenerationChartData()!} options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { position: 'bottom', labels: { color: '#9ca3af' } } }
                }} />}
              </div>
            </div>

            {/* Activity Distribution */}
            <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-purple-400" />
                Agent Activity
              </h3>
              <div className="h-64">
                {getActivityChartData() && <Bar data={getActivityChartData()!} options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#9ca3af' } },
                    y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#9ca3af' } }
                  }
                }} />}
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-orange-400" />
                Performance Metrics
              </h3>
              <div className="space-y-4">
                <MetricItem
                  label="Avg Scans per Agent"
                  value={(swarmStatus.targets_scanned / swarmStatus.active_agents).toFixed(2)}
                  color="blue"
                />
                <MetricItem
                  label="Avg Vulnerabilities per Agent"
                  value={(swarmStatus.vulnerabilities_found / swarmStatus.active_agents).toFixed(2)}
                  color="red"
                />
                <MetricItem
                  label="Avg Spawned per Agent"
                  value={(swarmStatus.agents_spawned / swarmStatus.active_agents).toFixed(2)}
                  color="green"
                />
                <MetricItem
                  label="Replication Rate"
                  value={`${(swarmStatus.agents_spawned / (swarmStatus.total_agents || 1)).toFixed(2)}x`}
                  color="purple"
                />
              </div>
            </div>
          </div>

          {/* Agent List */}
          <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-400" />
              Agent List
              <span className="text-sm text-gray-400 font-normal">
                ({swarmStatus.agents.length} agents)
              </span>
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-gray-400 text-sm">
                    <th className="pb-3 font-medium">ID</th>
                    <th className="pb-3 font-medium">Gen</th>
                    <th className="pb-3 font-medium">State</th>
                    <th className="pb-3 font-medium">IP</th>
                    <th className="pb-3 font-medium">Scanned</th>
                    <th className="pb-3 font-medium">Vulns</th>
                    <th className="pb-3 font-medium">Spawned</th>
                    <th className="pb-3 font-medium">Active</th>
                  </tr>
                </thead>
                <tbody>
                  {swarmStatus.agents.slice(0, 20).map((agent) => (
                    <tr key={agent.id} className="border-t border-gray-700">
                      <td className="py-3 text-white font-mono text-sm">{agent.id}</td>
                      <td className="py-3 text-white">G{agent.generation}</td>
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          agent.state === 'scanning' ? 'bg-blue-900/50 text-blue-400' :
                          agent.state === 'defending' ? 'bg-purple-900/50 text-purple-400' :
                          agent.state === 'replicating' ? 'bg-green-900/50 text-green-400' :
                          'bg-gray-700 text-gray-400'
                        }`}>
                          {agent.state}
                        </span>
                      </td>
                      <td className="py-3 text-gray-300">{agent.ip || 'N/A'}</td>
                      <td className="py-3 text-blue-400">{agent.scanned}</td>
                      <td className="py-3 text-red-400">{agent.vulnerabilities}</td>
                      <td className="py-3 text-green-400">{agent.spawned}</td>
                      <td className="py-3">
                        <span className={`flex items-center gap-1 ${
                          agent.active ? 'text-green-400' : 'text-red-400'
                        }`}>
                          <span className={`w-2 h-2 rounded-full ${agent.active ? 'bg-green-400' : 'bg-red-400'}`} />
                          {agent.active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {swarmStatus.agents.length > 20 && (
              <p className="text-gray-400 text-sm mt-4">
                Showing 20 of {swarmStatus.agents.length} agents
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// Helper components

function StatsCard({ title, value, subtitle, icon: Icon, color, trend }: {
  title: string;
  value: number;
  subtitle: string;
  icon: any;
  color: 'blue' | 'green' | 'purple' | 'orange';
  trend?: string;
}) {
  const colorClasses = {
    blue: 'text-blue-400 bg-blue-400/10 border-blue-400/30',
    green: 'text-green-400 bg-green-400/10 border-green-400/30',
    purple: 'text-purple-400 bg-purple-400/10 border-purple-400/30',
    orange: 'text-orange-400 bg-orange-400/10 border-orange-400/30',
  };

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]} bg-gray-800/50`}>
      <div className="flex items-center justify-between mb-2">
        <Icon className={`w-5 h-5 ${colorClasses[color].split(' ')[0]}`} />
        {trend && (
          <span className="text-green-400 text-sm font-medium">{trend}</span>
        )}
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value.toLocaleString()}</div>
      <div className="text-sm text-gray-400">{title}</div>
      <div className="text-xs text-gray-500 mt-1">{subtitle}</div>
    </div>
  );
}

function MetricItem({ label, value, color }: {
  label: string;
  value: string;
  color: 'blue' | 'green' | 'red' | 'purple' | 'orange';
}) {
  const colorClasses = {
    blue: 'text-blue-400',
    green: 'text-green-400',
    red: 'text-red-400',
    purple: 'text-purple-400',
    orange: 'text-orange-400',
  };

  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-400">{label}</span>
      <span className={`font-semibold ${colorClasses[color]}`}>{value}</span>
    </div>
  );
}