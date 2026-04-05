import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

export function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'critical':
      return 'text-cyber-red bg-cyber-red/10 border-cyber-red';
    case 'high':
      return 'text-orange-400 bg-orange-400/10 border-orange-400';
    case 'medium':
      return 'text-yellow-400 bg-yellow-400/10 border-yellow-400';
    case 'low':
      return 'text-green-400 bg-green-400/10 border-green-400';
    default:
      return 'text-gray-400 bg-gray-400/10 border-gray-400';
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'active':
    case 'running':
    case 'completed':
      return 'text-green-400 bg-green-400/10 border-green-400';
    case 'scanning':
    case 'exploiting':
    case 'deploying':
    case 'running':
    case 'researching':
    case 'generating':
    case 'queued':
      return 'text-serverroot-400 bg-serverroot-400/10 border-serverroot-400';
    case 'paused':
    case 'idle':
      return 'text-yellow-400 bg-yellow-400/10 border-yellow-400';
    case 'failed':
    case 'stopped':
      return 'text-cyber-red bg-cyber-red/10 border-cyber-red';
    default:
      return 'text-gray-400 bg-gray-400/10 border-gray-400';
  }
}