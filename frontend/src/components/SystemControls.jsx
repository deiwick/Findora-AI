import React, { useState } from 'react';
import { Shield, Trash2, RefreshCw, Server, Sliders, CheckCircle2, Lock, Cpu, Database, AlertOctagon } from 'lucide-react';

export default function SystemControls({ stats, onRestartEngine, onClearMemory }) {
  const [confirmClear, setConfirmClear] = useState(false);
  const [clearing, setClearing] = useState(false);

  const handleClear = async () => {
    setClearing(true);
    await onClearMemory();
    setClearing(false);
    setConfirmClear(false);
  };

  return (
    <div className="space-y-6 mb-8">
      {/* Privacy Guard & System Health Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel rounded-2xl p-5 border border-emerald-500/30">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Cloud Privacy Guard</span>
            <Lock className="w-4 h-4 text-neon-green" />
          </div>
          <h4 className="text-xl font-bold text-white mb-1">100% On-Device</h4>
          <p className="text-xs text-slate-400">
            Zero telemetry, zero cloud NLP or external vision APIs. All inference runs on local CPU/GPU.
          </p>
        </div>

        <div className="glass-panel rounded-2xl p-5 border border-cyan-500/30">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Local SQLite Memory</span>
            <Database className="w-4 h-4 text-neon-blue" />
          </div>
          <h4 className="text-xl font-bold text-white mb-1">{stats?.db_size_kb || 0} KB</h4>
          <p className="text-xs text-slate-400">
            Compact local relational database with indexed spatial timestamps and coordinates.
          </p>
        </div>

        <div className="glass-panel rounded-2xl p-5 border border-purple-500/30">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Saved Snapshots</span>
            <Server className="w-4 h-4 text-purple-400" />
          </div>
          <h4 className="text-xl font-bold text-white mb-1">{stats?.thumbnail_count || 0} Crops</h4>
          <p className="text-xs text-slate-400">
            Strict 200x200 pixel localized crops. Full-scene background images are never saved to disk.
          </p>
        </div>
      </div>

      {/* Main Control Panel */}
      <div className="glass-panel rounded-2xl p-6 lg:p-8 border border-white/10">
        <div className="flex items-center gap-2 mb-6">
          <Sliders className="w-5 h-5 text-neon-blue" />
          <h3 className="text-lg font-bold text-white">
            Edge-AI Engine Calibration & Memory Operations
          </h3>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Active Calibration Parameters */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2">
              Runtime Detection Parameters:
            </h4>
            <div className="p-3.5 rounded-xl bg-dark-800/80 border border-white/5 flex items-center justify-between text-xs">
              <span className="text-slate-400">YOLOv8 Model:</span>
              <span className="font-mono font-bold text-white">yolov8n.pt (COCO 80)</span>
            </div>
            <div className="p-3.5 rounded-xl bg-dark-800/80 border border-white/5 flex items-center justify-between text-xs">
              <span className="text-slate-400">Confidence Threshold:</span>
              <span className="font-mono font-bold text-cyan-300">
                {((stats?.conf_threshold || 0.28) * 100).toFixed(0)}% (Conf ≥ {stats?.conf_threshold || 0.28})
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-dark-800/80 border border-white/5 flex items-center justify-between text-xs">
              <span className="text-slate-400">Stationary Lock Time:</span>
              <span className="font-mono font-bold text-emerald-300">
                {stats?.stationary_time_threshold || 2.5} seconds
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-dark-800/80 border border-white/5 flex items-center justify-between text-xs">
              <span className="text-slate-400">Lost Missing Timeout:</span>
              <span className="font-mono font-bold text-red-300">
                {stats?.lost_timeout || 4.0} seconds
              </span>
            </div>
          </div>

          {/* Action Operations */}
          <div className="space-y-4">
            <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2">
              System Actions & Maintenance:
            </h4>

            {/* Restart Engine */}
            <div className="p-4 rounded-xl bg-dark-800/80 border border-white/5 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-white">Restart Vision Engine</p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Re-initializes camera workers, clears buffers, and warms up YOLOv8 models.
                </p>
              </div>
              <button
                onClick={onRestartEngine}
                className="px-4 py-2 rounded-xl bg-dark-700 hover:bg-dark-600 border border-white/10 hover:border-cyan-500/40 text-xs font-semibold text-cyan-300 hover:text-white transition-all flex items-center gap-2"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Restart</span>
              </button>
            </div>

            {/* Clear Database */}
            <div className="p-4 rounded-xl bg-red-500/5 border border-red-500/20 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-red-400">Purge Spatial Memory Database</p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Deletes all historical event logs and clears saved thumbnail crop files.
                </p>
              </div>
              <button
                onClick={() => setConfirmClear(true)}
                className="px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-xs font-bold text-red-400 hover:text-red-300 transition-all flex items-center gap-2"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear DB</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {confirmClear && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel rounded-2xl p-6 max-w-md w-full border border-red-500/30 shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2.5 rounded-xl bg-red-500/10 text-red-400 border border-red-500/30">
                <AlertOctagon className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Confirm Memory Reset</h4>
                <p className="text-xs text-slate-400">This action cannot be undone.</p>
              </div>
            </div>
            <p className="text-xs text-slate-300 mb-6 leading-relaxed">
              Are you sure you want to clear all spatial memory records and delete all saved thumbnail snapshots?
            </p>
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setConfirmClear(false)}
                className="px-4 py-2 rounded-xl bg-dark-800 hover:bg-dark-700 text-slate-300 text-xs font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleClear}
                disabled={clearing}
                className="px-4 py-2 rounded-xl bg-red-500 hover:bg-red-600 text-white text-xs font-bold shadow-neon-red transition-all disabled:opacity-50 flex items-center gap-2"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>{clearing ? 'Clearing...' : 'Purge Everything'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
