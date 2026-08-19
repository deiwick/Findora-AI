import os
import cv2
import numpy as np
from datetime import datetime, timedelta
import config
from database import db

def create_mock_thumbnail(object_name, color=(100, 150, 250)):
    """Creates a mock 200x200px thumbnail containing a colored square and label."""
    # Create image
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    
    # Fill with a soft background color
    img[:] = color
    
    # Draw simple outline representing object
    cv2.rectangle(img, (40, 40), (160, 160), (255, 255, 255), 3)
    
    # Put label text
    cv2.putText(img, object_name.upper(), (20, 105), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Ensure thumbnail directory exists
    os.makedirs(config.THUMBNAIL_DIR, exist_ok=True)
    
    # Save thumbnail
    thumb_name = f"mock_{object_name}_{int(datetime.now().timestamp())}.jpg"
    thumb_path = os.path.join(config.THUMBNAIL_DIR, thumb_name)
    cv2.imwrite(thumb_path, img)
    
    # Return relative path from BASE_DIR
    return os.path.relpath(thumb_path, config.BASE_DIR)

def seed_database():
    print("Initializing Database...")
    db.init_db()
    
    print("Purging existing logs and thumbnails...")
    db.purge_all_logs()
    
    print("Generating mock data...")
    base_time = datetime.now() - timedelta(hours=5)
    
    # 1. Keys Timeline
    # - 08:00 AM: Stationary in Living Room
    # - 08:30 AM: Moved from Living Room
    # - 08:32 AM: Stationary in Bedroom
    keys_thumb = create_mock_thumbnail("keys", color=(220, 80, 80)) # Reddish
    db.insert_event(
        object_name="keys",
        room_name="Living Room",
        status="stationary",
        thumbnail_path=keys_thumb,
        confidence=0.90,
        bbox=[150, 220, 200, 270],
        track_id=10,
        timestamp=base_time
    )
    db.insert_event(
        object_name="keys",
        room_name="Living Room",
        status="moved",
        thumbnail_path=keys_thumb,
        confidence=0.88,
        bbox=[180, 220, 230, 270],
        track_id=10,
        timestamp=base_time + timedelta(minutes=30)
    )
    keys_new_thumb = create_mock_thumbnail("keys", color=(180, 60, 60))
    db.insert_event(
        object_name="keys",
        room_name="Bedroom",
        status="stationary",
        thumbnail_path=keys_new_thumb,
        confidence=0.94,
        bbox=[100, 150, 150, 200],
        track_id=20,
        timestamp=base_time + timedelta(minutes=32)
    )
    
    # 2. Wallet Timeline
    # - 09:15 AM: Stationary in Bedroom
    # - 12:00 PM: Moved from Bedroom
    # - 12:05 PM: Stationary in Living Room
    wallet_thumb = create_mock_thumbnail("wallet", color=(80, 180, 80)) # Greenish
    db.insert_event(
        object_name="wallet",
        room_name="Bedroom",
        status="stationary",
        thumbnail_path=wallet_thumb,
        confidence=0.95,
        bbox=[450, 280, 520, 350],
        track_id=11,
        timestamp=base_time + timedelta(hours=1, minutes=15)
    )
    db.insert_event(
        object_name="wallet",
        room_name="Bedroom",
        status="moved",
        thumbnail_path=wallet_thumb,
        confidence=0.92,
        bbox=[470, 280, 540, 350],
        track_id=11,
        timestamp=base_time + timedelta(hours=4)
    )
    wallet_new_thumb = create_mock_thumbnail("wallet", color=(60, 160, 60))
    db.insert_event(
        object_name="wallet",
        room_name="Living Room",
        status="stationary",
        thumbnail_path=wallet_new_thumb,
        confidence=0.96,
        bbox=[220, 230, 290, 300],
        track_id=21,
        timestamp=base_time + timedelta(hours=4, minutes=5)
    )

    # 3. Laptop: Stationary in Bedroom on Desk since 10:00 AM
    laptop_thumb = create_mock_thumbnail("laptop", color=(80, 80, 180)) # Blueish
    db.insert_event(
        object_name="laptop",
        room_name="Bedroom",
        status="stationary",
        thumbnail_path=laptop_thumb,
        confidence=0.98,
        bbox=[450, 270, 530, 330],
        track_id=12,
        timestamp=base_time + timedelta(hours=2)
    )

    # 4. Phone: Stationary in Living Room since 11:30 AM
    phone_thumb = create_mock_thumbnail("phone", color=(180, 80, 180)) # Purple
    db.insert_event(
        object_name="phone",
        room_name="Living Room",
        status="stationary",
        thumbnail_path=phone_thumb,
        confidence=0.91,
        bbox=[300, 240, 340, 300],
        track_id=13,
        timestamp=base_time + timedelta(hours=3, minutes=30)
    )

    # 5. Book: Entered Bedroom at 07:00 AM, but was marked lost at 07:40 AM
    book_thumb = create_mock_thumbnail("book", color=(180, 180, 80)) # Yellowish
    db.insert_event(
        object_name="book",
        room_name="Bedroom",
        status="stationary",
        thumbnail_path=book_thumb,
        confidence=0.89,
        bbox=[150, 230, 210, 280],
        track_id=14,
        timestamp=base_time - timedelta(hours=1)
    )
    db.insert_event(
        object_name="book",
        room_name="Bedroom",
        status="lost",
        thumbnail_path=book_thumb,
        confidence=0.85,
        bbox=[150, 230, 210, 280],
        track_id=14,
        timestamp=base_time - timedelta(minutes=20)
    )

    print("Mock database seeding complete!")
    print(f"Total records in DB: {len(db.get_all_records(50))}")

if __name__ == "__main__":
    seed_database()
