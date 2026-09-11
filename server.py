"""
Findora AI — Production FastAPI Server
Serves high-performance MJPEG streams, REST APIs for spatial memory,
natural language search, and static assets for the React UI.
"""
import os
import io
import cv2
import time
import asyncio
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
from database import db
from engine.query import execute_search, parse_natural_query
from engine.vision import VisionEngine

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("findora_server")

# Initialize database
db.init_db()

# Global Vision Engine instance
vision_engine: Optional[VisionEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global vision_engine
    logger.info("Initializing Vision Engine...")
    vision_engine = VisionEngine()
    vision_engine.start()
    logger.info("Vision Engine started on server startup.")
    yield
    if vision_engine and vision_engine.is_running:
        logger.info("Stopping Vision Engine...")
        vision_engine.stop()
        logger.info("Vision Engine stopped.")

app = FastAPI(
    title="Findora AI API",
    description="Edge-AI Spatial Memory Tracker Backend",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for local Vite frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str

# ──────────────────────────────────────────────────────────
# MJPEG Streaming Generators
# ──────────────────────────────────────────────────────────
def generate_mjpeg_stream(room_name: str, fps: int = 25):
    """
    Generator yielding multipart JPEG frames encoded directly from the VisionEngine buffer.
    """
    frame_interval = 1.0 / fps
    while True:
        t0 = time.time()
        if vision_engine is not None and vision_engine.is_running:
            frame = vision_engine.get_latest_frame(room_name)
            if frame is not None:
                ret, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"
                    )
        
        elapsed = time.time() - t0
        sleep_t = max(0.005, frame_interval - elapsed)
        time.sleep(sleep_t)

# ──────────────────────────────────────────────────────────
# Video Stream Endpoints
# ──────────────────────────────────────────────────────────
@app.get("/api/stream/laptop")
def stream_laptop():
    return StreamingResponse(
        generate_mjpeg_stream("Laptop Zone", fps=25),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/stream/esp32")
def stream_esp32():
    return StreamingResponse(
        generate_mjpeg_stream("ESP32-CAM Zone", fps=15),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# ──────────────────────────────────────────────────────────
# System Stats & Health
# ──────────────────────────────────────────────────────────
@app.get("/api/health")
def get_health():
    is_active = vision_engine is not None and vision_engine.is_running
    return {
        "status": "healthy",
        "engine_active": is_active,
        "timestamp": time.time()
    }

@app.get("/api/stats")
def get_stats():
    last_knowns = db.get_last_known_locations()
    total_tracked = len(last_knowns)
    stationary_count = sum(1 for x in last_knowns if x["status"] == "stationary")
    lost_count = sum(1 for x in last_knowns if x["status"] == "lost")
    moved_count = sum(1 for x in last_knowns if x["status"] == "moved")
    
    db_size = db.get_database_size()
    thumbs = os.listdir(config.THUMBNAIL_DIR) if os.path.exists(config.THUMBNAIL_DIR) else []
    
    return {
        "total_tracked": total_tracked,
        "stationary_count": stationary_count,
        "lost_count": lost_count,
        "moved_count": moved_count,
        "engine_active": vision_engine.is_running if vision_engine else False,
        "db_size_kb": round(db_size, 2),
        "thumbnail_count": len(thumbs),
        "camera_sources": config.CAMERA_SOURCES,
        "conf_threshold": config.YOLO_CONF_THRESHOLD,
        "stationary_time_threshold": config.STATIONARY_TIME_THRESHOLD,
        "lost_timeout": config.LOST_TIMEOUT,
        "stream_resolution": f"{config.STREAM_WIDTH}x{config.STREAM_HEIGHT}"
    }

# ──────────────────────────────────────────────────────────
# Spatial Memory & Event Log Endpoints
# ──────────────────────────────────────────────────────────
@app.get("/api/events")
def get_events(limit: int = Query(20, ge=1, le=100)):
    records = db.get_all_records(limit=limit)
    return {
        "events": records,
        "count": len(records)
    }

@app.get("/api/last-known")
def get_last_known():
    records = db.get_last_known_locations()
    return {
        "items": records,
        "count": len(records)
    }

@app.get("/api/objects")
def get_objects():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT object_name FROM findora_memory ORDER BY object_name")
    db_objs = [r[0] for r in cur.fetchall()]
    conn.close()
    
    all_classes = sorted(list(set(db_objs + list(config.YOLO_CLASS_MAP.values()))))
    return {
        "objects": all_classes,
        "active_in_db": db_objs
    }

@app.get("/api/history/{object_name}")
def get_object_history(object_name: str):
    history = db.get_object_history(object_name)
    return {
        "object_name": object_name,
        "history": history,
        "count": len(history)
    }

# ──────────────────────────────────────────────────────────
# Natural Language Search Endpoint
# ──────────────────────────────────────────────────────────
@app.post("/api/search")
def search_memory(payload: SearchRequest):
    query_text = payload.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    result = execute_search(query_text)
    obj_match, room_match = parse_natural_query(query_text)
    
    return {
        "success": result["success"],
        "message": result["message"],
        "data": result["data"],
        "parsed": {
            "object_class": obj_match,
            "room_filter": room_match
        }
    }

# ──────────────────────────────────────────────────────────
# Engine & Memory Controls
# ──────────────────────────────────────────────────────────
@app.post("/api/engine/start")
def start_engine():
    global vision_engine
    if vision_engine is None:
        vision_engine = VisionEngine()
    if not vision_engine.is_running:
        vision_engine.start()
    return {"status": "started", "engine_active": True}

@app.post("/api/engine/stop")
def stop_engine():
    global vision_engine
    if vision_engine and vision_engine.is_running:
        vision_engine.stop()
    return {"status": "stopped", "engine_active": False}

@app.post("/api/engine/restart")
def restart_engine():
    global vision_engine
    if vision_engine and vision_engine.is_running:
        vision_engine.stop()
        time.sleep(0.4)
    vision_engine = VisionEngine()
    vision_engine.start()
    return {"status": "restarted", "engine_active": True}

@app.post("/api/memory/clear")
def clear_memory():
    db.purge_all_logs()
    return {"status": "cleared", "message": "Spatial database and thumbnail snapshots purged."}

# ──────────────────────────────────────────────────────────
# Static Files & Frontend Build Mount
# ──────────────────────────────────────────────────────────
# Mount thumbnails directory so React UI can display cropped images
if os.path.exists(config.THUMBNAIL_DIR):
    app.mount("/database/thumbnails", StaticFiles(directory=config.THUMBNAIL_DIR), name="thumbnails")

# Mount built React frontend if it exists
frontend_dist = os.path.join(config.BASE_DIR, "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
