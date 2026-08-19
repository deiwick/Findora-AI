import os

# Project root directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
THUMBNAIL_DIR = os.path.join(DATABASE_DIR, "thumbnails")

# Database file path
DB_PATH = os.path.join(DATABASE_DIR, "findora_memory.db")

# YOLOv8 settings
YOLO_MODEL_NAME = "yolov8n.pt"
YOLO_CONF_THRESHOLD = 0.25

# COCO to Findora target class mapping
# Maps COCO class index -> Standard search label
YOLO_CLASS_MAP = {
    24: "backpack",
    26: "wallet",      # Mapped from COCO 'handbag'
    39: "bottle",
    41: "cup",
    63: "laptop",
    65: "remote",
    67: "phone",       # Mapped from COCO 'cell phone'
    73: "book",
    76: "scissors"
}

# Stationary detection parameters
STATIONARY_DISTANCE_THRESHOLD = 8.0  # Max pixel deviation to count as stationary
STATIONARY_TIME_THRESHOLD = 3.0      # Consecutive seconds required to mark stationary
LOST_TIMEOUT = 5.0                   # Seconds after which a missing track is marked 'lost'

# Simulated camera sources
# Maps room name to file path or camera index
CAMERA_SOURCES = {
    "Living Room": "room_living.mp4",
    "Bedroom": "room_bedroom.mp4"
}

# Ensure directories exist
os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)
