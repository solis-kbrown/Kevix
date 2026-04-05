'use client';
import { useState, useEffect, useCallback } from 'react';
import { SignalIcon, ArrowPathIcon, FunnelIcon } from '@heroicons/react/24/outline';
import { SwarmOperation } from '@/types';
import { fetchSwarmOperations, opTypeIcon, statusColor, platformColor } from '@/lib/api';

export default function Operations() {
  const [operations, setOperations] = useState<SwarmOperation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchAll = useCallback(async () => {
    try {
      const ops = await fetchSwarmOperations();
      setOperations(ops);
      setLastUpdated(new Date());
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch operations');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 4000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const types = ['all', ...Array.from(new Set(operations.map(o => o.type)))];
  const statuses = ['all', 'success', 'failed', 'running'];

  const filtered = operations.filter(op => {
    const matchType = typeFilter === 'all' || op.type === typeFilter;
    const matchStatus = statusFilter === 'all' || op.status === statusFilter;
    return matchType && matchStatus;
  });

  const successCount = operations.filter(o => o.status === 'success').length;
  const failCount = operations.filter(o => o.status === 'failed').length;
  const successRate = operations.length > 0 ? Math.round((successCount / operations.length) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Live Operations</h2>
          <p className="text-sm text-gray-400 mt-0.5">Real-time swarm activity · updated {lastUpdated.toLocaleTimeString()}</p>
        </div>
        <button onClick={fetchAll} className="flex items-center space-x-1 px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm border border-gray-700 transition-colors">
          <ArrowPathIcon className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Total', value: operations.length, color: 'text-white' },
          { label: 'Successful', value: successCount, color: 'text-green-400' },
          { label: 'Failed', value: failCount, color: 'text-red-400' },
          { label: 'Success Rate', value: `${successRate}%`, color: successRate > 70 ? 'text-green-400' : 'text-yellow-400' },
        ].map(item => (
          <div key={item.label} className="cyber-card py-3 text-center">
            <p className="text-xs text-gray-500 uppercase">{item.label}</p>
            <p className={`text-2xl font-bold mt-1 ${item.color}`}>{item.value}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="flex items-center space-x-2">
          <FunnelIcon className="w-4 h-4 text-gray-500" />
          <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-white text-sm">
            {types.map(t => <option key={t} value={t}>{t === 'all' ? 'All Types' : t}</option>)}
          </select>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-white text-sm">
            {statuses.map(s => <option key={s} value={s}>{s === 'all' ? 'All Status' : s}</option>)}
          </select>
        </div>
        <span className="text-xs text-gray-500 self-center">Showing {filtered.length} of {operations.length}</span>
      </div>

      {/* Operations Table */}
      {loading ? (
        <div className="text-center py-16 text-gray-500">
          <SignalIcon className="w-10 h-10 mx-auto mb-3 animate-pulse" />
          <p>Loading operations...</p>
        </div>
      ) : error ? (
        <div className="cyber-card border-red-700/40 bg-red-900/10 text-center py-10">
          <p className="text-red-400 font-mono text-sm">⚠ {error}</p>
        </div>
      ) : (
        <div className="cyber-card overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 bg-gray-900/50">
                  <th className="text-left px-4 py-3 text-xs text-gray-500 uppercase font-medium">Type</th>
                  <th className="text-left px-4 py-3 text-xs text-gray-500 uppercase font-medium">Platform</th>
                  <th className="text-left px-4 py-3 text-xs text-gray-500 uppercase font-medium">Agent</th>
                  <th className="text-left px-4 py-3 text-xs text-gray-500 uppercase font-medium">Status</th>
                  <th className="text-left px-4 py-3 text-xs text-gray-500 uppercase font-medium">Time</th>
                  <th className="text-left px-4 py-3 text-xs text-gray-500 uppercase font-medium">ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/50">
                {filtered.map(op => (
                  <tr key={op.id} className="hover:bg-gray-800/30 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-2">
                        <span>{opTypeIcon(op.type)}</span>
                        <span className="font-mono text-white uppercase text-xs">{op.type.replace('_', ' ')}</span>
                      </div>
                    </td>
                    <td className={`px-4 py-3 font-medium text-xs ${platformColor(op.platform)}`}>{op.platform}</td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-400">{op.agent_id.slice(-12)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${statusColor(op.status)}`}>{op.status}</span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">{new Date(op.timestamp).toLocaleTimeString()}</td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-700">{op.id.slice(0, 8)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <p>No operations match your filter</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}