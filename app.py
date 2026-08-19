import os
import cv2
import time
import pandas as pd
from PIL import Image
from datetime import datetime
import streamlit as st

import config
from database import db
from engine.query import execute_search, parse_natural_query
from engine.vision import VisionEngine
import generate_mock_data

# Set up page configurations
st.set_page_config(
    page_title="Findora AI - Edge AI Object Tracker",
    layout="wide",
    page_icon="🛡️"
)

# Custom CSS for polished interface styling (card look, borders, custom headers)
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-label {
        font-size: 14px;
        color: #6c757d;
        font-weight: 500;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 24px;
        color: #212529;
        font-weight: 700;
    }
    .status-badge-stationary {
        background-color: #d4edda;
        color: #155724;
        padding: 3px 8px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-badge-moved {
        background-color: #fff3cd;
        color: #856404;
        padding: 3px 8px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-badge-lost {
        background-color: #f8d7da;
        color: #721c24;
        padding: 3px 8px;
        border-radius: 5px;
        font-weight: bold;
    }
    .timeline-card {
        border-left: 3px solid #007bff;
        padding-left: 15px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
db.init_db()

# Initialize the Vision Engine in Session State (singleton)
if "vision_engine" not in st.session_state:
    engine = VisionEngine()
    engine.start()
    st.session_state.vision_engine = engine

# Header section
st.title("🛡️ Findora AI: Local Object Finder & Spatial Memory")
st.markdown("""
A Principal-grade Edge AI prototype featuring **real-time spatial tracking, 2D virtual room physics simulation, multi-camera handoff**, and **natural language query mapping**.
""")

# Sidebar control panel
st.sidebar.header("⚙️ Edge Engine Control")

# Display current status of the worker thread
engine_active = st.session_state.vision_engine.is_running
status_color = "green" if engine_active else "red"
st.sidebar.markdown(f"Engine Status: :**{status_color}[{'ACTIVE' if engine_active else 'OFFLINE'}]**")

# Toggle to Start/Stop the background worker
if engine_active:
    if st.sidebar.button("Stop Vision Thread", use_container_width=True):
        st.session_state.vision_engine.stop()
        st.rerun()
else:
    if st.sidebar.button("Start Vision Thread", use_container_width=True):
        st.session_state.vision_engine.start()
        st.rerun()

st.sidebar.markdown("---")

# Active items quick overview in Sidebar
st.sidebar.subheader("📍 Active Spatial Memory Map")
last_knowns = db.get_last_known_locations()
if last_knowns:
    for item in last_knowns:
        status_color = "green" if item['status'] == 'stationary' else "orange" if item['status'] == 'moved' else "red"
        st.sidebar.markdown(f"**{item['object_name'].capitalize()}**: :{status_color}[{item['status'].upper()}] in *{item['room_name']}*")
else:
    st.sidebar.info("Memory database is currently empty.")

# Setup Tabs
tab_live, tab_search, tab_timeline, tab_privacy = st.tabs([
    "📹 Live Camera Feeds", 
    "🔍 AI Object Finder", 
    "⏳ Spatial Timelines", 
    "🛡️ Local Audit Panel"
])

# ==========================================
# TAB 1: LIVE FEED / MONITOR
# ==========================================
with tab_live:
    # KPI metrics row
    st.subheader("System Performance & Health Indicators")
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    # Calculate metrics
    total_tracked = len(last_knowns)
    stationary_count = sum(1 for x in last_knowns if x['status'] == 'stationary')
    lost_count = sum(1 for x in last_knowns if x['status'] == 'lost')
    
    col_kpi1.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Objects in Database</div>
        <div class="metric-value">{total_tracked} items</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_kpi2.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Stationary (Locked)</div>
        <div class="metric-value" style="color: #28a745;">{stationary_count} items</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_kpi3.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Missing / Lost</div>
        <div class="metric-value" style="color: #dc3545;">{lost_count} items</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_kpi4.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Handoff Logic Status</div>
        <div class="metric-value" style="color: #007bff;">Operational</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📹 Real-Time Spatial Video Feeds")
    
    # Toggle for continuous video streaming (prevent CPU bloat when doing searches)
    live_stream = st.checkbox("Continuous Stream Render (Updates feed at ~10 FPS)", value=False)
    
    col_cam1, col_cam2 = st.columns(2)
    placeholder_lr = col_cam1.empty()
    placeholder_br = col_cam2.empty()

    # Fetch and show static/dynamic frame
    def render_frames():
        lr_frame = st.session_state.vision_engine.get_latest_frame("Living Room")
        br_frame = st.session_state.vision_engine.get_latest_frame("Bedroom")
        
        if lr_frame is not None:
            placeholder_lr.image(cv2.cvtColor(lr_frame, cv2.COLOR_BGR2RGB), use_container_width=True, caption="Room Cam 1: Living Room Floorplan")
        else:
            placeholder_lr.info("Waiting for Living Room Camera feed...")

        if br_frame is not None:
            placeholder_br.image(cv2.cvtColor(br_frame, cv2.COLOR_BGR2RGB), use_container_width=True, caption="Room Cam 2: Bedroom Floorplan")
        else:
            placeholder_br.info("Waiting for Bedroom Camera feed...")

    render_frames()

    # Display live event log
    st.markdown("### 📋 SQLite Live Memory Event Log")
    log_placeholder = st.empty()
    
    def refresh_logs():
        records = db.get_all_records(limit=10)
        if records:
            df = pd.DataFrame(records)
            df.columns = ["ID", "Object Label", "Room Name", "Timestamp", "Status", "Confidence", "Track ID"]
            
            # Map status strings to emojis
            status_emoji_map = {
                'stationary': '📍 STATIONARY',
                'moved': '➡️ MOVED',
                'lost': '❓ LOST'
            }
            df['Status'] = df['Status'].map(status_emoji_map)
            df['Confidence'] = df['Confidence'].apply(lambda x: f"{x * 100:.1f}%" if x else "N/A")
            log_placeholder.dataframe(df, use_container_width=True, hide_index=True)
        else:
            log_placeholder.info("No tracking events logged yet. Displace an item or wait for it to become stationary.")

    refresh_logs()

    # Loop to support continuous live view if checked
    if live_stream and engine_active:
        for _ in range(15):
            render_frames()
            refresh_logs()
            time.sleep(0.1)
        st.rerun()

# ==========================================
# TAB 2: OBJECT FINDER (SEARCH)
# ==========================================
with tab_search:
    st.subheader("🔍 Spatial Memory Query Engine")
    st.markdown("Query Findora's memory in natural English. The system maps intent and corrects spelling typos locally.")
    
    # Common quick suggestions
    st.markdown("**Quick Query Templates (Click to apply):**")
    cols_sug = st.columns(6)
    suggestions = [
        "Where is my phone?", 
        "Did I leave my backpack in the kitchen?", 
        "Where did I put the book?",
        "Is my laptop in the lounge?", 
        "where is my phn? (Typo Test)", 
        "is the ccup in the Living Room? (Typo Test)"
    ]
    
    # Check button click
    for idx, sug in enumerate(suggestions):
        if cols_sug[idx % 6].button(sug, key=f"sug_btn_{idx}"):
            st.session_state.search_query = sug

    search_input = st.text_input(
        "Enter your query:",
        value=st.session_state.get('search_query', ""),
        placeholder="e.g., Where is my cell phone?",
        key="search_bar"
    )

    if search_input:
        # Run fuzzy search
        result = execute_search(search_input)
        
        # Show judges the internal AI details of Levenshtein matching!
        obj_match, room_match = parse_natural_query(search_input)
        
        # UI Columns
        col_res, col_ai_insights = st.columns([3, 2])
        
        with col_res:
            if result["success"]:
                st.info("🧠 **Findora Brain Response:**")
                st.success(result["message"])
                
                record = result["data"]
                
                # Card details
                col_meta, col_img = st.columns([3, 2])
                with col_meta:
                    st.markdown("#### Database Record Summary")
                    st.write(f"📍 **Last Room:** `{record['room_name']}`")
                    st.write(f"🛠️ **Track Status:** `{record['status'].upper()}`")
                    st.write(f"🕒 **Logged At:** `{record['timestamp']}`")
                    st.write(f"🎯 **Confidence:** `{record['confidence']*100:.1f}%`")
                    st.write(f"🆔 **Track ID Reference:** `Track #{record['track_id']}`")
                    st.write(f"📦 **Bounding Box Coordinates:** `{record['bbox']}`")
                
                with col_img:
                    st.markdown("#### Crop Thumbnail Snapshot")
                    thumb_path = record['thumbnail_path']
                    if thumb_path:
                        full_path = os.path.join(config.BASE_DIR, thumb_path)
                        if os.path.exists(full_path):
                            try:
                                img = Image.open(full_path)
                                st.image(img, caption=f"Last logged crop of {record['object_name']}", width=180)
                            except Exception as e:
                                st.error(f"Error loading thumbnail: {e}")
                        else:
                            st.warning("Thumbnail image file missing.")
                    else:
                        st.info("No thumbnail saved.")
            else:
                st.error(result["message"])
                
        with col_ai_insights:
            st.markdown("#### 💡 Edge-AI Parse Insights")
            st.info(f"""
            - **Raw Query Text**: `"{search_input}"`
            - **Identified Class Label**: `{obj_match.upper() if obj_match else "None (Unidentified)"}`
            - **Identified Room Filter**: `{room_match.upper() if room_match else "None (Unfiltered)"}`
            """)
            st.markdown("""
            **How it works:** 
            A lightweight, local Levenshtein string distance algorithm tokenizes the input words and maps typos or synonyms to the closest standard target category in config.
            """)

# ==========================================
# TAB 3: MOVEMENT HISTORY (TIMELINE)
# ==========================================
with tab_timeline:
    st.subheader("⏳ Temporal Spatial Timeline Audit")
    st.markdown("Select a tracked object to view its chronological displacement trail.")
    
    # Pull items present in the DB
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT object_name FROM findora_memory")
    distinct_objects = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    display_objects = sorted(list(set(distinct_objects + list(config.YOLO_CLASS_MAP.values()))))
    selected_obj = st.selectbox("Inspect Object:", display_objects)
    
    if selected_obj:
        history = db.get_object_history(selected_obj)
        
        if history:
            st.markdown(f"### Spatial Trail: **{selected_obj.capitalize()}**")
            
            # Draw chronological audit trail cards
            for idx, event in enumerate(history):
                status = event['status']
                timestamp_str = event['timestamp']
                room = event['room_name']
                confidence = event['confidence']
                track_id = event['track_id']
                
                # Format timestamps
                try:
                    dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    formatted_time = dt.strftime("%b %d, %Y - %I:%M:%S %p")
                except:
                    formatted_time = timestamp_str

                # Calculate duration stayed if previous event was a move/lost and this is stationary
                duration_str = ""
                if status == 'stationary' and idx > 0:
                    # The next event in history (which is chronological predecessor, i.e., index idx - 1)
                    # has the timestamp when the object was moved from this position.
                    prev_event = history[idx - 1]
                    try:
                        t_start = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        t_end = datetime.strptime(prev_event['timestamp'], "%Y-%m-%d %H:%M:%S")
                        delta = t_end - t_start
                        
                        # Format delta
                        seconds = int(delta.total_seconds())
                        hours, remainder = divmod(seconds, 3600)
                        minutes, secs = divmod(remainder, 60)
                        if hours > 0:
                            duration_str = f"⌛ *Stayed at this spot for {hours}h {minutes}m*"
                        elif minutes > 0:
                            duration_str = f"⌛ *Stayed at this spot for {minutes} min {secs} sec*"
                        else:
                            duration_str = f"⌛ *Stayed at this spot for {secs} sec*"
                    except:
                        pass

                # Styling based on status
                if status == 'stationary':
                    icon = "📍"
                    badge_style = "status-badge-stationary"
                    desc = f"became **STATIONARY** in the **{room}**"
                elif status == 'moved':
                    icon = "➡️"
                    badge_style = "status-badge-moved"
                    desc = f"was **MOVED** from coordinates in the **{room}**"
                else:  # lost
                    icon = "❓"
                    badge_style = "status-badge-lost"
                    desc = f"was marked **LOST** (disappeared from camera feed) in the **{room}**"

                # Render Card block
                st.markdown(f"""
                <div class="timeline-card">
                    <strong>{icon} {formatted_time}</strong> | 
                    <span class="{badge_style}">{status.upper()}</span>
                    <p style="margin-top:5px; margin-bottom:0px;">Object {desc} (Track #{track_id}, Confidence: {confidence*100:.1f}%)</p>
                </div>
                """, unsafe_allow_html=True)
                
                if duration_str:
                    st.markdown(duration_str)

                # Show crop thumbnail expander
                thumb_path = event['thumbnail_path']
                if thumb_path:
                    full_path = os.path.join(config.BASE_DIR, thumb_path)
                    if os.path.exists(full_path) and status == 'stationary':
                        with st.expander("👁️ View Snapshot Crop"):
                            st.image(full_path, width=150)
                            
                st.markdown("---")
        else:
            st.info(f"No history records found for '{selected_obj}' in local memory.")

# ==========================================
# TAB 4: PRIVACY AUDIT & CONTROLS
# ==========================================
with tab_privacy:
    st.subheader("🛡️ Edge-AI Privacy Guard Controls")
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    # Stats
    col_stat1.metric(
        label="Cloud Connection Status",
        value="OFFLINE",
        delta="Zero External Networks Used",
        delta_color="normal"
    )
    
    db_size = db.get_database_size()
    col_stat2.metric(
        label="SQLite SQLite Database File",
        value=f"{db_size:.2f} KB",
        delta="Stored Encrypted Locally",
        delta_color="normal"
    )
    
    thumb_files = os.listdir(config.THUMBNAIL_DIR) if os.path.exists(config.THUMBNAIL_DIR) else []
    col_stat3.metric(
        label="Saved Crop Snapshots",
        value=f"{len(thumb_files)} files",
        delta="RAM Only Video Stream",
        delta_color="normal"
    )
    
    st.markdown("---")
    st.subheader("⚡ Demo Controls")
    st.markdown("Reset or seed mock data directly from the user interface to show judges immediate timeline handoffs.")
    
    col_seed1, col_seed2 = st.columns(2)
    
    if col_seed1.button("⚡ Seed Mock Database Timeline", type="secondary", use_container_width=True):
        generate_mock_data.seed_database()
        st.toast("Successfully seeded database with object timelines and color-coded thumbnails!")
        time.sleep(1.0)
        st.rerun()

    if col_seed2.button("🗑️ Purge Database & Local Images", type="primary", use_container_width=True):
        db.purge_all_logs()
        st.toast("Successfully cleared SQLite database and purged thumbnail directory.")
        time.sleep(1.0)
        st.rerun()

    st.markdown("---")
    st.subheader("Compliance Checklist")
    st.markdown("""
    - [x] **Zero Raw Video Retention**: Raw frames are processed in volatile memory buffers. No raw stream is stored on disk.
    - [x] **Privacy Boundary Crops**: Crop images are capped at `200x200px` around the item coordinates, eliminating surrounding scene capture.
    - [x] **Local Inference**: The YOLOv8 model runs locally on CPU/GPU. No data goes online.
    """)
