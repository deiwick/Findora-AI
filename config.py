import os

# Project root directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
THUMBNAIL_DIR = os.path.join(DATABASE_DIR, "thumbnails")

# Database file path
DB_PATH = os.path.join(DATABASE_DIR, "findora_memory.db")

# YOLOv8 settings
YOLO_MODEL_NAME    = "yolov8n.pt"
YOLO_CONF_THRESHOLD = 0.25       # Enhanced sensitivity for phone/cup/small object recognition

# Display resolution for processed frames
STREAM_WIDTH  = 854
STREAM_HEIGHT = 480

# COCO to Findora target class mapping
# Maps COCO class index -> Standard search label
YOLO_CLASS_MAP = {
    0: "person",
    24: "backpack",
    26: "wallet",       # Mapped from COCO 'handbag'
    28: "umbrella",
    39: "bottle",
    41: "cup",
    45: "bowl",
    56: "chair",
    63: "laptop",
    64: "mouse",
    65: "remote",
    66: "keyboard",
    67: "phone",        # Mapped from COCO 'cell phone'
    73: "book",
    74: "clock",
    75: "vase",
    76: "scissors",
    77: "teddy bear",
    79: "toothbrush"
}

# Stationary detection parameters
STATIONARY_DISTANCE_THRESHOLD = 20.0  # Pixels tolerance for camera shake/noise
STATIONARY_TIME_THRESHOLD = 2.0       # Seconds before an object is marked stationary (faster locking)
LOST_TIMEOUT = 3.5                    # Seconds before a missing track is marked 'lost'

# Camera zone configuration
# ─────────────────────────────────────────────────────────────────────────────
# WEBCAM_INDEX    : OpenCV device index for your laptop/USB webcam (usually 0)
# ESP32_STREAM_URL: Full HTTP URL of your ESP32-CAM MJPEG stream.
#                   Find your ESP32-CAM IP from your router's DHCP table or
#                   from the Serial Monitor after flashing the firmware.
# ─────────────────────────────────────────────────────────────────────────────
CAMERA_SOURCES = {
    "Laptop Zone":    0,                                          # Webcam device index
    "ESP32-CAM Zone": "http://<YOUR_ESP32_IP>/stream"            # Replace <YOUR_ESP32_IP>
}

# Ensure directories exist
os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)
