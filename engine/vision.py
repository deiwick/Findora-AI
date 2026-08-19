import os
import cv2
import time
import numpy as np
import threading
import logging
import config
from engine.tracker import StationaryTracker

logger = logging.getLogger(__name__)

class VisionEngine:
    def __init__(self):
        self.tracker = StationaryTracker()
        self.is_running = False
        self.latest_frames = {}  # Maps room_name -> cv2 frame
        self.thread = None
        self.lock = threading.Lock()
        
        # Load YOLO model safely
        self.model = None
        try:
            from ultralytics import YOLO
            os.environ["YOLO_VERBOSE"] = "False"
            self.model = YOLO(config.YOLO_MODEL_NAME)
            logger.info("YOLOv8 model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load YOLOv8 model: {e}. Running in simulation mode.")

    def start(self):
        """Starts the background vision processing thread."""
        with self.lock:
            if not self.is_running:
                self.is_running = True
                self.thread = threading.Thread(target=self.run, daemon=True)
                self.thread.start()
                logger.info("Vision Engine started in background.")

    def stop(self):
        """Stops the background vision processing thread."""
        with self.lock:
            if self.is_running:
                self.is_running = False
                if self.thread:
                    self.thread.join(timeout=2.0)
                logger.info("Vision Engine stopped.")

    def _draw_room_background(self, room_name):
        """Renders a beautiful 2D perspective interior for the room."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Floor (Soft warm grey)
        cv2.rectangle(frame, (0, 240), (640, 480), (220, 215, 210), -1)
        
        # Walls (Soft blue-grey wallpaper)
        cv2.rectangle(frame, (0, 0), (640, 240), (145, 130, 115), -1)
        
        # Wall baseboard separator
        cv2.line(frame, (0, 240), (640, 240), (90, 80, 75), 3)

        if room_name == "Living Room":
            # Draw Rug (Warm beige oval)
            cv2.ellipse(frame, (320, 380), (260, 80), 0, 0, 360, (180, 190, 205), -1)
            cv2.ellipse(frame, (320, 380), (260, 80), 0, 0, 360, (140, 150, 165), 2)
            
            # Sofa (Brown wood base, orange/brown cushions)
            # Base board
            cv2.rectangle(frame, (100, 350), (540, 430), (50, 65, 85), -1)
            # Backrest cushions
            cv2.rectangle(frame, (120, 270), (250, 350), (70, 90, 120), -1)
            cv2.rectangle(frame, (250, 270), (380, 350), (70, 90, 120), -1)
            cv2.rectangle(frame, (380, 270), (510, 350), (70, 90, 120), -1)
            # Armrests
            cv2.rectangle(frame, (80, 310), (120, 430), (50, 65, 85), -1)
            cv2.rectangle(frame, (510, 310), (550, 430), (50, 65, 85), -1)
            # Seat cushions
            cv2.rectangle(frame, (120, 350), (250, 420), (85, 110, 145), -1)
            cv2.rectangle(frame, (250, 350), (380, 420), (85, 110, 145), -1)
            cv2.rectangle(frame, (380, 350), (510, 420), (85, 110, 145), -1)
            
            # Draw Table (Brown wood table)
            # Legs
            cv2.rectangle(frame, (220, 250), (235, 310), (50, 50, 50), -1)
            cv2.rectangle(frame, (400, 250), (415, 310), (50, 50, 50), -1)
            # Tabletop
            cv2.rectangle(frame, (180, 240), (450, 255), (40, 70, 110), -1)
            
            # Wall art/painting
            cv2.rectangle(frame, (260, 60), (380, 150), (60, 130, 80), -1)
            cv2.rectangle(frame, (260, 60), (380, 150), (40, 50, 60), 3) # Frame
            cv2.circle(frame, (320, 105), 15, (0, 230, 255), -1) # Sun
            cv2.line(frame, (265, 145), (320, 115), (50, 90, 60), 2) # Hill
            cv2.line(frame, (375, 145), (320, 115), (50, 90, 60), 2)
            
        elif room_name == "Bedroom":
            # Draw Window (with outdoor sky view)
            cv2.rectangle(frame, (450, 40), (580, 180), (255, 235, 180), -1) # Wall window light
            cv2.rectangle(frame, (460, 50), (570, 170), (250, 180, 100), -1) # Sky color
            cv2.line(frame, (515, 50), (515, 170), (255, 235, 180), 2)
            cv2.line(frame, (460, 110), (570, 110), (255, 235, 180), 2)
            
            # Draw Bed (Teal comforter, white pillows)
            # Frame base
            cv2.rectangle(frame, (60, 220), (340, 460), (50, 50, 60), -1)
            # Mattress / Sheets
            cv2.rectangle(frame, (80, 240), (340, 450), (240, 240, 245), -1)
            # Pillows
            cv2.rectangle(frame, (90, 250), (140, 330), (220, 220, 220), -1)
            cv2.rectangle(frame, (90, 350), (140, 430), (220, 220, 220), -1)
            # Quilt/Blanket
            cv2.rectangle(frame, (150, 240), (340, 450), (140, 110, 70), -1)
            
            # Draw Desk
            # Legs
            cv2.rectangle(frame, (410, 270), (425, 390), (40, 40, 40), -1)
            cv2.rectangle(frame, (570, 270), (585, 390), (40, 40, 40), -1)
            # Desktop
            cv2.rectangle(frame, (380, 260), (600, 275), (45, 80, 120), -1)
            
        return frame

    def _draw_cup(self, frame, x, y):
        """Draws a stylized blue coffee cup."""
        # Body
        cv2.rectangle(frame, (x - 12, y - 16), (x + 12, y + 16), (200, 110, 45), -1)
        # Handle
        cv2.ellipse(frame, (x + 12, y), (8, 10), 0, 270, 90, (200, 110, 45), 3)
        # Rim
        cv2.ellipse(frame, (x, y - 16), (12, 3), 0, 0, 360, (235, 175, 140), -1)

    def _draw_phone(self, frame, x, y):
        """Draws a stylized smartphone with a glowing wallpaper."""
        # Phone body
        cv2.rectangle(frame, (x - 12, y - 20), (x + 12, y + 20), (30, 30, 30), -1)
        # Screen glow
        cv2.rectangle(frame, (x - 10, y - 18), (x + 10, y + 18), (250, 220, 80), -1)
        # Screen wallpaper details
        cv2.circle(frame, (x, y - 5), 6, (180, 100, 50), -1)
        cv2.line(frame, (x - 10, y + 10), (x + 10, y + 10), (255, 255, 255), 1)
        # Speaker notch
        cv2.line(frame, (x - 4, y - 19), (x + 4, y - 19), (0, 0, 0), 1)

    def _draw_laptop(self, frame, x, y):
        """Draws an open silver laptop."""
        # Base
        cv2.rectangle(frame, (x - 35, y), (x + 35, y + 6), (200, 200, 205), -1)
        # Trackpad
        cv2.rectangle(frame, (x - 10, y), (x + 10, y + 3), (160, 160, 165), -1)
        # Screen lid
        cv2.rectangle(frame, (x - 30, y - 40), (x + 30, y), (80, 80, 80), -1)
        # Screen panel
        cv2.rectangle(frame, (x - 27, y - 37), (x + 27, y - 3), (150, 80, 50), -1)
        # Simulated code lines on screen
        cv2.line(frame, (x - 20, y - 30), (x - 5, y - 30), (255, 255, 255), 2)
        cv2.line(frame, (x - 20, y - 24), (x - 10, y - 24), (0, 255, 255), 2)
        cv2.line(frame, (x - 20, y - 18), (x, y - 18), (0, 255, 0), 2)

    def _draw_book(self, frame, x, y):
        """Draws a stacked pile of colorful books."""
        # Book 1 (Red)
        cv2.rectangle(frame, (x - 22, y + 4), (x + 22, y + 12), (70, 70, 210), -1)
        cv2.rectangle(frame, (x - 20, y + 4), (x + 22, y + 12), (240, 240, 240), 1) # Pages spine
        # Book 2 (Green)
        cv2.rectangle(frame, (x - 18, y - 4), (x + 18, y + 3), (70, 160, 70), -1)
        cv2.rectangle(frame, (x - 16, y - 4), (x + 18, y + 3), (240, 240, 240), 1)
        # Book 3 (Orange)
        cv2.rectangle(frame, (x - 15, y - 12), (x + 15, y - 5), (60, 120, 210), -1)
        cv2.rectangle(frame, (x - 13, y - 12), (x + 15, y - 5), (240, 240, 240), 1)

    def generate_synthetic_frame(self, room_name, t):
        """Generates a high-fidelity room frame and maps moving objects."""
        # 1. Draw static room layout
        frame = self._draw_room_background(room_name)
        
        # 60-second animation loop
        cycle = t % 60.0
        detections = []

        if room_name == "Living Room":
            # 1. Cup: Always stationary on table
            cx_cup, cy_cup = 260, 225
            self._draw_cup(frame, cx_cup, cy_cup)
            detections.append({
                'track_id': 1,
                'name': 'cup',
                'confidence': 0.94,
                'bbox': [cx_cup - 15, cy_cup - 20, cx_cup + 15, cy_cup + 20]
            })

            # 2. Phone physics path
            # - 0s to 10s: stationary on table
            # - 10s to 16s: sliding to sofa
            # - 16s to 25s: stationary on sofa
            # - 25s to 30s: sliding off-screen right
            # - 30s to 55s: off-screen
            # - 55s to 60s: sliding back to table
            cx, cy = None, None
            if 0.0 <= cycle < 10.0:
                cx, cy = 340, 225
            elif 10.0 <= cycle < 16.0:
                p = (cycle - 10.0) / 6.0
                cx = 340.0 + p * (450.0 - 340.0)
                cy = 225.0 + p * (380.0 - 225.0)
            elif 16.0 <= cycle < 25.0:
                cx, cy = 450, 380
            elif 25.0 <= cycle < 30.0:
                p = (cycle - 25.0) / 5.0
                cx = 450.0 + p * 250.0  # 450 to 700
                cy = 380.0 - p * 30.0   # 380 to 350
            elif 30.0 <= cycle < 55.0:
                cx, cy = None, None
            else:  # 55.0 to 60.0
                p = (cycle - 55.0) / 5.0
                cx = 700.0 - p * 360.0  # 700 to 340
                cy = 350.0 - p * 125.0  # 350 to 225

            if cx is not None and cy is not None and (0 <= cx <= 640):
                self._draw_phone(frame, int(cx), int(cy))
                detections.append({
                    'track_id': 2,
                    'name': 'phone',
                    'confidence': 0.91,
                    'bbox': [cx - 15, cy - 20, cx + 15, cy + 20]
                })

        elif room_name == "Bedroom":
            # 1. Laptop: Stationary on table
            cx_lap, cy_lap = 490, 235
            self._draw_laptop(frame, cx_lap, cy_lap)
            detections.append({
                'track_id': 3,
                'name': 'laptop',
                'confidence': 0.96,
                'bbox': [cx_lap - 35, cy_lap - 25, cx_lap + 35, cy_lap + 10]
            })

            # 2. Book: Stationary on Bed
            cx_bk, cy_bk = 160, 300
            self._draw_book(frame, cx_bk, cy_bk)
            detections.append({
                'track_id': 4,
                'name': 'book',
                'confidence': 0.88,
                'bbox': [cx_bk - 25, cy_bk - 20, cx_bk + 25, cy_bk + 20]
            })

            # 3. Phone (displaced from Living Room)
            # - 0s to 29s: off-screen
            # - 29s to 34s: entering from left to bed cushion
            # - 34s to 42s: stationary on Bed
            # - 42s to 48s: sliding to desk
            # - 48s to 56s: stationary on desk
            # - 56s to 60s: sliding off-screen left
            cx, cy = None, None
            if 29.0 <= cycle < 34.0:
                p = (cycle - 29.0) / 5.0
                cx = -50.0 + p * 270.0  # -50 to 220
                cy = 300.0 + p * 20.0   # 300 to 320
            elif 34.0 <= cycle < 42.0:
                cx, cy = 220, 320
            elif 42.0 <= cycle < 48.0:
                p = (cycle - 42.0) / 6.0
                cx = 220.0 + p * 210.0  # 220 to 430
                cy = 320.0 - p * 75.0   # 320 to 245
            elif 48.0 <= cycle < 56.0:
                cx, cy = 430, 245
            elif 56.0 <= cycle < 60.0:
                p = (cycle - 56.0) / 4.0
                cx = 430.0 - p * 490.0  # 430 to -60
                cy = 245.0 + p * 55.0   # 245 to 300

            if cx is not None and cy is not None and (0 <= cx <= 640):
                self._draw_phone(frame, int(cx), int(cy))
                detections.append({
                    # Track ID matches the Living Room source logic to show multi-camera sequence
                    'track_id': 20, 
                    'name': 'phone',
                    'confidence': 0.89,
                    'bbox': [cx - 15, cy - 20, cx + 15, cy + 20]
                })

        return frame, detections

    def process_camera(self, room_name, source):
        """Processes a camera feed and draws active tracks and trail indicators."""
        frame = None
        detections = []
        is_simulated = True

        # Try to load actual video feed
        if isinstance(source, str) and os.path.exists(source):
            is_simulated = False
        elif isinstance(source, int):
            is_simulated = False

        if not is_simulated and self.model is not None:
            cap = cv2.VideoCapture(source)
            if cap.isOpened():
                ret, raw_frame = cap.read()
                if ret:
                    frame = raw_frame
                    frame = cv2.resize(frame, (640, 480))
                    
                    results = self.model.track(
                        source=frame,
                        persist=True,
                        conf=config.YOLO_CONF_THRESHOLD,
                        verbose=False
                    )
                    
                    if results and results[0].boxes is not None and results[0].boxes.id is not None:
                        ids = results[0].boxes.id.int().cpu().tolist()
                        boxes = results[0].boxes.xyxy.cpu().tolist()
                        confs = results[0].boxes.conf.cpu().tolist()
                        clss = results[0].boxes.cls.int().cpu().tolist()
                        
                        for track_id, box, conf, cls_id in zip(ids, boxes, confs, clss):
                            if cls_id in config.YOLO_CLASS_MAP:
                                detections.append({
                                    'track_id': track_id,
                                    'name': config.YOLO_CLASS_MAP[cls_id],
                                    'confidence': conf,
                                    'bbox': box
                                })
                cap.release()
            else:
                is_simulated = True

        if is_simulated:
            frame, detections = self.generate_synthetic_frame(room_name, time.time())

        # Feed to stationary tracker
        if frame is not None:
            self.tracker.update(room_name, detections, frame)
            
            # Draw tracks, boxes, and history trails
            active_room_tracks = self.tracker.active_tracks.get(room_name, {})
            for track_id, state in active_room_tracks.items():
                x1, y1, x2, y2 = map(int, state.bbox)
                
                if state.status == 'stationary':
                    color = (50, 220, 50)     # Green
                elif state.status == 'tracking':
                    color = (0, 140, 255)     # Orange/Yellow
                else:
                    color = (50, 50, 220)     # Red
                
                # DRAW CENTROID HISTORICAL TRAIL
                trail = state.centroid_history
                if len(trail) > 1:
                    for i in range(1, len(trail)):
                        pt1 = (int(trail[i-1][1]), int(trail[i-1][2]))
                        pt2 = (int(trail[i][1]), int(trail[i][2]))
                        # Draw fade trail lines
                        thickness = int(1 + (i / len(trail)) * 3)
                        cv2.line(frame, pt1, pt2, (0, 140, 255), thickness)
                        # Draw dots along path
                        if i == len(trail) - 1:
                            cv2.circle(frame, pt2, 4, (0, 220, 255), -1)

                # Draw bounding box outline
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Draw dynamic classification card
                label = f"{state.object_name.upper()} #{track_id} ({state.status.upper()})"
                cv2.rectangle(frame, (x1 - 1, y1 - 20), (x1 + 180, y1), color, -1)
                cv2.putText(frame, label, (x1 + 4, y1 - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

            with self.lock:
                self.latest_frames[room_name] = frame

    def run(self):
        """Processes frames continuously at ~10 FPS."""
        logger.info("Vision loop entered.")
        while self.is_running:
            start_time = time.time()
            for room_name, source in config.CAMERA_SOURCES.items():
                try:
                    self.process_camera(room_name, source)
                except Exception as e:
                    logger.error(f"Error processing room {room_name}: {e}")
                    
            elapsed = time.time() - start_time
            sleep_time = max(0.01, 0.1 - elapsed)
            time.sleep(sleep_time)
        logger.info("Vision loop exited.")

    def get_latest_frame(self, room_name):
        """Thread-safely gets the latest frame for a room."""
        with self.lock:
            return self.latest_frames.get(room_name)
