'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import Dashboard from '@/components/Dashboard';
import Agents from '@/components/Agents';
import Operations from '@/components/Operations';
import CommandCenter from '@/components/CommandCenter';
import type { TabType } from '@/components/Header';

export default function Home() {
  const [activeTab, setTab] = useState<TabType>('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':    return <Dashboard />;
      case 'agents':       return <Agents />;
      case 'vulnerabilities': return <Operations />;  // Live operations feed
      case 'threats':      return <Operations />;     // Live threat feed
      case 'campaigns':    return <CommandCenter />;  // Campaign = command center
      case 'research':     return <CommandCenter />;  // AI research = command center
      case 'commands':     return <CommandCenter />;  // Full command center
      default:             return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <Header
        activeTab={activeTab}
        onTabChange={setTab}
        notifications={0}
      />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderContent()}
      </main>
    </div>
  );
}