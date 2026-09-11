import React, { useState } from 'react';
import { Search, Sparkles, MapPin, Tag, Clock, CheckCircle2, AlertCircle, Info, Image as ImageIcon, X, ArrowRight, CornerDownLeft } from 'lucide-react';

export default function ObjectFinder() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const suggestions = [
    'Where is my phone?',
    'Where did I put the cup?',
    'Is the book in Laptop Zone?',
    'Did I leave my backpack in ESP32 Zone?',
    'where is my phn? (Typo Test)',
    'where is my water bottle?',
    'find my laptop',
    'is the mouse in Laptop Zone?'
  ];

  const handleSearch = async (textToSearch) => {
    const q = textToSearch || query;
    if (!q || !q.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q.trim() }),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError('Failed to connect to spatial search engine.');
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (sug) => {
    // Remove (Typo Test) annotation if present for searching
    const cleanQuery = sug.replace(/\s*\(Typo Test\)/i, '');
    setQuery(cleanQuery);
    handleSearch(cleanQuery);
  };

  return (
    <div className="glass-panel rounded-2xl p-6 lg:p-8 mb-8 border border-white/10">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="w-5 h-5 text-neon-blue" />
          <h2 className="text-xl font-bold text-white">
            Natural Language Spatial Query Engine
          </h2>
        </div>
        <p className="text-xs text-slate-400">
          Ask Findora where your tracked items are. Features instant typo tolerance via local Levenshtein tokenization.
        </p>
      </div>

      {/* Suggested Query Chips */}
      <div className="mb-4">
        <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
          Quick Search Templates:
        </span>
        <div className="flex flex-wrap gap-2">
          {suggestions.map((sug, idx) => (
            <button
              key={idx}
              onClick={() => handleSuggestionClick(sug)}
              className="px-3 py-1.5 rounded-xl bg-dark-800 hover:bg-dark-700 border border-white/10 hover:border-cyan-500/40 text-xs font-medium text-slate-300 hover:text-cyan-300 transition-all duration-200 text-left flex items-center gap-1.5"
            >
              <span>{sug}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Search Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSearch();
        }}
        className="flex gap-2 mb-8"
      >
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="e.g. Where is my cell phone? / Did I leave the cup in ESP32 Zone?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-10 pr-10 py-3 rounded-xl bg-dark-800/90 border border-white/15 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 transition-all"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 p-1"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold uppercase tracking-wider shadow-neon-blue transition-all disabled:opacity-50 flex items-center gap-2"
        >
          <span>{loading ? 'Searching...' : 'Locate Item'}</span>
          <CornerDownLeft className="w-3.5 h-3.5" />
        </button>
      </form>

      {/* Results View */}
      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2 mb-6">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
          {/* Main Answer Card */}
          <div className="lg:col-span-2 glass-card rounded-2xl p-6 border border-white/10 relative overflow-hidden">
            {result.success ? (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span className="p-1.5 rounded-lg bg-emerald-500/10 text-neon-green border border-emerald-500/30">
                    <CheckCircle2 className="w-4 h-4" />
                  </span>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    Findora Memory Response
                  </h3>
                </div>

                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-semibold text-sm mb-5 leading-relaxed">
                  {result.message}
                </div>

                {result.data && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Metadata */}
                    <div className="space-y-2.5 text-xs text-slate-300">
                      <div className="flex items-center justify-between p-2.5 rounded-lg bg-dark-800/80 border border-white/5">
                        <span className="text-slate-400">Zone / Room:</span>
                        <span className="font-bold text-white flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                          {result.data.room_name}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-2.5 rounded-lg bg-dark-800/80 border border-white/5">
                        <span className="text-slate-400">State Status:</span>
                        <span className={`font-bold uppercase ${
                          result.data.status === 'stationary'
                            ? 'text-neon-green'
                            : result.data.status === 'moved'
                            ? 'text-neon-amber'
                            : 'text-neon-red'
                        }`}>
                          {result.data.status}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-2.5 rounded-lg bg-dark-800/80 border border-white/5">
                        <span className="text-slate-400">Timestamp:</span>
                        <span className="font-mono text-slate-300">
                          {result.data.timestamp}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-2.5 rounded-lg bg-dark-800/80 border border-white/5">
                        <span className="text-slate-400">Confidence:</span>
                        <span className="font-bold text-cyan-300">
                          {result.data.confidence != null ? `${(result.data.confidence * 100).toFixed(1)}%` : '—'}
                        </span>
                      </div>
                    </div>

                    {/* Snapshot Preview */}
                    <div className="flex flex-col items-center justify-center p-3 rounded-xl bg-dark-800/80 border border-white/5">
                      <p className="text-[11px] font-mono text-slate-400 mb-2">
                        Real-Time Crop Snapshot
                      </p>
                      {result.data.thumbnail_path ? (
                        <div className="w-32 h-32 rounded-lg overflow-hidden border border-white/10 bg-black">
                          <img
                            src={`/${result.data.thumbnail_path}`}
                            alt={result.data.object_name}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.src = 'https://via.placeholder.com/128?text=Crop+Missing';
                            }}
                          />
                        </div>
                      ) : (
                        <div className="w-32 h-32 rounded-lg border border-dashed border-white/10 flex items-center justify-center text-slate-600 text-[11px]">
                          No Thumbnail
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span className="p-1.5 rounded-lg bg-red-500/10 text-neon-red border border-red-500/30">
                    <AlertCircle className="w-4 h-4" />
                  </span>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    Query Not Resolved
                  </h3>
                </div>
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs font-medium leading-relaxed">
                  {result.message}
                </div>
              </div>
            )}
          </div>

          {/* AI Parser Debug Card */}
          <div className="glass-card rounded-2xl p-6 border border-white/10">
            <div className="flex items-center gap-2 mb-4">
              <Info className="w-4 h-4 text-cyan-400" />
              <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                Edge-AI Parser Breakdown
              </h4>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-400 text-[11px] block">Target Entity Class:</span>
                <span className="font-mono text-cyan-300 font-semibold text-sm">
                  {result.parsed?.object_class?.toUpperCase() || 'UNIDENTIFIED'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 text-[11px] block">Target Zone Filter:</span>
                <span className="font-mono text-emerald-300 font-semibold text-sm">
                  {result.parsed?.room_filter?.toUpperCase() || 'ALL ZONES'}
                </span>
              </div>
              <div className="pt-3 border-t border-white/5 text-[11px] text-slate-400">
                <p>
                  Zero external cloud NLP calls. Tokenized via fuzzy string distance algorithms against target household items.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
