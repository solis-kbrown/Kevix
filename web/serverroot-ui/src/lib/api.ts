/**
 * ServerRoot.net — Production Live API Client
 * All data sourced from Flask API at :5001
 * No mock data, no fallbacks — production only
 *
 * API base URL resolution (per request):
 * 1. localStorage 'serverroot_api_url' override (user-configurable at runtime)
 * 2. Build-time NEXT_PUBLIC_API_URL env var
 * 3. Empty string '' = relative URL (works via Next.js proxy rewrite /api/* → :5001)
 */

import { SwarmAgent, SwarmOperation, SwarmIntelligence, ApiHealth, SystemStats, Command } from '@/types';

function getApiBase(): string {
  if (typeof window !== 'undefined') {
    const override = localStorage.getItem('serverroot_api_url');
    if (override && override.trim()) return override.trim();
  }
  return process.env.NEXT_PUBLIC_API_URL || '';
}

// ── Core fetcher ────────────────────────────────────────────────────────────
async function apiFetch<T>(endpoint: string, options?: RequestInit, timeout = 8000): Promise<T> {
  const base = getApiBase();
  const controller = new AbortController();
  const tid = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(`${base}${endpoint}`, {
      ...options,
      signal: controller.signal,
      headers: { 'Content-Type': 'application/json', ...options?.headers },
    });
    clearTimeout(tid);
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${endpoint}`);
    return await res.json() as T;
  } catch (err) {
    clearTimeout(tid);
    throw err;
  }
}

// ── Health ──────────────────────────────────────────────────────────────────
export async function fetchHealth(): Promise<ApiHealth> {
  return apiFetch<ApiHealth>('/api/health');
}

// ── Swarm Status ────────────────────────────────────────────────────────────
export async function fetchSwarmStatus(): Promise<{
  initialized: boolean;
  agent_count: number;
  active_agents: number;
  stats: {
    total_agents: number;
    active_agents: number;
    total_operations: number;
    successful_operations: number;
    targets_scanned: number;
    vulnerabilities_found: number;
    uptime_seconds: number;
  };
  timestamp: string;
}> {
  return apiFetch('/api/swarm/status');
}

// ── Agents ──────────────────────────────────────────────────────────────────
export async function fetchSwarmAgents(): Promise<SwarmAgent[]> {
  const data = await apiFetch<{ agents: SwarmAgent[] }>('/api/swarm/agents');
  return data.agents ?? [];
}

export async function fetchAgent(agentId: string): Promise<SwarmAgent> {
  return apiFetch<SwarmAgent>(`/api/swarm/agents/${agentId}`);
}

// ── Stats ────────────────────────────────────────────────────────────────────
export async function fetchSwarmStats(): Promise<{
  active_agents: number;
  successful_operations: number;
  targets_scanned: number;
  total_agents: number;
  total_operations: number;
  uptime_seconds: number;
  vulnerabilities_found: number;
}> {
  return apiFetch('/api/swarm/stats');
}

// ── Operations ───────────────────────────────────────────────────────────────
export async function fetchSwarmOperations(): Promise<SwarmOperation[]> {
  const data = await apiFetch<{ operations: SwarmOperation[] }>('/api/swarm/operations');
  return data.operations ?? [];
}

// ── Intelligence ─────────────────────────────────────────────────────────────
export async function fetchSwarmIntelligence(): Promise<SwarmIntelligence> {
  return apiFetch<SwarmIntelligence>('/api/swarm/intelligence');
}

// ── Commands ─────────────────────────────────────────────────────────────────
export async function sendCommand(payload: {
  command: string;
  agent_id?: string;
  target?: string;
  parameters?: Record<string, unknown>;
}): Promise<{ success: boolean; result?: string; error?: string }> {
  return apiFetch('/api/swarm/commands', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function scaleSwarm(count: number): Promise<{ success: boolean }> {
  return apiFetch('/api/swarm/scale', {
    method: 'POST',
    body: JSON.stringify({ count }),
  });
}

export async function initSwarm(): Promise<{ success: boolean }> {
  return apiFetch('/api/swarm/init', { method: 'POST' });
}

export async function resetSwarm(): Promise<{ success: boolean }> {
  return apiFetch('/api/swarm/reset', { method: 'POST' });
}

// ── Runtime API URL management ───────────────────────────────────────────────
export function setApiUrl(url: string): void {
  if (typeof window !== 'undefined') {
    if (url.trim()) {
      localStorage.setItem('serverroot_api_url', url.trim());
    } else {
      localStorage.removeItem('serverroot_api_url');
    }
  }
}

export function getConfiguredApiUrl(): string {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('serverroot_api_url') || '';
  }
  return process.env.NEXT_PUBLIC_API_URL || '';
}

// ── Data transformation helpers ───────────────────────────────────────────────

export function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  return `${Math.floor(seconds / 86400)}d ${Math.floor((seconds % 86400) / 3600)}h`;
}

export function platformColor(platform: string): string {
  const map: Record<string, string> = {
    windows: 'text-blue-400',
    linux: 'text-orange-400',
    esxi: 'text-purple-400',
    macos: 'text-gray-300',
    router: 'text-yellow-400',
    vpn: 'text-cyan-400',
    iot: 'text-pink-400',
    android: 'text-green-400',
  };
  return map[platform] ?? 'text-gray-400';
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    active: 'text-green-400 bg-green-400/10 border-green-400',
    scanning: 'text-blue-400 bg-blue-400/10 border-blue-400',
    exploiting: 'text-red-400 bg-red-400/10 border-red-400',
    deploying: 'text-serverroot-400 bg-serverroot-400/10 border-serverroot-400',
    idle: 'text-yellow-400 bg-yellow-400/10 border-yellow-400',
    error: 'text-red-500 bg-red-500/10 border-red-500',
    success: 'text-green-400 bg-green-400/10 border-green-400',
    failed: 'text-red-400 bg-red-400/10 border-red-400',
    running: 'text-blue-400 bg-blue-400/10 border-blue-400',
  };
  return map[status] ?? 'text-gray-400 bg-gray-400/10 border-gray-400';
}

export function opTypeIcon(type: string): string {
  const map: Record<string, string> = {
    scan: '🔍',
    recon: '📡',
    exploit: '💥',
    exfil: '📤',
    persist: '🔒',
    persistence: '🔒',
    lateral_move: '↔️',
    deploy: '🚀',
    gather: '📊',
  };
  return map[type] ?? '⚡';
}

export function healthColor(health: string): string {
  const map: Record<string, string> = {
    healthy: 'text-green-400',
    degraded: 'text-yellow-400',
    critical: 'text-red-400',
  };
  return map[health] ?? 'text-gray-400';
}

// ── Build SystemStats from API data ──────────────────────────────────────────
export function buildSystemStats(
  stats: Awaited<ReturnType<typeof fetchSwarmStats>>,
  intel: SwarmIntelligence
): SystemStats {
  return {
    totalAgents: stats.total_agents,
    activeAgents: stats.active_agents,
    totalVulnerabilities: stats.vulnerabilities_found,
    criticalVulnerabilities: 0,
    totalExploits: stats.successful_operations,
    activeCampaigns: 0,
    totalThreats: 0,
    systemUptime: stats.uptime_seconds,
    aiResearchReports: 0,
    successRate: intel.success_rate,
    swarmHealth: intel.swarm_health,
    operationsLastHour: intel.operations_last_hour,
  };
}

// ── Build threats from operations ────────────────────────────────────────────
export function operationsToThreats(operations: SwarmOperation[]) {
  const threatTypes: Record<string, { type: string; severity: string }> = {
    exploit:      { type: 'exploit',  severity: 'critical' },
    exfil:        { type: 'exfil',    severity: 'high' },
    lateral_move: { type: 'lateral',  severity: 'high' },
    persist:      { type: 'apt',      severity: 'high' },
    persistence:  { type: 'apt',      severity: 'high' },
    recon:        { type: 'recon',    severity: 'medium' },
    scan:         { type: 'recon',    severity: 'low' },
    deploy:       { type: 'malware',  severity: 'medium' },
  };
  return operations
    .filter(op => op.status === 'success' && threatTypes[op.type])
    .slice(0, 10)
    .map(op => {
      const tt = threatTypes[op.type] ?? { type: 'exploit', severity: 'medium' };
      return {
        id: op.id,
        type: tt.type as never,
        severity: tt.severity as never,
        title: `${op.type.replace('_', ' ').toUpperCase()} on ${op.platform}`,
        description: `Agent ${op.agent_id.slice(-8)} executed ${op.type} against ${op.platform} target`,
        detectedAt: new Date(op.timestamp),
        source: op.agent_id,
        agentId: op.agent_id,
        platform: op.platform,
      };
    });
}