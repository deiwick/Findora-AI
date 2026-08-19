import re
from datetime import datetime
from database import db

# Mapping of synonyms to standard Findora object classes
SYNONYMS = {
    "phone": ["phone", "cellphone", "mobile", "iphone", "telephone", "android", "cell phone"],
    "keys": ["key", "keys", "housekey", "carkey", "keychain", "car keys"],
    "wallet": ["wallet", "purse", "billfold", "handbag", "cardholder", "pocketbook"],
    "book": ["book", "textbook", "notebook", "novel", "magazine", "reading"],
    "bottle": ["bottle", "flask", "thermos", "waterbottle", "canteen"],
    "cup": ["cup", "mug", "glass", "teacup", "tumbler", "coffee cup"],
    "remote": ["remote", "clicker", "controller", "tv remote", "remotely"],
    "backpack": ["backpack", "bag", "pack", "knapsack", "satchel", "schoolbag"],
    "laptop": ["laptop", "computer", "macbook", "pc", "chromebook", "notebook computer"],
    "scissors": ["scissors", "shears", "cutters", "clipper"]
}

# Mapping of common room aliases to database rooms
ROOMS = {
    "Living Room": ["living room", "livingroom", "lounge", "parlor", "couch area"],
    "Bedroom": ["bedroom", "bed room", "sleeping room", "bed"],
    "Kitchen": ["kitchen", "cooking area", "pantry"],
    "Office": ["office", "study", "workspace", "desk"]
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
    # Only run on words of reasonable length
    if len(word) < 3:
        return None
        
    for choice in choices:
        dist = levenshtein_distance(word, choice)
        # Check if distance is low enough
        if dist <= max_dist:
            return choice
    return None

def parse_natural_query(query_text):
    """
    Parses a natural language query to extract target object and room.
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
        # Strip punctuation and tokenize
        tokens = re.findall(rf"\b\w+\b", query_clean)
        best_match = None
        min_distance = 999
        
        for token in tokens:
            for obj, syn_list in SYNONYMS.items():
                # Check fuzzy match against all synonyms
                matched_syn = find_fuzzy_match(token, syn_list, max_dist=2)
                if matched_syn:
                    dist = levenshtein_distance(token, matched_syn)
                    if dist < min_distance:
                        min_distance = dist
                        best_match = obj
        matched_object = best_match

    # 3. Room Match Check
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
    Executes a natural language search.
    Provides context-aware recommendations if items are marked 'lost'.
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
        ORDER BY timestamp DESC
        LIMIT 1
    """, (obj,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {
            "success": False,
            "message": f"I recognized '{obj}', but no tracking history exists in local memory yet.",
            "data": None
        }
        
    record = dict(row)
    
    # Format timestamp
    timestamp_str = record['timestamp']
    try:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        time_formatted = dt.strftime("%b %d, %I:%M %p")
    except:
        time_formatted = timestamp_str
        
    status = record['status']
    confidence_pct = record['confidence'] * 100 if record['confidence'] else 0.0
    actual_room = record['room_name']
    
    msg = ""
    if status == 'stationary':
        if room and room.lower() != actual_room.lower():
            msg = f"No, your **{obj}** is not in the **{room}**. I found it stationary in the **{actual_room}** since {time_formatted} ({confidence_pct:.1f}% confidence)."
        else:
            msg = f"I found your **{obj}**! It is currently **stationary** in the **{actual_room}** (since {time_formatted}, confidence: {confidence_pct:.1f}%)."
            
    elif status == 'moved':
        if room and room.lower() != actual_room.lower():
            msg = f"No, it was last logged in the **{actual_room}**, but was reported **moved** at {time_formatted}."
        else:
            msg = f"Your **{obj}** was last seen in the **{actual_room}**, but is currently marked **moved** as of {time_formatted}."
            
    else:  # lost
        # Enhanced AI recommendation: Query database history to find the last known stationary location!
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT room_name, timestamp, bbox
            FROM findora_memory
            WHERE object_name = ? AND status = 'stationary'
            ORDER BY timestamp DESC
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
            except:
                h_time_formatted = h_time
            
            # Formulate targeted physical check based on coordinates or room
            loc_suggestion = f" Check near its last stationary location in the **{h_room}** (logged at {h_time_formatted})."
        
        if room and room.lower() != actual_room.lower():
            msg = f"No, your **{obj}** is currently **lost/missing**. It was last seen in the **{actual_room}** (at {time_formatted}).{loc_suggestion}"
        else:
            msg = f"Your **{obj}** is currently **lost/not visible**. It was last logged in the **{actual_room}** at {time_formatted}.{loc_suggestion}"
            
    return {
        "success": True,
        "message": msg,
        "data": record
    }
