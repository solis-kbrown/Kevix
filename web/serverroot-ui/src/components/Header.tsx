import { useState } from 'react';
import { 
  ComputerDesktopIcon, 
  ShieldCheckIcon, 
  BeakerIcon, 
  DocumentTextIcon,
  CpuChipIcon,
  BellIcon,
  UserCircleIcon
} from '@heroicons/react/24/outline';
import { BellIcon as BellSolidIcon } from '@heroicons/react/24/solid';

export type TabType = 'dashboard' | 'agents' | 'vulnerabilities' | 'threats' | 'campaigns' | 'research' | 'commands';

interface HeaderProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  notifications?: number;
}

export default function Header({ activeTab, onTabChange, notifications = 0 }: HeaderProps) {
  const tabs = [
    { id: 'dashboard' as TabType, label: 'Dashboard', icon: CpuChipIcon },
    { id: 'agents' as TabType, label: 'Agents', icon: ComputerDesktopIcon },
    { id: 'vulnerabilities' as TabType, label: 'Vulnerabilities', icon: ShieldCheckIcon },
    { id: 'threats' as TabType, label: 'Threats', icon: BellIcon },
    { id: 'campaigns' as TabType, label: 'Campaigns', icon: DocumentTextIcon },
    { id: 'research' as TabType, label: 'AI Research', icon: BeakerIcon },
    { id: 'commands' as TabType, label: 'Commands', icon: ShieldCheckIcon },
  ];

  return (
    <header className="bg-gray-900/80 backdrop-blur-xl border-b border-gray-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-serverroot-500 to-serverroot-700 rounded-lg flex items-center justify-center glow-effect">
              <ShieldCheckIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">ServerRoot.net</h1>
              <p className="text-xs text-serverroot-400">AI Defense Platform</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden lg:flex items-center space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-serverroot-600/20 text-serverroot-400 border border-serverroot-600/50'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Section */}
          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <button className="relative p-2 text-gray-400 hover:text-white transition-colors">
              {notifications > 0 ? (
                <BellSolidIcon className="w-5 h-5 text-serverroot-400" />
              ) : (
                <BellIcon className="w-5 h-5" />
              )}
              {notifications > 0 && (
                <span className="absolute top-1 right-1 w-2 h-2 bg-cyber-red rounded-full pulse-animation" />
              )}
            </button>

            {/* User Profile */}
            <button className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors">
              <UserCircleIcon className="w-8 h-8" />
              <span className="text-sm font-medium">Admin</span>
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="lg:hidden pb-3 overflow-x-auto">
          <nav className="flex items-center space-x-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-200 whitespace-nowrap ${
                    isActive
                      ? 'bg-serverroot-600/20 text-serverroot-400 border border-serverroot-600/50'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}