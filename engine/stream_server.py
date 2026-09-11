"""
Findora AI — MJPEG Stream Server
Serves camera feeds as native browser-renderable MJPEG streams via Flask.
This completely eliminates Streamlit DOM re-rendering for video — the browser
handles the MJPEG natively at 25-30 FPS with zero page flicker.

Usage:
    import engine.stream_server as stream_server
    stream_server.start(engine_instance, port=5001)

Routes:
    /video/laptop   → Laptop Zone MJPEG stream
    /video/esp32    → ESP32-CAM Zone MJPEG stream
    /health         → {"status": "ok"}
"""
import cv2
import time
import threading
import logging
from flask import Flask, Response, jsonify

logger = logging.getLogger(__name__)

_flask_app  = Flask("findora_mjpeg")
_engine_ref = [None]   # mutable list so it can be updated after start()
_server_thread = None
_JPEG_QUALITY  = 80    # 80% JPEG quality — good balance of quality vs bandwidth

# Suppress Flask request logs (they're noisy in Streamlit console)
import logging as _logging
_logging.getLogger("werkzeug").setLevel(_logging.ERROR)


def _gen_frames(room_name: str, fps: int = 25):
    """
    Generator that yields MJPEG frames for a given camera room.
    Runs in a Flask response thread — reads from the engine's shared frame buffer.
    """
    interval = 1.0 / fps
    while True:
        t0     = time.time()
        engine = _engine_ref[0]
        if engine is None:
            time.sleep(0.1)
            continue

        frame = engine.get_latest_frame(room_name)
        if frame is None:
            time.sleep(0.05)
            continue

        # Encode to JPEG — much faster than PNG
        ret, buf = cv2.imencode(".jpg", frame,
                                [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY])
        if ret:
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n"
                   + buf.tobytes()
                   + b"\r\n")

        elapsed = time.time() - t0
        wait    = max(0.0, interval - elapsed)
        if wait > 0:
            time.sleep(wait)


@_flask_app.route("/video/laptop")
def stream_laptop():
    return Response(
        _gen_frames("Laptop Zone", fps=25),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@_flask_app.route("/video/esp32")
def stream_esp32():
    return Response(
        _gen_frames("ESP32-CAM Zone", fps=15),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@_flask_app.route("/health")
def health():
    return jsonify({"status": "ok"})


def start(engine, port: int = 5001):
    """Start the MJPEG stream server in a daemon thread. Safe to call multiple times."""
    global _server_thread
    _engine_ref[0] = engine

    if _server_thread is not None and _server_thread.is_alive():
        logger.info("Stream server already running.")
        return

    _server_thread = threading.Thread(
        target=lambda: _flask_app.run(
            host="0.0.0.0",
            port=port,
            threaded=True,
            use_reloader=False,    # IMPORTANT: prevents Flask from forking a subprocess
            debug=False
        ),
        daemon=True,
        name="MJPEGStreamServer"
    )
    _server_thread.start()
    logger.info(f"MJPEG stream server started on port {port}.")
