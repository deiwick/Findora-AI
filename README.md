<div align="center">

# 🛡️ Findora AI

### Real-Time Dual-Camera Spatial Memory & Object Tracker

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.0+-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-FF6F00)](https://ultralytics.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3.0+-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-F7DF1E?logo=opensourceinitiative&logoColor=black)](LICENSE)

**Findora AI** is a production-grade, fully on-device **spatial memory system** that tracks physical objects across multiple camera zones in real-time — using YOLOv8 computer vision, a FastAPI backend, and a glassmorphic React dashboard. No cloud. No subscriptions. No privacy trade-offs.

</div>

---

## ✨ What It Does

Findora AI answers the question **"Where did I leave my [phone/keys/cup]?"** by continuously watching camera feeds, detecting when objects become stationary, logging their location with a timestamp and a cropped snapshot, and making all of that instantly searchable through natural language.

> *"Where is my phone?"* → **"Phone was last seen stationary in Laptop Zone at 4:32 PM"** (with thumbnail)

---

## 🏗️ System Architecture

```
┌──────────────────┐    ┌──────────────────┐
│  Laptop Webcam   │    │   ESP32-CAM       │
│  (Zone 1)        │    │   Wi-Fi MJPEG     │
│  USB / DShow     │    │   (Zone 2)        │
└────────┬─────────┘    └────────┬──────────┘
         │  WebcamWorker          │  ESP32Worker
         └──────────┬─────────────┘
                    ▼
         ┌─────────────────────┐
         │   VisionEngine v5   │
         │  Per-camera YOLO    │◄── YOLOv8n (20 classes)
         │  InferenceDispatcher│
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  StationaryTracker  │  2.0s lock threshold
         │  State machine:     │  Stationary → Moved → Lost
         │  centroid history   │
         └──────────┬──────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
 ┌─────────────┐     ┌──────────────────────┐
 │  SQLite DB  │     │  200×200px Thumbnails │
 │  (events +  │     │  (local disk only)    │
 │  locations) │     └──────────────────────┘
 └──────┬──────┘
        ▼
 ┌─────────────────────────────┐
 │   FastAPI Server :8000      │
 │   REST + MJPEG streams      │
 └──────────────┬──────────────┘
                ▼
 ┌──────────────────────────────┐
 │  React Dashboard (Vite)      │
 │  Glassmorphic Dark UI        │
 │  Framer Motion animations    │
 └──────────────────────────────┘
```

---

## 🌟 Features

### 🎥 Real-Time Dual-Camera Ingestion
- Simultaneous feed from **Laptop Webcam** (Zone 1) and **ESP32-CAM Wi-Fi stream** (Zone 2)
- Native browser MJPEG rendering — **zero DOM flicker**, zero re-render lag
- One-click fullscreen expand per camera; reconnect button for unstable streams
- Per-camera isolated YOLOv8 model instances — prevents ByteTrack ID cross-contamination

### 🧠 Spatial Memory & Cross-Zone Handoff
- Object becomes **stationary** → locked location logged with zone, timestamp, confidence, and crop snapshot
- Object moves or exits frame → state transitions: `STATIONARY → MOVED → LOST`
- Object re-enters any zone → new stationary event created, full cross-zone trail maintained

### 🔍 Typo-Tolerant Natural Language Query Engine
- Ask *"where is my phone"*, *"did i leave the cup somewhere"*, *"keybord"* (typo: keyboard)
- Local **Levenshtein distance** fuzzy matching — 100% offline, zero cloud API calls
- Expanded synonym dictionary: phone → mobile, cell, handset; laptop → computer, mac, notebook; etc.
- Returns last-known zone, timestamp, confidence score, and thumbnail preview

### ⏳ Spatial Timeline
- Chronological audit trail of every object displacement across all camera zones
- Filter by object name or status (`STATIONARY` / `MOVED` / `LOST`)
- Expandable thumbnail modal for each event
- Null-safe rendering — no crashes on incomplete database rows

### 📊 Live KPI Dashboard
- **Objects in Memory** — total indexed items
- **Stationary Locked** — objects with confirmed static coordinates
- **Missing / Displaced** — items that have exited camera view
- **Engine Status** — YOLOv8 active / offline indicator with stream resolution

### 🔧 System Controls
- Calibration parameter viewer (confidence threshold, stationary time, lost timeout)
- **One-click Memory Purge** — wipes SQLite database and deletes all thumbnail crops
- Privacy audit panel — confirms zero external data transmission

### 🛡️ 100% On-Device Privacy
- **No cloud API calls** of any kind — inference runs locally on CPU/GPU
- Raw video frames exist only in volatile RAM; never written to disk
- Thumbnails are restricted to `200×200 px` bounding-box crops
- All SQLite data is local to `database/findora_memory.db`
- One-click purge deletes everything permanently

---

## 🎯 Detected Object Classes (YOLOv8n — 20 Classes)

| Category | Objects |
|----------|---------|
| **People** | person |
| **Devices** | laptop, cell phone, keyboard, mouse, remote, clock, tv |
| **Bags** | backpack, handbag, suitcase |
| **Everyday** | book, bottle, cup, chair, umbrella, bowl, vase, teddy bear, toothbrush |

---

## 🛠️ Hardware Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10/11, macOS 13+, Ubuntu 20.04+ |
| **Python** | 3.10 or higher |
| **Node.js** | 18.0 or higher (for frontend build only) |
| **Camera 1** | Built-in or USB webcam (OpenCV device index `0`) |
| **Camera 2** | ESP32-CAM module broadcasting MJPEG stream on local network |
| **RAM** | 4 GB minimum (8 GB recommended) |
| **GPU** | Optional — YOLO runs on CPU by default; CUDA accelerates inference |

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/deiwick/Findora-AI.git
cd Findora-AI
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

> YOLOv8 model weights (`yolov8n.pt`) are **auto-downloaded** by Ultralytics on first run — no manual download needed.

### 3. Build the React Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Configure Your Camera Zones

Open [`config.py`](config.py) and update the ESP32 IP address to match your network:

```python
ESP32_STREAM_URL = "http://192.168.1.7/stream"   # ← change to your ESP32-CAM IP
WEBCAM_INDEX     = 0                               # ← laptop/USB webcam device index
```

### 5. Launch the Application

```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser. That's it! 🎉

---

## 🔧 Frontend Development Mode

For live-reload React development:

```bash
# Terminal 1 — Backend
python -m uvicorn server:app --host 0.0.0.0 --port 8000

# Terminal 2 — Vite Dev Server
cd frontend
npm run dev
```

Open **[http://localhost:5173](http://localhost:5173)** — API calls are proxied to port 8000 automatically.

---

## 📂 Project Structure

```
Findora-AI/
├── server.py                    # FastAPI app — REST API + MJPEG streams
├── config.py                    # All thresholds & hardware config (edit this)
├── requirements.txt             # Python dependencies
│
├── engine/
│   ├── vision.py                # VisionEngine v5: per-camera YOLO + workers
│   ├── tracker.py               # StationaryTracker state machine & crop saver
│   └── query.py                 # Natural language fuzzy search engine
│
├── database/
│   ├── db.py                    # SQLite CRUD: events, locations, history
│   └── thumbnails/              # 200×200px object crop snapshots (gitignored)
│       └── .gitkeep
│
└── frontend/
    ├── src/
    │   ├── App.jsx              # Root component — polling, tabs, toast alerts
    │   ├── index.css            # Glassmorphic dark theme + animation keyframes
    │   └── components/
    │       ├── Header.jsx       # Navigation, clock, engine status badge
    │       ├── KPICards.jsx     # Live metric tiles (4 KPIs)
    │       ├── LiveCameraFeeds.jsx  # Dual MJPEG stream monitors
    │       ├── LiveEventLog.jsx     # Searchable event table + thumbnail modal
    │       ├── ObjectFinder.jsx     # Natural language search UI
    │       ├── SpatialTimeline.jsx  # Chronological object history
    │       └── SystemControls.jsx   # Calibration, purge, privacy panel
    ├── package.json
    ├── tailwind.config.js       # Dark/neon color tokens
    └── vite.config.js           # Dev proxy configuration
```

---

## ⚙️ Configuration Reference

All system parameters live in [`config.py`](config.py):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `WEBCAM_INDEX` | `0` | OpenCV device index for laptop/USB camera |
| `ESP32_STREAM_URL` | `http://192.168.1.7/stream` | ESP32-CAM MJPEG stream URL |
| `YOLO_CONF` | `0.25` | Detection confidence threshold (lower = more detections) |
| `YOLO_IOU` | `0.45` | NMS IoU threshold |
| `STATIONARY_TIME` | `2.0s` | Seconds an object must be still to be logged |
| `LOST_TIMEOUT` | `3.5s` | Seconds before a missing object is marked LOST |
| `MOVEMENT_THRESHOLD` | `15px` | Centroid pixel movement to count as "moved" |
| `THUMBNAIL_SIZE` | `200×200` | Crop snapshot resolution |

---

## 🛡️ Privacy Architecture

Findora AI is designed from the ground up for **maximum privacy**:

1. **No internet connection required** — runs entirely on your local network
2. **No cloud inference** — YOLOv8 runs locally; no frames leave your machine
3. **Volatile frame buffers** — raw video never written to disk
4. **Minimal crops only** — only `200×200 px` bounding-box regions are saved
5. **User-controlled purge** — single button in the dashboard deletes all data instantly
6. **Gitignored by default** — `database/findora_memory.db` and all thumbnails are excluded from version control
7. **No analytics, no telemetry** — the application makes zero external HTTP requests

---

## 🔭 Future Roadmap

| Feature | Status |
|---------|--------|
| 🌐 Multi-room support (3+ cameras) | Planned |
| 🔔 Push notifications when object goes missing | Planned |
| 🗺️ Interactive room floor-plan overlay | Planned |
| 🤖 LLM-powered conversational search ("What moved after 3pm?") | Planned |
| 📱 Mobile companion app (React Native) | Planned |
| 🎯 Custom class training (add your own objects) | Planned |
| 🔐 Password-protected dashboard | Planned |
| ☁️ Optional encrypted cloud sync (opt-in) | Planned |
| 🧩 Home Assistant / MQTT integration | Planned |
| 🖥️ GPU acceleration auto-detection (CUDA/MPS) | Planned |

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push to your branch: `git push origin feature/my-feature`
5. Open a Pull Request

Please ensure your code follows existing patterns and does not include any personal data, `.db` files, or model weights.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Built with ❤️ by [deiwick](https://github.com/deiwick)

*Findora AI — Know where everything is, always.*

</div>
