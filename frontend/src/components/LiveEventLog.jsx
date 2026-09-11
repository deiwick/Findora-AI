import React, { useState } from 'react';
import { Database, Search, MapPin, Tag, Clock, CheckCircle2, AlertTriangle, HelpCircle, Image as ImageIcon, ExternalLink } from 'lucide-react';

export default function LiveEventLog({ events, onRefresh }) {
  const [filterQuery, setFilterQuery] = useState('');
  const [selectedThumb, setSelectedThumb] = useState(null);

  const filteredEvents = (events || []).filter((e) => {
    if (!filterQuery) return true;
    const q = filterQuery.toLowerCase();
    return (
      (e.object_name && e.object_name.toLowerCase().includes(q)) ||
      (e.room_name && e.room_name.toLowerCase().includes(q)) ||
      (e.status && e.status.toLowerCase().includes(q)) ||
      (e.track_id && String(e.track_id).includes(q))
    );
  });

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'stationary':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3 text-neon-green" />
            <span>STATIONARY</span>
          </span>
        );
      case 'moved':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-3 h-3 text-neon-amber" />
            <span>MOVED</span>
          </span>
        );
      case 'lost':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/30">
            <HelpCircle className="w-3 h-3 text-neon-red" />
            <span>LOST</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-slate-800 text-slate-300">
            {status?.toUpperCase() || 'UNKNOWN'}
          </span>
        );
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 mb-8 border border-white/10">
      {/* Header & Search Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-5">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-neon-blue" />
            <span>SQLite Spatial Memory Audit Stream</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Immutable timeline of object state transitions recorded locally
          </p>
        </div>

        {/* Filter Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Filter by object, zone..."
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 rounded-xl bg-dark-800 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition-colors"
          />
        </div>
      </div>

      {/* Events Table */}
      <div className="overflow-x-auto rounded-xl border border-white/5">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-dark-800/80 border-b border-white/10 text-[11px] font-mono text-slate-400 uppercase tracking-wider">
              <th className="py-3 px-4">Event ID</th>
              <th className="py-3 px-4">Object Label</th>
              <th className="py-3 px-4">Room / Zone</th>
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4">State</th>
              <th className="py-3 px-4">Confidence</th>
              <th className="py-3 px-4 text-center">Snapshot Crop</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-xs">
            {filteredEvents.length > 0 ? (
              filteredEvents.map((ev) => (
                <tr
                  key={ev.id}
                  className="hover:bg-white/[0.02] transition-colors font-medium text-slate-200"
                >
                  <td className="py-3 px-4 font-mono text-slate-400">#{ev.id}</td>
                  <td className="py-3 px-4 font-semibold text-white capitalize flex items-center gap-2">
                    <Tag className="w-3.5 h-3.5 text-cyan-400" />
                    <span>{ev.object_name}</span>
                    <span className="text-[10px] font-mono text-slate-500">
                      (Track #{ev.track_id})
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-300">
                    <span className="inline-flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span>{ev.room_name}</span>
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">
                    <span className="inline-flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-500" />
                      <span>{ev.timestamp}</span>
                    </span>
                  </td>
                  <td className="py-3 px-4">{getStatusBadge(ev.status)}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 rounded-full bg-dark-700 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full"
                          style={{ width: `${Math.min(100, Math.max(0, (ev.confidence || 0) * 100))}%` }}
                        />
                      </div>
                      <span className="font-mono text-[11px] text-slate-300">
                        {ev.confidence ? `${(ev.confidence * 100).toFixed(0)}%` : 'N/A'}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center">
                    {ev.thumbnail_path ? (
                      <button
                        onClick={() => setSelectedThumb(`/${ev.thumbnail_path}`)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-dark-800 hover:bg-dark-700 border border-white/10 text-cyan-300 hover:text-cyan-200 text-[11px] transition-colors"
                      >
                        <ImageIcon className="w-3 h-3" />
                        <span>View</span>
                      </button>
                    ) : (
                      <span className="text-[11px] text-slate-600 font-mono">—</span>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500 text-xs">
                  No spatial memory events recorded yet. Place an object in view of a camera for ~2.5 seconds.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Snapshot Modal */}
      {selectedThumb && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setSelectedThumb(null)}
        >
          <div
            className="glass-panel rounded-2xl p-4 max-w-sm w-full border border-white/20 shadow-2xl relative"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-white/10">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-neon-blue" />
                <span>200x200 Bounding Box Crop</span>
              </h4>
              <button
                onClick={() => setSelectedThumb(null)}
                className="text-slate-400 hover:text-white text-xs font-mono px-2 py-1 rounded bg-white/5"
              >
                ESC
              </button>
            </div>
            <div className="rounded-xl overflow-hidden bg-black flex items-center justify-center aspect-square border border-white/10">
              <img
                src={selectedThumb}
                alt="Object Snapshot"
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.src = 'https://via.placeholder.com/200?text=Snapshot+Missing';
                }}
              />
            </div>
            <p className="text-[11px] text-slate-400 text-center mt-3 font-mono">
              Privacy Crop: Surrounding room background excluded.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
