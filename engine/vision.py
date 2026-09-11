"""
Findora AI - High-Performance Dual Camera Vision Engine (v5)

Features:
1. Rock-solid MJPEG stream parser for ESP32-CAM with automatic byte buffer synchronization.
2. Fast, reliable OpenCV capture for Laptop Webcam using default MSMF backend.
3. Isolated YOLOv8 models per camera zone (no ByteTrack state contamination).
4. Continuous background inference dispatcher.
5. Real-time overlay projection: bounding boxes & trails are drawn directly on every frame served to the browser.
"""
import os
import cv2
import time
import urllib.request
import numpy as np
import threading
import logging
from datetime import datetime
import config
from engine.tracker import StationaryTracker

logger = logging.getLogger(__name__)

_TARGET_CLASSES = list(config.YOLO_CLASS_MAP.keys())
_YOLO_IMGSZ = 416


# ──────────────────────────────────────────────────────────
# Robust MJPEG Stream Reader for ESP32-CAM
# ──────────────────────────────────────────────────────────
def _read_mjpeg_stream(url, frame_callback, stop_event, timeout=10.0):
    """
    Robust HTTP MJPEG stream reader with boundary search and byte buffer persistence.
    Handles slow WiFi, variable frame rates, and chunked transfers cleanly.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FindoraAI/1.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
    except Exception as e:
        logger.warning(f"Failed to connect to MJPEG stream at {url}: {e}")
        return False, str(e)

    logger.info(f"MJPEG stream connected: {url} (Content-Type: {resp.headers.get('Content-Type')})")
    buf = b""
    max_buf_size = 2 * 1024 * 1024  # 2 MB safety cap

    try:
        while not stop_event.is_set():
            try:
                chunk = resp.read(4096)
                if not chunk:
                    logger.warning("MJPEG stream EOF reached.")
                    break
                buf += chunk
            except Exception as e:
                logger.warning(f"Error reading chunk from {url}: {e}")
                break

            # Search and extract all complete JPEG frames in buffer
            while True:
                start_idx = buf.find(b"\xff\xd8")
                if start_idx == -1:
                    # No JPEG start marker; keep only last 2 bytes in case marker is split
                    if len(buf) > 2:
                        buf = buf[-2:]
                    break

                end_idx = buf.find(b"\xff\xd9", start_idx + 2)
                if end_idx == -1:
                    # Start found but waiting for complete end marker
                    if start_idx > 0:
                        buf = buf[start_idx:]  # Discard header/noise before start
                    if len(buf) > max_buf_size:
                        buf = buf[-4096:]  # Buffer overflow prevention
                    break

                # Full JPEG frame extracted
                jpg_data = buf[start_idx : end_idx + 2]
                buf = buf[end_idx + 2 :]

                try:
                    arr = np.frombuffer(jpg_data, dtype=np.uint8)
                    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if frame is not None and frame.size > 0:
                        frame_callback(frame)
                except Exception as decode_err:
                    logger.debug(f"JPEG decode error: {decode_err}")

    except Exception as outer_err:
        logger.warning(f"MJPEG loop error: {outer_err}")
        return False, str(outer_err)
    finally:
        try:
            resp.close()
        except Exception:
            pass

    return True, ""


def _create_diagnostic_frame(room_name, source, status_msg):
    """Generates an informative diagnostic canvas when a camera stream is offline."""
    f = np.zeros((480, 854, 3), dtype=np.uint8) + 20
    cv2.rectangle(f, (0, 0), (854, 45), (35, 35, 35), -1)
    cv2.putText(f, f"{room_name.upper()}  —  {status_msg}", (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (240, 240, 240), 2, cv2.LINE_AA)
    
    src_str = str(source)
    if len(src_str) > 60:
        src_str = src_str[:57] + "..."
    cv2.putText(f, f"Source: {src_str}", (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (160, 160, 160), 1, cv2.LINE_AA)
    cv2.putText(f, f"Status: {status_msg}", (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 165, 255), 2, cv2.LINE_AA)
    cv2.putText(f, f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", (20, 180),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1, cv2.LINE_AA)
    cv2.putText(f, "Attempting continuous background connection...", (20, 440),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1, cv2.LINE_AA)
    return f


# ──────────────────────────────────────────────────────────
# Single Shared Inference Dispatcher (One Model per Camera)
# ──────────────────────────────────────────────────────────
class InferenceDispatcher(threading.Thread):
    def __init__(self, engine):
        super().__init__(name="InferenceDispatcher", daemon=True)
        self.engine = engine
        self.stop_event = threading.Event()
        self._slots = {}
        self._lock = threading.Lock()

    def submit(self, room_name, frame):
        with self._lock:
            self._slots[room_name] = frame

    def run(self):
        logger.info("InferenceDispatcher worker started.")
        while not self.stop_event.is_set():
            with self._lock:
                pending = dict(self._slots)
                self._slots.clear()

            if not pending:
                time.sleep(0.01)
                continue

            for room_name, frame in pending.items():
                if self.stop_event.is_set():
                    break

                model = self.engine.models.get(room_name)
                if model is None:
                    continue

                try:
                    # Run YOLOv8 detection and tracking on dedicated per-room model
                    results = model.track(
                        source=frame,
                        persist=True,
                        conf=config.YOLO_CONF_THRESHOLD,
                        classes=_TARGET_CLASSES,
                        imgsz=_YOLO_IMGSZ,
                        verbose=False
                    )

                    detections = []
                    if results and len(results) > 0 and results[0].boxes is not None:
                        boxes_obj = results[0].boxes
                        if boxes_obj.cls is not None and len(boxes_obj.cls) > 0:
                            boxes_xyxy = boxes_obj.xyxy.cpu().tolist()
                            confs_list = boxes_obj.conf.cpu().tolist()
                            clss_list = boxes_obj.cls.int().cpu().tolist()

                            # Track IDs
                            if boxes_obj.id is not None:
                                ids_list = boxes_obj.id.int().cpu().tolist()
                            else:
                                # Fallback pseudo-IDs based on spatial grid hash
                                ids_list = [
                                    abs(hash((int(b[0]) // 30, int(b[1]) // 30, int(b[2]) // 30, int(b[3]) // 30, c))) % 8000 + 1000
                                    for b, c in zip(boxes_xyxy, clss_list)
                                ]

                            for tid, box, conf, cls_id in zip(ids_list, boxes_xyxy, confs_list, clss_list):
                                if cls_id in config.YOLO_CLASS_MAP:
                                    detections.append({
                                        "track_id": tid,
                                        "name": config.YOLO_CLASS_MAP[cls_id],
                                        "confidence": float(conf),
                                        "bbox": box
                                    })

                    # Update tracker state machine
                    self.engine.tracker.update(room_name, detections, frame)

                except Exception as e:
                    logger.error(f"Inference error on {room_name}: {e}")

        logger.info("InferenceDispatcher stopped.")

    def stop(self):
        self.stop_event.set()


# ──────────────────────────────────────────────────────────
# Webcam Capture Worker
# ──────────────────────────────────────────────────────────
class WebcamWorker(threading.Thread):
    def __init__(self, room_name, index, engine):
        super().__init__(name=f"Webcam-{room_name}", daemon=True)
        self.room_name = room_name
        self.index = index
        self.engine = engine
        self.stop_event = threading.Event()
        self.TARGET_FPS = 25

    def run(self):
        logger.info(f"[{self.room_name}] Webcam worker started (device index {self.index}).")
        
        while not self.stop_event.is_set() and self.engine.is_running:
            cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(self.index)

            if not cap.isOpened():
                logger.warning(f"[{self.room_name}] Cannot open webcam index {self.index}.")
                self.engine.set_raw_frame(self.room_name, _create_diagnostic_frame(self.room_name, self.index, "UNAVAILABLE"))
                time.sleep(1.5)
                continue

            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            logger.info(f"[{self.room_name}] Webcam ready.")
            frame_interval = 1.0 / self.TARGET_FPS

            while not self.stop_event.is_set() and self.engine.is_running:
                t0 = time.time()
                ret, raw = cap.read()
                if not ret or raw is None:
                    logger.warning(f"[{self.room_name}] Frame grab failed. Reconnecting...")
                    break

                # Resize to standard stream resolution
                frame = cv2.resize(raw, (config.STREAM_WIDTH, config.STREAM_HEIGHT))
                self.engine.set_raw_frame(self.room_name, frame)
                self.engine.dispatcher.submit(self.room_name, frame)

                elapsed = time.time() - t0
                sleep_t = max(0.0, frame_interval - elapsed)
                if sleep_t > 0:
                    time.sleep(sleep_t)

            cap.release()
            if not self.stop_event.is_set():
                time.sleep(0.5)

        logger.info(f"[{self.room_name}] Webcam worker stopped.")

    def stop(self):
        self.stop_event.set()


# ──────────────────────────────────────────────────────────
# ESP32-CAM Worker
# ──────────────────────────────────────────────────────────
class ESP32Worker(threading.Thread):
    def __init__(self, room_name, url, engine):
        super().__init__(name=f"ESP32-{room_name}", daemon=True)
        self.room_name = room_name
        self.url = url
        self.engine = engine
        self.stop_event = threading.Event()

    def _on_frame(self, raw_frame):
        frame = cv2.resize(raw_frame, (config.STREAM_WIDTH, config.STREAM_HEIGHT))
        self.engine.set_raw_frame(self.room_name, frame)
        self.engine.dispatcher.submit(self.room_name, frame)

    def run(self):
        logger.info(f"[{self.room_name}] ESP32 worker started: {self.url}")
        
        while not self.stop_event.is_set() and self.engine.is_running:
            self.engine.set_raw_frame(self.room_name, _create_diagnostic_frame(self.room_name, self.url, "CONNECTING..."))
            
            # Read MJPEG stream with auto-reconnect
            success, err = _read_mjpeg_stream(self.url, self._on_frame, self.stop_event, timeout=10.0)
            
            if not success and not self.stop_event.is_set():
                self.engine.set_raw_frame(self.room_name, _create_diagnostic_frame(self.room_name, self.url, f"OFFLINE ({err[:35]})"))
                time.sleep(2.0)

        logger.info(f"[{self.room_name}] ESP32 worker stopped.")

    def stop(self):
        self.stop_event.set()


# ──────────────────────────────────────────────────────────
# VisionEngine Central Orchestrator
# ──────────────────────────────────────────────────────────
class VisionEngine:
    def __init__(self):
        self.tracker = StationaryTracker()
        self.is_running = False

        self.raw_frames = {}
        self.frame_lock = threading.Lock()

        self.camera_workers = {}
        self.dispatcher = None
        self.models = {}
        self.model = None

        # Load YOLOv8 models (one instance per camera zone)
        try:
            from ultralytics import YOLO
            os.environ["YOLO_VERBOSE"] = "False"
            dummy = np.zeros((_YOLO_IMGSZ, _YOLO_IMGSZ, 3), dtype=np.uint8)

            for room_name in config.CAMERA_SOURCES:
                m = YOLO(config.YOLO_MODEL_NAME)
                # Model warm-up
                m.track(source=dummy, persist=False, conf=0.9, classes=_TARGET_CLASSES, imgsz=_YOLO_IMGSZ, verbose=False)
                self.models[room_name] = m
                logger.info(f"YOLOv8 initialized for zone '{room_name}'.")

            self.model = next(iter(self.models.values()), None)
        except Exception as e:
            logger.error(f"Failed to load YOLO models: {e}")

    def set_raw_frame(self, room_name, frame):
        with self.frame_lock:
            self.raw_frames[room_name] = frame

    def get_latest_frame(self, room_name):
        """
        Returns the latest camera frame with real-time bounding boxes, trails,
        and status badges rendered directly on top.
        """
        with self.frame_lock:
            raw = self.raw_frames.get(room_name)
            if raw is None:
                return None
            frame = raw.copy()

        # Render overlays directly on frame
        active_tracks = self.tracker.active_tracks.get(room_name, {})
        for tid, state in active_tracks.items():
            x1, y1, x2, y2 = map(int, state.bbox)

            # Color scheme: Green = Stationary, Orange = Tracking/Moving, Red = Lost
            if state.status == "stationary":
                color = (45, 215, 45)      # Vibrant Green
                badge_text = "STATIONARY"
            elif state.status == "tracking":
                color = (0, 165, 255)       # Amber / Orange
                badge_text = "TRACKING"
            else:
                color = (50, 50, 220)       # Red
                badge_text = "LOST"

            # 1. Centroid Motion Trail
            trail = state.centroid_history
            for i in range(1, len(trail)):
                p1 = (int(trail[i - 1][1]), int(trail[i - 1][2]))
                p2 = (int(trail[i][1]), int(trail[i][2]))
                thickness = max(1, int(1 + (i / len(trail)) * 2))
                cv2.line(frame, p1, p2, (0, 140, 255), thickness)
            if trail:
                cv2.circle(frame, (int(trail[-1][1]), int(trail[-1][2])), 5, (0, 220, 255), -1)

            # 2. Bounding Box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # 3. Label Badge Header
            label = f"{state.object_name.upper()} #{tid} [{badge_text}] {state.confidence * 100:.0f}%"
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.46, 1)
            ty = max(0, y1 - lh - 6)
            cv2.rectangle(frame, (x1, ty), (x1 + lw + 6, y1), color, -1)
            cv2.putText(frame, label, (x1 + 3, max(12, y1 - 3)), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1, cv2.LINE_AA)

        # Zone Header Banner
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 28), (0, 0, 0), -1)
        cv2.circle(frame, (12, 14), 5, (0, 255, 0), -1)
        cv2.putText(frame, f"{room_name.upper()}  |  LIVE", (26, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1, cv2.LINE_AA)

        return frame

    def start(self):
        if self.is_running:
            return
        self.is_running = True

        # Start single inference dispatcher
        self.dispatcher = InferenceDispatcher(self)
        self.dispatcher.start()

        # Start capture workers
        for room_name, source in config.CAMERA_SOURCES.items():
            if isinstance(source, int):
                w = WebcamWorker(room_name, source, self)
            else:
                w = ESP32Worker(room_name, source, self)
            w.start()
            self.camera_workers[room_name] = w

        logger.info("VisionEngine started successfully.")

    def stop(self):
        if not self.is_running:
            return
        self.is_running = False

        if self.dispatcher:
            self.dispatcher.stop()
        for w in self.camera_workers.values():
            w.stop()

        if self.dispatcher and self.dispatcher.is_alive():
            self.dispatcher.join(timeout=2.0)
        for w in self.camera_workers.values():
            if w.is_alive():
                w.join(timeout=2.0)

        self.camera_workers.clear()
        self.dispatcher = None
        logger.info("VisionEngine stopped.")