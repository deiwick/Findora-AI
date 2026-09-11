import React, { useState } from 'react';
import { Video, Wifi, Maximize2, Minimize2, Camera, AlertCircle, RefreshCw, Eye } from 'lucide-react';

export default function LiveCameraFeeds({ stats }) {
  const [fullscreenCam, setFullscreenCam] = useState(null);
  const [keyLaptop, setKeyLaptop] = useState(Date.now());
  const [keyEsp32, setKeyEsp32] = useState(Date.now());

  const engineActive = stats?.engine_active ?? false;

  const reloadStream = (cam) => {
    if (cam === 'laptop') setKeyLaptop(Date.now());
    if (cam === 'esp32') setKeyEsp32(Date.now());
  };

  const cameras = [
    {
      id: 'laptop',
      name: 'Camera 1: Laptop Zone',
      source: stats?.camera_sources?.['Laptop Zone'] ?? 'Webcam Device 0',
      type: 'Built-in USB / DShow',
      streamUrl: `/api/stream/laptop?t=${keyLaptop}`,
      fps: '~25 FPS',
      accentColor: 'border-cyan-500/40',
      glowColor: 'shadow-neon-blue',
      badgeBg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    },
    {
      id: 'esp32',
      name: 'Camera 2: ESP32-CAM Zone',
      source: stats?.camera_sources?.['ESP32-CAM Zone'] ?? 'http://192.168.1.7/stream',
      type: 'Wi-Fi MJPEG Stream',
      streamUrl: `/api/stream/esp32?t=${keyEsp32}`,
      fps: '~15 FPS',
      accentColor: 'border-emerald-500/40',
      glowColor: 'shadow-neon-green',
      badgeBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    },
  ];

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Video className="w-5 h-5 text-neon-blue" />
            <span>Real-Time Dual-Camera Spatial Ingestion</span>
          </h2>
          <p className="text-xs text-slate-400">
            Hardware-accelerated native browser streaming with 0 ms DOM lag & continuous YOLOv8 tracking
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-dark-800 border border-white/10 text-xs font-mono text-slate-300">
            <span className="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
            <span>Native MJPEG Stream</span>
          </span>
        </div>
      </div>

      {/* Camera Grid */}
      <div className={`grid gap-6 ${fullscreenCam ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2'}`}>
        {cameras
          .filter((cam) => !fullscreenCam || fullscreenCam === cam.id)
          .map((cam) => {
            const isFull = fullscreenCam === cam.id;
            return (
              <div
                key={cam.id}
                className={`glass-panel rounded-2xl overflow-hidden border ${cam.accentColor} transition-all duration-300 relative group flex flex-col`}
              >
                {/* Camera Card Header */}
                <div className="flex items-center justify-between px-4 py-3 bg-dark-800/90 border-b border-white/10">
                  <div className="flex items-center gap-2.5">
                    <span className="flex h-2.5 w-2.5 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon-green opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-neon-green"></span>
                    </span>
                    <div>
                      <h3 className="text-xs font-bold text-slate-100 tracking-wide">
                        {cam.name}
                      </h3>
                      <p className="text-[10px] font-mono text-slate-400 truncate max-w-[240px]">
                        {cam.source}
                      </p>
                    </div>
                  </div>

                  {/* Actions & Badges */}
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 text-[10px] font-mono font-semibold rounded-full border ${cam.badgeBg}`}>
                      {cam.fps}
                    </span>
                    <button
                      onClick={() => reloadStream(cam.id)}
                      title="Reconnect Stream"
                      className="p-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 text-slate-400 hover:text-white transition-colors"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => setFullscreenCam(isFull ? null : cam.id)}
                      title={isFull ? 'Exit Fullscreen' : 'Expand View'}
                      className="p-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 text-slate-400 hover:text-white transition-colors"
                    >
                      {isFull ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Video Feed Screen */}
                <div className="relative bg-black aspect-video flex items-center justify-center overflow-hidden">
                  {engineActive ? (
                    <img
                      src={cam.streamUrl}
                      alt={cam.name}
                      className="w-full h-full object-contain"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        const fallback = e.target.nextSibling;
                        if (fallback) fallback.style.display = 'flex';
                      }}
                    />
                  ) : null}

                  {/* Offline / Reconnecting Fallback */}
                  <div
                    className="absolute inset-0 bg-dark-900/95 flex flex-col items-center justify-center gap-3 p-6 text-center"
                    style={{ display: engineActive ? 'none' : 'flex' }}
                  >
                    <div className="p-3 rounded-full bg-dark-800 border border-white/10 text-amber-400">
                      <AlertCircle className="w-6 h-6" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-white">Stream Connecting / Standby</h4>
                      <p className="text-xs text-slate-400 mt-1 max-w-sm">
                        Waiting for camera frame buffer. Background thread will reconnect automatically.
                      </p>
                    </div>
                    <button
                      onClick={() => reloadStream(cam.id)}
                      className="px-3 py-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 border border-white/10 text-xs text-cyan-300 font-medium transition-colors flex items-center gap-1.5"
                    >
                      <RefreshCw className="w-3 h-3" />
                      <span>Retry Connection</span>
                    </button>
                  </div>

                  {/* Live HUD Watermark */}
                  <div className="absolute bottom-2 left-2 pointer-events-none flex items-center gap-1.5 px-2 py-0.5 rounded bg-black/60 backdrop-blur border border-white/10 text-[10px] font-mono text-slate-300">
                    <span className="w-1.5 h-1.5 rounded-full bg-neon-green animate-pulse" />
                    <span>EDGE-AI LIVE TRACKER</span>
                  </div>
                </div>

                {/* Card Footer Info */}
                <div className="px-4 py-2 bg-dark-900/90 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                  <span>Type: {cam.type}</span>
                  <span className="text-slate-500">Auto-Reconnection: ON</span>
                </div>
              </div>
            );
          })}
      </div>
    </div>
  );
}
