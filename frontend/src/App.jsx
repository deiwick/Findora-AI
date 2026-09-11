import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import KPICards from './components/KPICards';
import LiveCameraFeeds from './components/LiveCameraFeeds';
import LiveEventLog from './components/LiveEventLog';
import ObjectFinder from './components/ObjectFinder';
import SpatialTimeline from './components/SpatialTimeline';
import SystemControls from './components/SystemControls';

export default function App() {
  const [activeTab, setActiveTab] = useState('live');
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg, type = 'info') => {
    setToastMessage({ msg, type });
    setTimeout(() => setToastMessage(null), 3500);
  };

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch('/api/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  }, []);

  const fetchEvents = useCallback(async () => {
    try {
      const res = await fetch('/api/events?limit=25');
      if (res.ok) {
        const data = await res.json();
        setEvents(data.events || []);
      }
    } catch (err) {
      console.error('Error fetching events:', err);
    }
  }, []);

  // Polling loop for background stats and event log updates
  useEffect(() => {
    fetchStats();
    fetchEvents();

    const interval = setInterval(() => {
      fetchStats();
      fetchEvents();
    }, 2500);

    return () => clearInterval(interval);
  }, [fetchStats, fetchEvents]);

  // Restart Engine Action
  const handleRestartEngine = async () => {
    showToast('Restarting Vision Engine...', 'info');
    try {
      const res = await fetch('/api/engine/restart', { method: 'POST' });
      if (res.ok) {
        showToast('Vision Engine successfully restarted!', 'success');
        fetchStats();
      }
    } catch (err) {
      showToast('Failed to restart Vision Engine.', 'error');
    }
  };

  // Toggle Engine (Start / Stop) Action
  const handleToggleEngine = async () => {
    const isRunning = stats?.engine_active ?? false;
    const endpoint = isRunning ? '/api/engine/stop' : '/api/engine/start';
    try {
      const res = await fetch(endpoint, { method: 'POST' });
      if (res.ok) {
        showToast(isRunning ? 'Vision Engine stopped.' : 'Vision Engine started.', 'info');
        fetchStats();
      }
    } catch (err) {
      showToast('Failed to toggle engine state.', 'error');
    }
  };

  // Clear Spatial Memory Action
  const handleClearMemory = async () => {
    try {
      const res = await fetch('/api/memory/clear', { method: 'POST' });
      if (res.ok) {
        showToast('Spatial Memory & snapshots cleared.', 'success');
        fetchStats();
        fetchEvents();
      }
    } catch (err) {
      showToast('Failed to clear spatial memory.', 'error');
    }
  };

  return (
    <div className="min-h-screen bg-dark-900 text-slate-100 flex flex-col">
      {/* Top Navigation & Status Bar */}
      <Header
        stats={stats}
        onRestartEngine={handleRestartEngine}
        onToggleEngine={handleToggleEngine}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 pb-12">
        {/* Metric KPI Banner */}
        <KPICards stats={stats} />

        {/* Tab 1: Live Feeds & Memory Log */}
        {activeTab === 'live' && (
          <div className="animate-fadeIn">
            <LiveCameraFeeds stats={stats} />
            <LiveEventLog events={events} onRefresh={fetchEvents} />
          </div>
        )}

        {/* Tab 2: AI Object Finder */}
        {activeTab === 'search' && (
          <div className="animate-fadeIn">
            <ObjectFinder />
          </div>
        )}

        {/* Tab 3: Spatial Timeline */}
        {activeTab === 'timeline' && (
          <div className="animate-fadeIn">
            <SpatialTimeline />
          </div>
        )}

        {/* Tab 4: System Controls & Privacy */}
        {activeTab === 'controls' && (
          <div className="animate-fadeIn">
            <SystemControls
              stats={stats}
              onRestartEngine={handleRestartEngine}
              onClearMemory={handleClearMemory}
            />
          </div>
        )}
      </main>

      {/* Floating Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 animate-bounce">
          <div
            className={`px-4 py-2.5 rounded-xl text-xs font-semibold shadow-2xl border ${
              toastMessage.type === 'error'
                ? 'bg-red-500/90 text-white border-red-400'
                : toastMessage.type === 'success'
                ? 'bg-emerald-500/90 text-white border-emerald-400'
                : 'bg-cyan-500/90 text-white border-cyan-400'
            }`}
          >
            {toastMessage.msg}
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-white/5 py-4 text-center text-xs text-slate-600 font-mono">
        Findora AI — Edge-AI Spatial Memory Architecture · Local SQLite & YOLOv8n
      </footer>
    </div>
  );
}
