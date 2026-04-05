// ServerRoot.net — Production Types
// All data comes from live API — no mock fallbacks

export interface Agent {
  id: string;
  hostname: string;
  ip: string;
  platform: 'windows' | 'linux' | 'macos' | 'esxi' | 'android' | 'iot' | 'router' | 'vpn';
  status: 'active' | 'scanning' | 'exploiting' | 'deploying' | 'idle' | 'error';
  role: 'leader' | 'worker';
  lastSeen: Date;
  registeredAt: Date;
  vulnerabilities: number;
  exploitsExecuted: number;
  tasksCompleted: number;
  load: number;
  uptime: number;
  capabilities: string[];
}

export interface Vulnerability {
  id: string;
  cve: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  affectedSystems: number;
  exploitAvailable: boolean;
  publishedDate: Date;
  service?: string;
  port?: number;
  cvssScore?: number;
}

export interface Threat {
  id: string;
  type: 'ransomware' | 'apt' | 'exploit' | 'malware' | 'recon' | 'exfil' | 'lateral';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  detectedAt: Date;
  source: string;
  agentId?: string;
  platform?: string;
}

export interface Campaign {
  id: string;
  name: string;
  status: 'running' | 'paused' | 'completed' | 'failed';
  targetsScanned: number;
  vulnerabilitiesFound: number;
  agentsDeployed: number;
  exploitsExecuted: number;
  startTime: Date;
  endTime?: Date;
}

export interface ResearchReport {
  id: string;
  title: string;
  type: 'vulnerability' | 'exploit' | 'persistence' | 'evasion';
  status: 'researching' | 'generating' | 'completed';
  progress: number;
  cve?: string;
  findings: string[];
  generatedAt: Date;
}

export interface SystemStats {
  totalAgents: number;
  activeAgents: number;
  totalVulnerabilities: number;
  criticalVulnerabilities: number;
  totalExploits: number;
  activeCampaigns: number;
  totalThreats: number;
  systemUptime: number;
  aiResearchReports: number;
  successRate: number;
  swarmHealth: string;
  operationsLastHour: number;
}

export interface Command {
  id: string;
  type: 'scan' | 'exploit' | 'deploy' | 'persistence' | 'persist' | 'propagate' | 'gather' | 'stop' | 'recon' | 'exfil' | 'lateral_move';
  targetAgent?: string;
  targetNetwork?: string;
  parameters: Record<string, unknown>;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'success';
  createdAt: Date;
  completedAt?: Date;
  result?: string;
  platform?: string;
}

export interface SwarmOperation {
  id: string;
  agent_id: string;
  type: string;
  platform: string;
  status: 'success' | 'failed' | 'running';
  timestamp: string;
}

export interface SwarmAgent {
  id: string;
  hostname: string;
  ip: string;
  platform: string;
  status: string;
  role: string;
  load: number;
  last_seen: string;
  registered_at: string;
  tasks_completed: number;
  capabilities: string[];
}

export interface ApiHealth {
  service: string;
  status: string;
  timestamp: string;
  uptime_seconds: number;
  version: string;
}

export interface SwarmIntelligence {
  active_agents: number;
  average_load: number;
  capabilities: {
    platforms: string[];
    roles: { leaders: number; workers: number };
  };
  operations_last_hour: number;
  success_rate: number;
  swarm_health: string;
  timestamp: string;
  total_agents: number;
}