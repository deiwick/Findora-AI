import sqlite3
import os
import glob
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database and creates the findora_memory table."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create the memory events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS findora_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_name TEXT NOT NULL,
            room_name TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            status TEXT NOT NULL, -- 'stationary', 'moved', 'lost'
            thumbnail_path TEXT,
            confidence REAL,
            bbox TEXT,            -- Saved as 'x1,y1,x2,y2'
            track_id INTEGER
        )
    """)
    
    # Create indexes for optimized queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_object_name ON findora_memory(object_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON findora_memory(timestamp)")
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

def insert_event(object_name, room_name, status, thumbnail_path, confidence, bbox, track_id, timestamp=None):
    """Inserts a state event into the database."""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(timestamp, datetime):
        timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
    conn = get_connection()
    cursor = conn.cursor()
    
    bbox_str = ",".join(map(str, bbox)) if bbox else None
    
    cursor.execute("""
        INSERT INTO findora_memory (object_name, room_name, timestamp, status, thumbnail_path, confidence, bbox, track_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (object_name.lower(), room_name, timestamp, status, thumbnail_path, confidence, bbox_str, track_id))
    
    conn.commit()
    conn.close()
    logger.info(f"DB Log: {object_name} is '{status}' in {room_name} (track {track_id})")

def get_last_known_locations():
    """Retrieves the latest state/event of every tracked object."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Gets the latest entry for each object_name using max ID
    cursor.execute("""
        SELECT id, object_name, room_name, timestamp, status, thumbnail_path, confidence, bbox, track_id
        FROM findora_memory
        WHERE id IN (
            SELECT MAX(id) FROM findora_memory GROUP BY object_name
        )
        ORDER BY timestamp DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_object_history(object_name):
    """Retrieves the temporal history of a specific object."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT room_name, timestamp, status, confidence, bbox, thumbnail_path, track_id
        FROM findora_memory
        WHERE object_name = ?
        ORDER BY timestamp DESC
    """, (object_name.lower(),))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def purge_all_logs():
    """Deletes all events from database and purges local thumbnail files."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM findora_memory")
    conn.commit()
    conn.close()
    
    # Remove files from config.THUMBNAIL_DIR
    files = glob.glob(os.path.join(config.THUMBNAIL_DIR, "*"))
    for f in files:
        try:
            os.remove(f)
        except Exception as e:
            logger.error(f"Failed to delete {f}: {e}")
            
    logger.info("Database and thumbnails purged successfully.")

def get_database_size():
    """Returns database size in KB."""
    if os.path.exists(config.DB_PATH):
        return os.path.getsize(config.DB_PATH) / 1024.0
    return 0.0

def get_all_records(limit=100):
    """Retrieves all memory log records for the system audit feed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, object_name, room_name, timestamp, status, confidence, track_id
        FROM findora_memory
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
