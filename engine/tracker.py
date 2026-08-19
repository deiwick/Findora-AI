import os
import cv2
import time
import math
import logging
from datetime import datetime
import config
from database import db

logger = logging.getLogger(__name__)

class TrackState:
    def __init__(self, track_id, object_name, confidence, bbox, timestamp):
        self.track_id = track_id
        self.object_name = object_name
        self.confidence = confidence
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.first_seen = timestamp
        self.last_seen = timestamp
        
        # History of centroids: [(timestamp, cx, cy)]
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
        self.centroid_history = [(timestamp, cx, cy)]
        
        # Internal state machine status: 'tracking', 'stationary', 'lost'
        self.status = 'tracking'
        
        # Coordinates at which the object was logged as stationary
        self.last_db_centroid = None
        self.thumbnail_path = None

class StationaryTracker:
    def __init__(self):
        # Maps room_name -> {track_id: TrackState}
        self.active_tracks = {}

    def _calculate_distance(self, p1, p2):
        """Calculates Euclidean distance between two points."""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def _crop_thumbnail(self, frame, bbox):
        """Crops a 200x200px thumbnail centered on the bounding box."""
        h, w, _ = frame.shape
        x1, y1, x2, y2 = map(int, bbox)
        
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        
        # Target crop size
        crop_w, crop_h = 200, 200
        
        # Calculate boundaries
        tx1 = max(0, cx - crop_w // 2)
        ty1 = max(0, cy - crop_h // 2)
        tx2 = min(w, tx1 + crop_w)
        ty2 = min(h, ty1 + crop_h)
        
        # Readjust tx1, ty1 if tx2, ty2 hit image boundary
        if tx2 - tx1 < crop_w:
            tx1 = max(0, tx2 - crop_w)
        if ty2 - ty1 < crop_h:
            ty1 = max(0, ty2 - crop_h)
            
        crop = frame[ty1:ty2, tx1:tx2]
        
        # Resize to exactly 200x200 if boundary conditions caused slightly smaller crop
        if crop.shape[0] != 200 or crop.shape[1] != 200:
            crop = cv2.resize(crop, (200, 200))
            
        return crop

    def update(self, room_name, detections, frame):
        """
        Updates tracking state for a room.
        detections: list of dictionaries: {'track_id': int, 'name': str, 'confidence': float, 'bbox': [x1, y1, x2, y2]}
        frame: OpenCV image frame
        """
        now_time = time.time()
        
        if room_name not in self.active_tracks:
            self.active_tracks[room_name] = {}
            
        current_room_tracks = self.active_tracks[room_name]
        detected_track_ids = set()
        
        # 1. Update detections
        for det in detections:
            track_id = det['track_id']
            name = det['name']
            conf = det['confidence']
            bbox = det['bbox']
            cx = (bbox[0] + bbox[2]) / 2.0
            cy = (bbox[1] + bbox[3]) / 2.0
            
            detected_track_ids.add(track_id)
            
            if track_id not in current_room_tracks:
                # New track
                current_room_tracks[track_id] = TrackState(track_id, name, conf, bbox, now_time)
                logger.info(f"Room {room_name}: New track {track_id} ({name}) registered.")
            else:
                # Existing track - update values
                state = current_room_tracks[track_id]
                state.last_seen = now_time
                state.bbox = bbox
                state.confidence = conf
                state.centroid_history.append((now_time, cx, cy))
                
                # Prune history to sliding window of 1.5 times STATIONARY_TIME_THRESHOLD seconds
                # to ensure we always have points spanning at least STATIONARY_TIME_THRESHOLD.
                state.centroid_history = [
                    pt for pt in state.centroid_history 
                    if now_time - pt[0] <= config.STATIONARY_TIME_THRESHOLD * 1.5
                ]
                
        # 2. Check stationary logic for all active tracks in the room
        for track_id, state in list(current_room_tracks.items()):
            if track_id not in detected_track_ids:
                continue # Handled in the lost logic below
                
            # Filter history to the exact target window for stationary calculation
            window_pts = [
                pt for pt in state.centroid_history 
                if now_time - pt[0] <= config.STATIONARY_TIME_THRESHOLD
            ]
            
            if not window_pts:
                continue
                
            first_t = window_pts[0][0]
            last_t = window_pts[-1][0]
            
            # Require that the target window spans at least STATIONARY_TIME_THRESHOLD
            # or that the total time seen is at least STATIONARY_TIME_THRESHOLD
            if (last_t - first_t >= config.STATIONARY_TIME_THRESHOLD * 0.9) or (now_time - state.first_seen >= config.STATIONARY_TIME_THRESHOLD):
                # Compute maximum centroid shift within window
                centroids = [(pt[1], pt[2]) for pt in window_pts]
                max_dev = 0.0
                for i in range(len(centroids)):
                    for j in range(i + 1, len(centroids)):
                        dist = self._calculate_distance(centroids[i], centroids[j])
                        if dist > max_dev:
                            max_dev = dist
                            
                current_centroid = centroids[-1]
                
                # A. Stationary Condition
                if max_dev <= config.STATIONARY_DISTANCE_THRESHOLD:
                    # Check if we should log to DB
                    # Case 1: Was not stationary before
                    # Case 2: Was stationary, but moved to a new stationary position within the same camera
                    should_log = False
                    if state.status != 'stationary':
                        should_log = True
                    elif state.last_db_centroid is not None:
                        dist_from_last_db = self._calculate_distance(current_centroid, state.last_db_centroid)
                        if dist_from_last_db > config.STATIONARY_DISTANCE_THRESHOLD * 2:
                            should_log = True
                            
                    if should_log:
                        state.status = 'stationary'
                        state.last_db_centroid = current_centroid
                        
                        # Generate thumbnail
                        thumb = self._crop_thumbnail(frame, state.bbox)
                        thumb_name = f"{room_name.replace(' ', '_').lower()}_{state.object_name}_{track_id}_{int(now_time)}.jpg"
                        thumb_path = os.path.join(config.THUMBNAIL_DIR, thumb_name)
                        cv2.imwrite(thumb_path, thumb)
                        state.thumbnail_path = os.path.relpath(thumb_path, config.BASE_DIR)
                        
                        # Write to database
                        db.insert_event(
                            object_name=state.object_name,
                            room_name=room_name,
                            status='stationary',
                            thumbnail_path=state.thumbnail_path,
                            confidence=state.confidence,
                            bbox=state.bbox,
                            track_id=track_id
                        )
                        
                # B. Movement Condition (If it was stationary, but starts moving)
                elif state.status == 'stationary':
                    # Check if it has moved far enough from the locked stationary position
                    if state.last_db_centroid is not None:
                        dist_from_last_db = self._calculate_distance(current_centroid, state.last_db_centroid)
                        if dist_from_last_db > config.STATIONARY_DISTANCE_THRESHOLD * 2:
                            state.status = 'tracking'
                            db.insert_event(
                                object_name=state.object_name,
                                room_name=room_name,
                                status='moved',
                                thumbnail_path=state.thumbnail_path,
                                confidence=state.confidence,
                                bbox=state.bbox,
                                track_id=track_id
                            )
                            state.last_db_centroid = None
                            
        # 3. Handle Lost Tracks (not detected in current frame)
        for track_id, state in list(current_room_tracks.items()):
            if track_id not in detected_track_ids:
                if now_time - state.last_seen >= config.LOST_TIMEOUT:
                    # Object is officially lost (out of frame or obscured)
                    if state.status == 'stationary':
                        # Log lost state to database
                        db.insert_event(
                            object_name=state.object_name,
                            room_name=room_name,
                            status='lost',
                            thumbnail_path=state.thumbnail_path,
                            confidence=state.confidence,
                            bbox=state.bbox,
                            track_id=track_id
                        )
                    # Remove from active track catalog
                    del current_room_tracks[track_id]
                    logger.info(f"Room {room_name}: Track {track_id} ({state.object_name}) removed due to timeout.")
                    
    def get_track_status(self, room_name, track_id):
        """Returns the status of a specific track."""
        if room_name in self.active_tracks and track_id in self.active_tracks[room_name]:
            return self.active_tracks[room_name][track_id].status
        return 'unknown'
