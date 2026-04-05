'use client';
import { useState, useEffect, useCallback } from 'react';
import {
  CpuChipIcon,
  ShieldCheckIcon,
  BeakerIcon,
  BugAntIcon,
  ExclamationTriangleIcon,
  ServerIcon,
  SignalIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import StatsCard from './StatsCard';
import {
  fetchSwarmStats,
  fetchSwarmAgents,
  fetchSwarmOperations,
  fetchSwarmIntelligence,
  fetchHealth,
  buildSystemStats,
  operationsToThreats,
  formatUptime,
  statusColor,
  opTypeIcon,
  platformColor,
  healthColor,
} from '@/lib/api';
import { SystemStats, SwarmAgent, SwarmOperation, SwarmIntelligence, Threat } from '@/types';

const EMPTY_STATS: SystemStats = {
  totalAgents: 0, activeAgents: 0, totalVulnerabilities: 0,
  criticalVulnerabilities: 0, totalExploits: 0, activeCampaigns: 0,
  totalThreats: 0, systemUptime: 0, aiResearchReports: 0,
  successRate: 0, swarmHealth: 'initializing', operationsLastHour: 0,
};

export default function Dashboard() {
  const [stats, setStats] = useState<SystemStats>(EMPTY_STATS);
  const [agents, setAgents] = useState<SwarmAgent[]>([]);
  const [operations, setOperations] = useState<SwarmOperation[]>([]);
  const [threats, setThreats] = useState<Threat[]>([]);
  const [intel, setIntel] = useState<SwarmIntelligence | null>(null);
  const [apiStatus, setApiStatus] = useState<'connecting' | 'live' | 'error'>('connecting');
  const [apiUptime, setApiUptime] = useState<number>(0);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [error, setError] = useState<string>('');

  const fetchAll = useCallback(async () => {
    try {
      const [rawStats, rawAgents, rawOps, rawIntel, health] = await Promise.all([
        fetchSwarmStats(),
        fetchSwarmAgents(),
        fetchSwarmOperations(),
        fetchSwarmIntelligence(),
        fetchHealth(),
      ]);

      setStats(buildSystemStats(rawStats, rawIntel));
      setAgents(rawAgents);
      setOperations(rawOps);
      setThreats(operationsToThreats(rawOps));
      setIntel(rawIntel);
      setApiUptime(health.uptime_seconds);
      setApiStatus('live');
      setLastUpdated(new Date());
      setError('');
    } catch (err) {
      setApiStatus('error');
      setError(err instanceof Error ? err.message : 'API unreachable');
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 4000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const statusDot = apiStatus === 'live'
    ? 'bg-green-400 animate-pulse'
    : apiStatus === 'connecting'
    ? 'bg-yellow-400 animate-pulse'
    : 'bg-red-500';

  const statusText = apiStatus === 'live'
    ? `⚡ LIVE — API :5001 · ${formatUptime(apiUptime)} uptime · updated ${lastUpdated.toLocaleTimeString()}`
    : apiStatus === 'connecting'
    ? '⏳ Connecting to API...'
    : `⚠ API Error: ${error}`;

  return (
    <div className="space-y-6">

      {/* Live Status Bar */}
      <div className={`flex items-center justify-between px-4 py-2 rounded-lg border text-xs font-mono ${
        apiStatus === 'live' ? 'bg-green-900/20 border-green-700/40 text-green-400'
        : apiStatus === 'connecting' ? 'bg-yellow-900/20 border-yellow-700/40 text-yellow-400'
        : 'bg-red-900/20 border-red-700/40 text-red-400'
      }`}>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${statusDot}`}></div>
          <span>{statusText}</span>
        </div>
        <div className="flex items-center space-x-3">
          {intel && (
            <span className={`${healthColor(intel.swarm_health)} font-semibold uppercase`}>
              SWARM: {intel.swarm_health}
            </span>
          )}
          <button onClick={fetchAll} className="flex items-center space-x-1 text-gray-500 hover:text-white transition-colors">
            <ArrowPathIcon className="w-3 h-3" />
            <span>refresh</span>
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Active Agents"
          value={stats.activeAgents}
          change={`${stats.totalAgents} total deployed`}
          changeType="increase"
          icon={ServerIcon}
          color="serverroot"
        />
        <StatsCard
          title="Operations / Hour"
          value={stats.operationsLastHour}
          change={`${Math.round(stats.successRate * 100)}% success rate`}
          changeType={stats.successRate > 0.7 ? 'increase' : 'decrease'}
          icon={CpuChipIcon}
          color="cyber-green"
        />
        <StatsCard
          title="Total Exploits"
          value={stats.totalExploits}
          change={`${stats.totalVulnerabilities} vulns found`}
          changeType="increase"
          icon={ShieldCheckIcon}
          color="cyber-red"
        />
        <StatsCard
          title="System Uptime"
          value={formatUptime(stats.systemUptime)}
          change={`v2.0.0-Enterprise`}
          changeType="neutral"
          icon={BeakerIcon}
          color="cyber-yellow"
        />
      </div>

      {/* Intel Bar */}
      {intel && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Leaders', value: intel.capabilities?.roles?.leaders ?? 0, color: 'text-serverroot-400' },
            { label: 'Workers', value: intel.capabilities?.roles?.workers ?? 0, color: 'text-blue-400' },
            { label: 'Platforms', value: intel.capabilities?.platforms?.join(', ') ?? '—', color: 'text-yellow-400' },
            { label: 'Avg Load', value: `${Math.round((intel.average_load ?? 0) * 100)}%`, color: 'text-orange-400' },
          ].map(item => (
            <div key={item.label} className="cyber-card py-3 text-center">
              <p className="text-xs text-gray-500 uppercase tracking-wider">{item.label}</p>
              <p className={`text-lg font-bold mt-1 ${item.color}`}>{item.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Agents + Recent Operations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Live Agents */}
        <div className="lg:col-span-2 cyber-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white flex items-center">
              <ServerIcon className="w-5 h-5 mr-2 text-serverroot-400" />
              Live Agents
            </h2>
            <span className="text-sm text-serverroot-400">{agents.length} online</span>
          </div>
          {agents.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <SignalIcon className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p>No agents registered yet</p>
              <p className="text-xs mt-1">Deploy agents to targets to see them here</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
              {agents.map(agent => (
                <div key={agent.id} className="bg-gray-900/50 rounded-lg p-4 border border-gray-700 hover:border-serverroot-500/50 transition-all duration-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-2 h-2 rounded-full ${agent.status === 'active' ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`}></div>
                      <div>
                        <p className="text-white font-medium font-mono text-sm">{agent.hostname}</p>
                        <p className={`text-xs ${platformColor(agent.platform)}`}>
                          {agent.ip} · {agent.platform} · {agent.role}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${statusColor(agent.status)}`}>
                        {agent.status}
                      </span>
                    </div>
                  </div>
                  <div className="mt-3 grid grid-cols-4 gap-3 text-xs">
                    <div>
                      <p className="text-gray-500">Tasks</p>
                      <p className="text-white font-bold">{agent.tasks_completed}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Load</p>
                      <p className={`font-bold ${agent.load > 0.8 ? 'text-red-400' : 'text-green-400'}`}>
                        {Math.round(agent.load * 100)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Caps</p>
                      <p className="text-gray-300">{agent.capabilities?.length ?? 0}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Seen</p>
                      <p className="text-gray-300">{new Date(agent.last_seen).toLocaleTimeString()}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Live Operations Feed */}
        <div className="cyber-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white flex items-center">
              <SignalIcon className="w-5 h-5 mr-2 text-serverroot-400" />
              Live Feed
            </h2>
            <span className="text-xs text-gray-500">{operations.length} recent</span>
          </div>
          {operations.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p className="text-sm">No operations yet</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              {operations.slice(0, 20).map(op => (
                <div key={op.id} className="flex items-start space-x-2 py-2 border-b border-gray-800 last:border-0">
                  <span className="text-base mt-0.5">{opTypeIcon(op.type)}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono text-white uppercase">{op.type.replace('_', ' ')}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${op.status === 'success' ? 'text-green-400 bg-green-400/10' : 'text-red-400 bg-red-400/10'}`}>
                        {op.status}
                      </span>
                    </div>
                    <p className={`text-xs ${platformColor(op.platform)}`}>{op.platform}</p>
                    <p className="text-xs text-gray-600 font-mono truncate">{op.agent_id.slice(-8)}</p>
                    <p className="text-xs text-gray-700">{new Date(op.timestamp).toLocaleTimeString()}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Threats from live operations */}
      {threats.length > 0 && (
        <div className="cyber-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white flex items-center">
              <ExclamationTriangleIcon className="w-5 h-5 mr-2 text-red-400" />
              Detected Activity
            </h2>
            <span className="text-sm text-red-400">{threats.length} events</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {threats.slice(0, 6).map(threat => (
              <div key={threat.id} className="bg-gray-900/50 rounded-lg p-3 border border-gray-700 hover:border-red-500/30 transition-all">
                <div className="flex items-center justify-between mb-1">
                  <span className={`px-2 py-0.5 rounded text-xs font-bold border ${statusColor(threat.severity)}`}>
                    {threat.type.toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-600">{threat.detectedAt.toLocaleTimeString()}</span>
                </div>
                <p className="text-white text-sm font-medium mt-1">{threat.title}</p>
                <p className="text-xs text-gray-400 mt-1 leading-relaxed">{threat.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}