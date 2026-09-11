import React from 'react';
import { Database, Lock, HelpCircle, Cpu, Radio, ShieldCheck } from 'lucide-react';

export default function KPICards({ stats }) {
  const totalTracked = stats?.total_tracked ?? 0;
  const stationaryCount = stats?.stationary_count ?? 0;
  const lostCount = stats?.lost_count ?? 0;
  const engineActive = stats?.engine_active ?? false;
  const dbSize = stats?.db_size_kb ?? 0;

  const cards = [
    {
      title: 'Objects in Memory',
      value: `${totalTracked} items`,
      subtitle: 'Indexed in SQLite',
      icon: Database,
      accent: 'from-blue-500/20 to-cyan-500/10',
      textColor: 'text-neon-blue',
      borderColor: 'border-blue-500/30',
    },
    {
      title: 'Stationary Locked',
      value: `${stationaryCount} items`,
      subtitle: 'Static coordinates confirmed',
      icon: Lock,
      accent: 'from-emerald-500/20 to-green-500/10',
      textColor: 'text-neon-green',
      borderColor: 'border-emerald-500/30',
    },
    {
      title: 'Missing / Displaced',
      value: `${lostCount} items`,
      subtitle: 'Exited camera view',
      icon: HelpCircle,
      accent: 'from-red-500/20 to-pink-500/10',
      textColor: 'text-neon-red',
      borderColor: 'border-red-500/30',
    },
    {
      title: 'Handoff Vision Engine',
      value: engineActive ? 'ACTIVE' : 'OFFLINE',
      subtitle: `${stats?.stream_resolution || '854x480'} · YOLOv8n`,
      icon: Cpu,
      accent: engineActive ? 'from-purple-500/20 to-indigo-500/10' : 'from-slate-700/20 to-slate-800/10',
      textColor: engineActive ? 'text-purple-400' : 'text-slate-400',
      borderColor: engineActive ? 'border-purple-500/30' : 'border-slate-700/30',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`glass-panel glass-panel-hover rounded-2xl p-4.5 border ${card.borderColor} relative overflow-hidden animate-fadeIn`}
            style={{ animationDelay: `${idx * 80}ms` }}
          >
            <div className={`absolute -right-6 -bottom-6 w-24 h-24 rounded-full bg-gradient-to-br ${card.accent} blur-xl pointer-events-none`} />
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-1">
                  {card.title}
                </p>
                <h3 className={`text-2xl font-black tracking-tight ${card.textColor}`}>
                  {card.value}
                </h3>
                <p className="text-[11px] text-slate-500 font-medium mt-1">
                  {card.subtitle}
                </p>
              </div>
              <div className={`p-2.5 rounded-xl bg-dark-800/90 border border-white/5 ${card.textColor}`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
