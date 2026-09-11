# ─────────────────────────────────────────────────────────────────────────────
# Findora AI  |  Real-Time Dual-Camera Spatial Memory
#
# Camera feed architecture:
#   Flask MJPEG server (port 5001) serves frames from engine's shared buffer.
#   Browser renders the MJPEG streams natively via <img src="..."> tags.
#   → Zero Streamlit DOM re-rendering for video. Zero page flicker.
#   → Live event log uses @st.fragment(run_every=2) for DB polling only.
# ─────────────────────────────────────────────────────────────────────────────
import os
import time
import cv2
import pandas as pd
from PIL import Image
from datetime import datetime
import streamlit as st

import config
from database import db
from engine.query import execute_search, parse_natural_query
from engine.vision import VisionEngine
import engine.stream_server as stream_server

STREAM_PORT  = 5001
LAPTOP_URL   = f"http://localhost:{STREAM_PORT}/video/laptop"
ESP32_URL    = f"http://localhost:{STREAM_PORT}/video/esp32"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Findora AI",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
body { font-family: 'Segoe UI', sans-serif; }

.kpi-card {
    background: linear-gradient(135deg,#1a1a2e 0%,#252545 100%);
    border:1px solid #3a3a60; border-radius:12px;
    padding:16px 20px; text-align:center;
    box-shadow:0 4px 14px rgba(0,0,0,.35);
}
.kpi-label { font-size:11px; color:#8888bb; text-transform:uppercase;
             letter-spacing:1.2px; margin-bottom:5px; }
.kpi-value { font-size:26px; font-weight:700; color:#fff; }
.kpi-sub   { font-size:10px; color:#5555aa; margin-top:3px; }

/* Camera feed wrapper */
.cam-header {
    font-size:11px; font-weight:600; color:#8888cc;
    text-transform:uppercase; letter-spacing:1px;
    margin-bottom:4px; text-align:center;
}
.cam-wrap { border:2px solid #2e2e50; border-radius:10px;
            overflow:hidden; background:#08081a; }
.cam-wrap img { width:100%; display:block; border-radius:8px; }

/* Status badges */
.b-stat { background:#0c3d1a; color:#3ddb6e; padding:2px 10px;
          border-radius:20px; font-size:12px; font-weight:700; }
.b-move { background:#3d2e00; color:#ffbb33; padding:2px 10px;
          border-radius:20px; font-size:12px; font-weight:700; }
.b-lost { background:#3d0c0c; color:#ff5555; padding:2px 10px;
          border-radius:20px; font-size:12px; font-weight:700; }

/* Timeline */
.tl { border-left:3px solid #4466cc; padding:9px 15px; margin-bottom:10px;
      background:#10102a; border-radius:0 8px 8px 0; }

/* Hide Streamlit chrome */
#MainMenu,footer,header { visibility:hidden; }

/* Remove iframe border for MJPEG embeds */
iframe { border:none !important; }
</style>
""", unsafe_allow_html=True)

# ── Init DB ───────────────────────────────────────────────────────────────────
db.init_db()

# ── VisionEngine singleton ────────────────────────────────────────────────────
if "vision_engine" not in st.session_state:
    e = VisionEngine()
    e.start()
    st.session_state.vision_engine    = e
    st.session_state.engine_started   = datetime.now().strftime("%H:%M:%S")

engine: VisionEngine = st.session_state.vision_engine

# ── Flask MJPEG server (start once per process) ───────────────────────────────
if "stream_server_started" not in st.session_state:
    stream_server.start(engine, port=STREAM_PORT)
    st.session_state.stream_server_started = True
# Always keep engine reference fresh
stream_server._engine_ref[0] = engine


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ Findora AI")
    st.caption("Real-Time Spatial Memory Tracker")
    st.divider()

    is_running = engine.is_running
    if is_running:
        st.success("🟢  Vision Engine  **ACTIVE**")
        st.caption(f"Started: {st.session_state.get('engine_started','—')}")
        if st.button("⏹️ Stop Engine", width='stretch'):
            engine.stop()
            st.rerun()
    else:
        st.error("🔴  Vision Engine  **STOPPED**")
        if st.button("▶️ Start Engine", width='stretch', type="primary"):
            engine.start()
            st.session_state.engine_started = datetime.now().strftime("%H:%M:%S")
            st.rerun()

    if st.button("🔄 Restart Engine", width='stretch'):
        engine.stop()
        time.sleep(0.4)
        engine.start()
        stream_server._engine_ref[0] = engine
        st.session_state.engine_started = datetime.now().strftime("%H:%M:%S")
        st.toast("Engine restarted ✅")
        st.rerun()

    st.divider()
    st.subheader("📡 Camera Sources")
    for zone, src in config.CAMERA_SOURCES.items():
        icon = "💻" if isinstance(src, int) else "📡"
        st.markdown(f"{icon} **{zone}**  \n`{src}`")

    st.divider()
    st.subheader("🗺️ Spatial Memory")
    lk = db.get_last_known_locations()
    if lk:
        for item in lk:
            bcls = "b-stat" if item["status"]=="stationary" else \
                   "b-move" if item["status"]=="moved" else "b-lost"
            st.markdown(
                f"**{item['object_name'].capitalize()}** — *{item['room_name']}*  \n"
                f'<span class="{bcls}">{item["status"].upper()}</span>',
                unsafe_allow_html=True
            )
    else:
        st.info("Empty — place objects in camera view.")

    st.divider()
    st.caption(
        f"YOLOv8n · conf≥{config.YOLO_CONF_THRESHOLD} · "
        f"{config.STREAM_WIDTH}×{config.STREAM_HEIGHT} · "
        f"MJPEG:{STREAM_PORT}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
st.title("🛡️ Findora AI — Spatial Memory System")
st.caption("Edge-AI object tracker · 100% local · SQLite · Dual camera")

tab_live, tab_search, tab_timeline, tab_privacy = st.tabs([
    "📹 Live Feeds", "🔍 AI Finder", "⏳ Timeline", "🛡️ Privacy"
])


# ════════════════════════════════════════════════════════════════════
# TAB 1  —  LIVE FEEDS (native MJPEG — zero Streamlit re-render)
# ════════════════════════════════════════════════════════════════════
with tab_live:
    lk      = db.get_last_known_locations()
    total   = len(lk)
    stat_n  = sum(1 for x in lk if x["status"]=="stationary")
    lost_n  = sum(1 for x in lk if x["status"]=="lost")

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f'<div class="kpi-card"><div class="kpi-label">In Memory</div><div class="kpi-value">{total}</div><div class="kpi-sub">objects</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><div class="kpi-label">Stationary</div><div class="kpi-value" style="color:#3ddb6e">{stat_n}</div><div class="kpi-sub">locked</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card"><div class="kpi-label">Lost</div><div class="kpi-value" style="color:#ff5555">{lost_n}</div><div class="kpi-sub">missing</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card"><div class="kpi-label">Engine</div><div class="kpi-value" style="color:#55aaff">{"ON" if engine.is_running else "OFF"}</div><div class="kpi-sub">{"dual-cam" if engine.is_running else "stopped"}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    if engine.is_running:
        col1, col2 = st.columns(2, gap="small")

        # ── Laptop Zone — native MJPEG via <img> ──
        with col1:
            st.markdown('<div class="cam-header">💻 Camera 1 — Laptop Zone</div>', unsafe_allow_html=True)
            st.html(f"""
            <div class="cam-wrap">
              <img src="{LAPTOP_URL}"
                   onerror="this.alt='Connecting to Laptop Zone…';this.style.padding='60px 0';this.style.textAlign='center';"
                   style="width:100%;display:block;border-radius:8px;">
            </div>
            """)

        # ── ESP32-CAM Zone — native MJPEG via <img> ──
        with col2:
            st.markdown('<div class="cam-header">📡 Camera 2 — ESP32-CAM Zone</div>', unsafe_allow_html=True)
            st.html(f"""
            <div class="cam-wrap">
              <img src="{ESP32_URL}"
                   onerror="this.alt='Connecting to ESP32-CAM…';this.style.padding='60px 0';"
                   style="width:100%;display:block;border-radius:8px;">
            </div>
            """)

        st.info(
            f"📡 Feeds served natively by browser via MJPEG  ·  "
            f"Laptop: `{LAPTOP_URL}`  ·  ESP32: `{ESP32_URL}`",
            icon="ℹ️"
        )
    else:
        st.warning("▶️ Start the Vision Engine from the sidebar.", icon="⚠️")
        st.stop()

    # ── Live event log — fragment refreshes every 3s (DB only, not video) ──
    @st.fragment(run_every=3)
    def _event_log():
        st.markdown("#### 🗂️ Live Spatial Memory Events")
        records = db.get_all_records(limit=15)
        if records:
            df = pd.DataFrame(records)
            df.columns = ["ID","Object","Zone","Timestamp","Status","Confidence","Track ID"]
            df["Status"]     = df["Status"].map(
                {"stationary":"📍 STATIONARY","moved":"➡️ MOVED","lost":"❓ LOST"}
            ).fillna(df["Status"])
            df["Confidence"] = df["Confidence"].apply(
                lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "—"
            )
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("No events yet — hold an object in camera view for ~2.5 seconds.")

    _event_log()


# ════════════════════════════════════════════════════════════════════
# TAB 2  —  AI FINDER
# ════════════════════════════════════════════════════════════════════
with tab_search:
    st.subheader("🔍 Natural Language Object Finder")
    st.markdown("Ask where your objects are. Supports typos and synonyms.")

    sugs = ["Where is my phone?","Where did I put the cup?",
            "Is the book in Laptop Zone?","Find my backpack",
            "where is my phn?","Did I leave the remote somewhere?"]
    sc = st.columns(6)
    for i, s in enumerate(sugs):
        if sc[i % 6].button(s, key=f"sug_{i}", width='stretch'):
            st.session_state.search_query = s

    q = st.text_input(
        "Your query:",
        value=st.session_state.get("search_query",""),
        placeholder="e.g.  Where is my phone?  /  find the cup  /  where did I leave the book?",
        key="search_bar"
    )

    if q:
        result        = execute_search(q)
        obj_m, room_m = parse_natural_query(q)
        col_r, col_m  = st.columns([3,2])

        with col_r:
            if result["success"]:
                rec    = result["data"]
                status = rec["status"]
                bcls   = "b-stat" if status=="stationary" else \
                         "b-move" if status=="moved" else "b-lost"
                st.success(f"🧠 {result['message']}")
                st.markdown("---")
                m1,m2,m3 = st.columns(3)
                m1.metric("📍 Zone", rec["room_name"])
                m2.metric("🎯 Confidence", f"{rec['confidence']*100:.1f}%")
                m3.metric("🕒 Last Seen",  rec["timestamp"].split(" ")[1]
                          if " " in rec["timestamp"] else rec["timestamp"])
                st.markdown(
                    f'Status: <span class="{bcls}">{status.upper()}</span>'
                    f'  ·  Track <b>#{rec["track_id"]}</b>  ·  BBox: <code>{rec["bbox"]}</code>',
                    unsafe_allow_html=True)
                tp = rec.get("thumbnail_path")
                if tp:
                    fp = os.path.join(config.BASE_DIR, tp)
                    if os.path.exists(fp):
                        st.image(fp, width=200, caption=f"Crop: {rec['object_name']}")
            else:
                st.error(result["message"])

        with col_m:
            st.markdown("#### 🤖 AI Parser")
            st.info(
                f"**Query:** `{q}`\n\n"
                f"**Class:** `{obj_m.upper() if obj_m else 'None'}`\n\n"
                f"**Zone filter:** `{room_m.upper() if room_m else 'All zones'}`"
            )
            st.caption("Levenshtein fuzzy matching — fully local, zero API calls.")


# ════════════════════════════════════════════════════════════════════
# TAB 3  —  TIMELINE
# ════════════════════════════════════════════════════════════════════
with tab_timeline:
    st.subheader("⏳ Spatial Displacement Timeline")
    conn = db.get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT object_name FROM findora_memory ORDER BY object_name")
    db_objs = [r[0] for r in cur.fetchall()]
    conn.close()

    all_cls    = sorted(set(db_objs + list(config.YOLO_CLASS_MAP.values())))
    sel        = st.selectbox("Object:", all_cls)
    history    = db.get_object_history(sel) if sel else []

    if history:
        st.markdown(f"### Trail: **{sel.capitalize()}** ({len(history)} events)")
        for ev in history:
            status = ev["status"]
            ts     = ev["timestamp"]
            room   = ev["room_name"]
            try:
                ts_fmt = datetime.strptime(ts,"%Y-%m-%d %H:%M:%S").strftime("%b %d · %I:%M:%S %p")
            except ValueError:
                ts_fmt = ts
            icon  = {"stationary":"📍","moved":"➡️","lost":"❓"}.get(status,"•")
            bcls  = f"b-{'stat' if status=='stationary' else 'move' if status=='moved' else 'lost'}"
            desc  = {"stationary":f"stationary in **{room}**",
                     "moved":f"moved in **{room}**",
                     "lost":f"disappeared from **{room}**"}.get(status,"")
            st.markdown(f"""
<div class="tl">
  <b>{icon} {ts_fmt}</b> &nbsp;
  <span class="{bcls}">{status.upper()}</span><br/>
  <span style="color:#aaa;font-size:13px;">
    {sel.capitalize()} {desc} · Track #{ev['track_id']} · {ev['confidence']*100:.1f}%
  </span>
</div>""", unsafe_allow_html=True)
            tp = ev.get("thumbnail_path")
            if tp and status == "stationary":
                fp = os.path.join(config.BASE_DIR, tp)
                if os.path.exists(fp):
                    with st.expander("👁️ Snapshot"):
                        st.image(fp, width=160)
    else:
        st.info(f"No history for '{sel}' yet.")


# ════════════════════════════════════════════════════════════════════
# TAB 4  —  PRIVACY & CONTROLS
# ════════════════════════════════════════════════════════════════════
with tab_privacy:
    st.subheader("🛡️ Privacy & Edge Compliance")
    db_sz  = db.get_database_size()
    thumbs = os.listdir(config.THUMBNAIL_DIR) if os.path.exists(config.THUMBNAIL_DIR) else []
    c1,c2,c3 = st.columns(3)
    c1.metric("☁️ Cloud Connections","ZERO","100% offline")
    c2.metric("💾 SQLite Size",f"{db_sz:.2f} KB","local only")
    c3.metric("🖼️ Crops Saved",f"{len(thumbs)} files","200×200 px")

    st.markdown("---")
    st.subheader("⚡ Controls")
    ca, cb = st.columns(2)
    with ca:
        if st.button("🗑️ Clear All Memory", type="primary", width='stretch'):
            db.purge_all_logs()
            st.toast("✅ Memory cleared.", icon="🗑️")
            time.sleep(0.3)
            st.rerun()
    with cb:
        if st.button("🔄 Restart Vision Engine", width='stretch'):
            engine.stop()
            time.sleep(0.4)
            engine.start()
            stream_server._engine_ref[0] = engine
            st.session_state.engine_started = datetime.now().strftime("%H:%M:%S")
            st.toast("✅ Engine restarted.", icon="🔄")
            st.rerun()

    st.markdown("---")
    st.markdown("""
| Principle | Status |
|---|---|
| Zero raw video written to disk | ✅ RAM only |
| No cloud / external API calls | ✅ 100% local |
| Crop images bounded 200×200 px | ✅ No scene retention |
| YOLOv8 on-device inference | ✅ Local CPU |
| SQLite — no server | ✅ Single local file |
    """)