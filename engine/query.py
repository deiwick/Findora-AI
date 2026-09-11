import re
from datetime import datetime
from database import db

# Mapping of synonyms to standard Findora object classes
SYNONYMS = {
    "phone": ["phone", "cellphone", "mobile", "iphone", "telephone", "android", "cell phone", "smartphone", "phn", "mob", "cell"],
    "keys": ["key", "keys", "housekey", "carkey", "keychain", "car keys"],
    "wallet": ["wallet", "purse", "billfold", "handbag", "cardholder", "pocketbook", "clutch", "money bag"],
    "book": ["book", "textbook", "notebook", "novel", "magazine", "reading", "diary", "journal", "notes"],
    "bottle": ["bottle", "flask", "thermos", "waterbottle", "canteen", "water bottle", "hydroflask", "sipper"],
    "cup": ["cup", "mug", "glass", "teacup", "tumbler", "coffee cup", "coffee mug", "chai cup", "tea mug"],
    "remote": ["remote", "clicker", "controller", "tv remote", "remotely", "ac remote"],
    "backpack": ["backpack", "bag", "pack", "knapsack", "satchel", "schoolbag", "rucksack", "tote"],
    "laptop": ["laptop", "computer", "macbook", "pc", "chromebook", "notebook computer", "thinkpad", "laptop computer"],
    "mouse": ["mouse", "computermouse", "wireless mouse", "trackpad"],
    "keyboard": ["keyboard", "keypad", "typing board"],
    "chair": ["chair", "seat", "office chair", "stool", "armchair"],
    "clock": ["clock", "wall clock", "timepiece", "alarm clock", "watch"],
    "scissors": ["scissors", "shears", "cutters", "clipper"],
    "umbrella": ["umbrella", "parasol", "raincoat"],
    "bowl": ["bowl", "dish", "plate", "cereal bowl"],
    "person": ["person", "human", "someone", "user", "man", "woman", "guy", "people"]
}

# Mapping of common room / zone aliases to database zones
ROOMS = {
    "Laptop Zone": ["laptop zone", "laptop camera", "webcam zone", "webcam", "laptop area", "desk zone", "desk", "room 1", "zone 1"],
    "ESP32-CAM Zone": ["esp32-cam zone", "esp32 zone", "esp32 cam", "esp32", "esp camera", "network camera", "stream zone", "room 2", "zone 2"],
    "Living Room": ["living room", "livingroom", "lounge", "parlor", "couch area"],
    "Bedroom": ["bedroom", "bed room", "sleeping room", "bed"],
    "Kitchen": ["kitchen", "cooking area", "pantry"],
    "Office": ["office", "study", "workspace"]
}

def levenshtein_distance(s1, s2):
    """Calculates Levenshtein distance between two strings (typo score)."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def find_fuzzy_match(word, choices, max_dist=2):
    """Checks if a word is close to any string in choice list using Levenshtein distance."""
    if len(word) < 3:
        return None
        
    for choice in choices:
        dist = levenshtein_distance(word, choice)
        if dist <= max_dist:
            return choice
    return None

def parse_natural_query(query_text):
    """
    Parses a natural language query to extract target object and room/zone.
    Supports exact synonym matches and Levenshtein fuzzy matching.
    Returns: (mapped_object, mapped_room)
    """
    query_clean = query_text.lower().strip()
    
    # 1. Exact Match Check (Standard Synonyms)
    matched_object = None
    for obj, syn_list in SYNONYMS.items():
        sorted_syns = sorted(syn_list, key=len, reverse=True)
        for syn in sorted_syns:
            pattern = rf"\b{re.escape(syn)}\b"
            if re.search(pattern, query_clean):
                matched_object = obj
                break
        if matched_object:
            break
            
    # 2. Fuzzy Match Check (if no exact match)
    if not matched_object:
        tokens = re.findall(rf"\b\w+\b", query_clean)
        best_match = None
        min_distance = 999
        
        for token in tokens:
            for obj, syn_list in SYNONYMS.items():
                matched_syn = find_fuzzy_match(token, syn_list, max_dist=2)
                if matched_syn:
                    dist = levenshtein_distance(token, matched_syn)
                    if dist < min_distance:
                        min_distance = dist
                        best_match = obj
        matched_object = best_match

    # 3. Room/Zone Match Check
    matched_room = None
    for room, aliases in ROOMS.items():
        sorted_aliases = sorted(aliases, key=len, reverse=True)
        for alias in sorted_aliases:
            pattern = rf"\b{re.escape(alias)}\b"
            if re.search(pattern, query_clean):
                matched_room = room
                break
        if matched_room:
            break
            
    # Fuzzy room check if no exact room match
    if not matched_room:
        tokens = re.findall(rf"\b\w+\b", query_clean)
        for token in tokens:
            for room, aliases in ROOMS.items():
                matched_alias = find_fuzzy_match(token, aliases, max_dist=2)
                if matched_alias:
                    matched_room = room
                    break
            if matched_room:
                break
                
    return matched_object, matched_room

def execute_search(query_text):
    """
    Executes a natural language search against real SQLite memory records.
    Provides context-aware recommendations if items are marked 'lost' or 'moved'.
    """
    obj, room = parse_natural_query(query_text)
    
    if not obj:
        valid_items = ", ".join(SYNONYMS.keys())
        return {
            "success": False,
            "message": f"I couldn't identify the item you are looking for. Please search for one of: {valid_items}.",
            "data": None
        }

    # Query last known status of this object
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, object_name, room_name, timestamp, status, thumbnail_path, confidence, bbox, track_id
        FROM findora_memory
        WHERE object_name = ?
        ORDER BY timestamp DESC, id DESC
        LIMIT 1
    """, (obj,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {
            "success": False,
            "message": f"I recognized '{obj}', but no detection events have been recorded in physical memory yet.",
            "data": None
        }
        
    record = dict(row)
    
    # Format timestamp
    timestamp_str = record['timestamp']
    try:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        time_formatted = dt.strftime("%b %d, %I:%M %p")
    except Exception:
        time_formatted = timestamp_str
        
    status = record['status']
    confidence_pct = record['confidence'] * 100 if record['confidence'] else 0.0
    actual_room = record['room_name']
    
    msg = ""
    if status == 'stationary':
        if room and room.lower() != actual_room.lower():
            msg = f"No, your **{obj}** is not in **{room}**. It is currently **stationary** in **{actual_room}** (since {time_formatted}, {confidence_pct:.1f}% confidence)."
        else:
            msg = f"I found your **{obj}**! It is currently **stationary** in **{actual_room}** (since {time_formatted}, confidence: {confidence_pct:.1f}%)."
            
    elif status == 'moved':
        if room and room.lower() != actual_room.lower():
            msg = f"No, it was last logged in **{actual_room}**, but was reported **moved** at {time_formatted}."
        else:
            msg = f"Your **{obj}** was detected in **{actual_room}**, but is currently marked **moved** as of {time_formatted}."
            
    else:  # lost
        # Query database history to find the last known stationary location
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT room_name, timestamp, bbox
            FROM findora_memory
            WHERE object_name = ? AND status = 'stationary'
            ORDER BY timestamp DESC, id DESC
            LIMIT 1
        """, (obj,))
        hist_row = cursor.fetchone()
        conn.close()
        
        loc_suggestion = ""
        if hist_row:
            h_room = hist_row['room_name']
            h_time = hist_row['timestamp']
            try:
                h_dt = datetime.strptime(h_time, "%Y-%m-%d %H:%M:%S")
                h_time_formatted = h_dt.strftime("%I:%M %p")
            except Exception:
                h_time_formatted = h_time
            
            loc_suggestion = f" Check near its last stationary spot in **{h_room}** (logged at {h_time_formatted})."
        
        if room and room.lower() != actual_room.lower():
            msg = f"No, your **{obj}** is currently **missing/lost** from camera view. It was last seen in **{actual_room}** (at {time_formatted}).{loc_suggestion}"
        else:
            msg = f"Your **{obj}** is currently **missing/lost** from camera view. It was last seen in **{actual_room}** at {time_formatted}.{loc_suggestion}"
            
    return {
        "success": True,
        "message": msg,
        "data": record
    }
