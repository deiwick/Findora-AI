import React, { useState, useEffect } from 'react';
import { History, Tag, MapPin, Clock, ArrowRight, CheckCircle2, AlertTriangle, HelpCircle, Image as ImageIcon, Filter, Sparkles, Navigation } from 'lucide-react';

export default function SpatialTimeline() {
  const [objectList, setObjectList] = useState([]);
  const [selectedObject, setSelectedObject] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedThumb, setSelectedThumb] = useState(null);
  const [filterState, setFilterState] = useState('all');

  // Fetch available objects
  useEffect(() => {
    fetch('/api/objects')
      .then((res) => res.json())
      .then((data) => {
        const objs = data.objects || [];
        setObjectList(objs);
        if (objs.length > 0) {
          const defaultObj = data.active_in_db?.[0] || objs[0] || 'phone';
          setSelectedObject(defaultObj);
          fetchHistory(defaultObj);
        }
      })
      .catch((err) => console.error('Failed to fetch object list:', err));
  }, []);

  const fetchHistory = async (objName) => {
    if (!objName) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/history/${encodeURIComponent(objName)}`);
      const data = await res.json();
      setHistory(data.history || []);
    } catch (err) {
      console.error('Failed to fetch object history:', err);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectObject = (obj) => {
    setSelectedObject(obj);
    fetchHistory(obj);
  };

  const getStatusInfo = (status) => {
    switch (status?.toLowerCase()) {
      case 'stationary':
        return {
          icon: CheckCircle2,
          color: 'text-neon-green',
          border: 'border-emerald-500/40',
          bg: 'bg-emerald-500/10',
          text: 'STATIONARY',
          desc: 'Locked at stationary coordinates in',
        };
      case 'moved':
        return {
          icon: AlertTriangle,
          color: 'text-neon-amber',
          border: 'border-amber-500/40',
          bg: 'bg-amber-500/10',
          text: 'MOVED',
          desc: 'Displaced / moved coordinates within',
        };
      case 'lost':
        return {
          icon: HelpCircle,
          color: 'text-neon-red',
          border: 'border-red-500/40',
          bg: 'bg-red-500/10',
          text: 'LOST',
          desc: 'Exited frame / missing from',
        };
      default:
        return {
          icon: History,
          color: 'text-slate-400',
          border: 'border-slate-700',
          bg: 'bg-slate-800',
          text: (status || 'EVENT').toUpperCase(),
          desc: 'Detected in',
        };
    }
  };

  const filteredHistory = history.filter((ev) => {
    if (filterState === 'all') return true;
    return ev.status?.toLowerCase() === filterState;
  });

  return (
    <div className="glass-panel rounded-2xl p-6 lg:p-8 mb-8 border border-white/10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <History className="w-5 h-5 text-neon-blue" />
            <h2 className="text-xl font-bold text-white">
              Temporal Spatial Displacement Timeline
            </h2>
          </div>
          <p className="text-xs text-slate-400">
            Chronological audit trail of physical object journeys across camera zones
          </p>
        </div>

        {/* Object Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-mono text-slate-400">Target Object:</label>
          <select
            value={selectedObject}
            onChange={(e) => handleSelectObject(e.target.value)}
            className="px-3.5 py-1.5 rounded-xl bg-dark-800 border border-white/10 text-xs font-semibold text-white focus:outline-none focus:border-cyan-500 transition-colors"
          >
            {objectList.map((obj) => (
              <option key={obj} value={obj}>
                {(obj || '').charAt(0).toUpperCase() + (obj || '').slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 mb-6 pb-4 border-b border-white/5 overflow-x-auto">
        <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1 mr-2">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          Filter:
        </span>
        {['all', 'stationary', 'moved', 'lost'].map((st) => (
          <button
            key={st}
            onClick={() => setFilterState(st)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
              filterState === st
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-neon-blue'
                : 'bg-dark-800/60 text-slate-400 hover:text-slate-200 border border-white/5'
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Timeline Stream */}
      {loading ? (
        <div className="py-12 text-center text-slate-500 text-xs font-mono animate-pulse">
          Loading spatial timeline...
        </div>
      ) : filteredHistory.length > 0 ? (
        <div className="relative pl-6 border-l-2 border-cyan-500/30 space-y-6 my-4">
          {filteredHistory.map((ev, idx) => {
            const info = getStatusInfo(ev.status);
            const Icon = info.icon;
            const objLabel = (ev.object_name || selectedObject || 'Object').toUpperCase();
            const confPct = ev.confidence != null ? `${(ev.confidence * 100).toFixed(1)}%` : '—';

            return (
              <div key={ev.id || idx} className="relative group">
                {/* Node Dot */}
                <div className={`absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-dark-900 border-2 ${info.border} flex items-center justify-center shadow-lg`}>
                  <div className={`w-1.5 h-1.5 rounded-full ${info.color} bg-current`} />
                </div>

                {/* Event Card */}
                <div className="glass-card rounded-xl p-4 border border-white/5 hover:border-cyan-500/30 transition-all duration-200 shadow-md">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${info.border} ${info.bg} ${info.color}`}>
                        {info.text}
                      </span>
                      <span className="text-xs font-semibold text-white">
                        {objLabel} {ev.track_id ? `(Track #${ev.track_id})` : ''}
                      </span>
                    </div>
                    <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-500" />
                      {ev.timestamp || '—'}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 mb-3 flex items-center gap-1.5 flex-wrap">
                    <span>{info.desc}</span>
                    <strong className="text-white font-bold flex items-center gap-1 bg-white/5 px-2 py-0.5 rounded border border-white/5">
                      <MapPin className="w-3 h-3 text-cyan-400" />
                      {ev.room_name || 'Unknown Zone'}
                    </strong>
                    <span className="text-slate-500 font-mono text-[11px]">
                      (Confidence: {confPct})
                    </span>
                  </p>

                  {/* Thumbnail Preview */}
                  {ev.thumbnail_path && (
                    <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-14 h-14 rounded-lg overflow-hidden border border-white/10 bg-black flex-shrink-0 cursor-pointer hover:opacity-80 transition-opacity"
                          onClick={() => setSelectedThumb(`/${ev.thumbnail_path}`)}
                        >
                          <img
                            src={`/${ev.thumbnail_path}`}
                            alt="Snapshot Crop"
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                        </div>
                        <div>
                          <p className="text-[11px] font-bold text-slate-200">200x200 Crop Snapshot</p>
                          <p className="text-[10px] text-slate-500 font-mono">
                            Coordinates: {ev.bbox || 'N/A'}
                          </p>
                        </div>
                      </div>

                      <button
                        onClick={() => setSelectedThumb(`/${ev.thumbnail_path}`)}
                        className="px-2.5 py-1 rounded-lg bg-dark-800 hover:bg-dark-700 border border-white/10 text-cyan-300 text-[11px] font-medium transition-colors flex items-center gap-1"
                      >
                        <ImageIcon className="w-3 h-3" />
                        <span>Enlarge</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="py-12 text-center text-slate-500 text-xs">
          No records found for "{selectedObject}" with filter "{filterState}". Place the item in camera view to start tracking.
        </div>
      )}

      {/* Enlarged Image Modal */}
      {selectedThumb && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn"
          onClick={() => setSelectedThumb(null)}
        >
          <div
            className="glass-panel rounded-2xl p-4 max-w-sm w-full border border-white/20 shadow-2xl relative"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-white/10">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-neon-blue" />
                <span>Localized Crop Snapshot</span>
              </h4>
              <button
                onClick={() => setSelectedThumb(null)}
                className="text-slate-400 hover:text-white text-xs font-mono px-2 py-1 rounded bg-white/5"
              >
                ✕
              </button>
            </div>
            <div className="rounded-xl overflow-hidden bg-black flex items-center justify-center aspect-square border border-white/10">
              <img
                src={selectedThumb}
                alt="Object Snapshot"
                className="w-full h-full object-contain"
              />
            </div>
            <p className="text-[11px] text-slate-400 text-center mt-3 font-mono">
              Privacy Protected: 200x200 crop without background scene.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
