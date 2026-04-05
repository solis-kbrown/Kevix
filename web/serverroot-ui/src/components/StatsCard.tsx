import { HTMLAttributes } from 'react';

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon: React.ComponentType<HTMLAttributes<SVGElement>>;
  color?: 'serverroot' | 'cyber-green' | 'cyber-red' | 'cyber-yellow';
}

export default function StatsCard({
  title,
  value,
  change,
  changeType = 'neutral',
  icon: Icon,
  color = 'serverroot',
}: StatsCardProps) {
  const colorClasses = {
    serverroot: 'text-serverroot-400 bg-serverroot-400/10 border-serverroot-400/30',
    'cyber-green': 'text-cyber-green bg-cyber-green/10 border-cyber-green/30',
    'cyber-red': 'text-cyber-red bg-cyber-red/10 border-cyber-red/30',
    'cyber-yellow': 'text-cyber-yellow bg-cyber-yellow/10 border-cyber-yellow/30',
  };

  const changeColorClasses = {
    increase: 'text-green-400',
    decrease: 'text-cyber-red',
    neutral: 'text-gray-400',
  };

  return (
    <div className="cyber-card hover:border-serverroot-500/50 transition-all duration-300">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-400 font-medium">{title}</p>
          <p className="text-3xl font-bold text-white mt-1">{value}</p>
          {change && (
            <p className={`text-sm mt-2 ${changeColorClasses[changeType]}`}>
              {change}
            </p>
          )}
        </div>
        <div className={`p-3 rounded-lg border ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}