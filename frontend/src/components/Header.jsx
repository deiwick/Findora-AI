import React, { useState, useEffect } from 'react';
import { Shield, Radio, Activity, RefreshCw, Power, Video, Cpu } from 'lucide-react';

export default function Header({ stats, onRestartEngine, onToggleEngine, activeTab, setActiveTab }) {
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const engineActive = stats?.engine_active ?? false;

  const tabs = [
    { id: 'live', label: 'Live Feeds & Audit', icon: Video },
    { id: 'search', label: 'AI Object Finder', icon: Activity },
    { id: 'timeline', label: 'Spatial Timeline', icon: Radio },
    { id: 'controls', label: 'Controls & Privacy', icon: Shield },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-white/10 px-4 lg:px-8 py-3.5 mb-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Logo & Identity */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-11 h-11 rounded-xl bg-gradient-to-tr from-cyan-500/20 to-blue-600/30 border border-cyan-500/40 shadow-neon-blue">
            <Shield className="w-6 h-6 text-neon-blue" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${engineActive ? 'bg-neon-green' : 'bg-neon-red'}`}></span>
              <span className={`relative inline-flex rounded-full h-3 w-3 ${engineActive ? 'bg-neon-green' : 'bg-neon-red'}`}></span>
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                Findora AI
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                Edge v2.0
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Dual-Camera Spatial Memory & Handoff Tracker
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center bg-dark-800/80 p-1.5 rounded-xl border border-white/5 shadow-inner">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-neon-blue'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-neon-blue' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Engine Status & System Actions */}
        <div className="flex items-center gap-3">
          {/* Status Badge */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-800 border border-white/10 text-xs font-mono">
            <span className={`w-2 h-2 rounded-full ${engineActive ? 'bg-neon-green shadow-neon-green' : 'bg-neon-red'}`} />
            <span className="text-slate-300 font-medium">
              {engineActive ? 'ENGINE ONLINE' : 'ENGINE OFFLINE'}
            </span>
            <span className="text-slate-500 text-[11px] border-l border-white/10 pl-2">
              {timeStr}
            </span>
          </div>

          {/* Quick Restart Button */}
          <button
            onClick={onRestartEngine}
            title="Restart Vision Engine"
            className="flex items-center justify-center p-2 rounded-lg bg-dark-800 hover:bg-dark-700 border border-white/10 hover:border-cyan-500/40 text-slate-300 hover:text-cyan-400 transition-all duration-200 shadow-sm"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          {/* Power Toggle Button */}
          <button
            onClick={onToggleEngine}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
              engineActive
                ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30'
                : 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
            }`}
          >
            <Power className="w-3.5 h-3.5" />
            <span>{engineActive ? 'Stop' : 'Start'}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
