import streamlit as st
import pandas as pd
import json
import os
import socket
import plotly.express as px
import plotly.graph_objects as go
import hashlib
from datetime import datetime
from collections import Counter
import sentry_sdk

# Phase 2: Sentry Error Tracking
sentry_sdk.init(
    dsn="https://e9fb21060f9563c4613b6202972d3cc2@o4511089686151168.ingest.us.sentry.io/4511089698340864",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

# Import Phase 2 Analytics Module
from server.analytics import analyze_threats, build_markov_chain

# --- UI CONFIGURATION --- MUST BE FIRST
st.set_page_config(
    page_title="Neuro-Trap Command Center",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Cyberpunk CSS
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@400;500;700&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
<style>
    /* === ANIMATED GRADIENT BACKGROUND === */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 25%, #0a1628 50%, #0d0d1a 75%, #0a0a0f 100%);
        background-size: 400% 400%;
        animation: bgShift 20s ease infinite;
        color: #c9d1d9;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
    }
    @keyframes bgShift {
        0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%}
    }
    [data-testid="stMain"] { background: transparent; }
    [data-testid="stHeader"] { display: none; } /* Fix for white line at top */
    .block-container { padding-top: 2rem !important; padding-bottom: 1rem !important; }

    /* === TYPOGRAPHY === */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        color: #00ff41 !important;
        text-shadow: 0 0 8px rgba(0,255,65,0.4), 0 0 20px rgba(0,255,65,0.15);
        letter-spacing: 2px;
    }
    h2 { font-size: 1.3rem !important; }
    h3 { font-size: 1.1rem !important; color: #00ffff !important; text-shadow: 0 0 8px rgba(0,255,255,0.3); }
    p, span, label, div { font-family: 'JetBrains Mono', monospace; }

    /* === GLASSMORPHISM PANELS === */
    [data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(13,17,23,0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0,255,65,0.15);
        border-radius: 16px;
        padding: 8px;
    }

    /* === METRIC CARDS === */
    [data-testid="stMetricValue"] {
        font-family: 'Orbitron', sans-serif !important;
        color: #00ffff !important;
        font-size: 2.2rem !important;
        text-shadow: 0 0 15px rgba(0,255,255,0.5), 0 0 30px rgba(0,255,255,0.2);
        font-weight: 900;
    }
    [data-testid="stMetricLabel"] {
        font-family: 'Rajdhani', sans-serif !important;
        color: #ff003c !important;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-size: 0.8rem !important;
        text-shadow: 0 0 6px rgba(255,0,60,0.3);
    }
    [data-testid="stMetricDelta"] {
        color: #a855f7 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(0,255,255,0.05), rgba(0,255,65,0.03));
        border: 1px solid rgba(0,255,255,0.2);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 0 15px rgba(0,255,255,0.08), inset 0 1px 0 rgba(255,255,255,0.05);
        transition: all 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        border-color: rgba(0,255,255,0.5);
        box-shadow: 0 0 25px rgba(0,255,255,0.15), 0 0 50px rgba(0,255,255,0.05);
        transform: translateY(-2px);
    }

    /* === SIDEBAR === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #050508 0%, #0a0e1a 50%, #050508 100%) !important;
        border-right: 1px solid rgba(0,255,65,0.3);
        box-shadow: 4px 0 20px rgba(0,255,65,0.05);
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        font-size: 0.95rem !important;
    }

    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background: rgba(0,0,0,0.4);
        border-radius: 12px;
        padding: 4px;
        border: 1px solid rgba(0,255,65,0.15);
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
        letter-spacing: 1px;
        color: #8b949e;
        border-radius: 8px;
        padding: 8px 16px;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0,255,65,0.15), rgba(0,255,255,0.1)) !important;
        color: #00ff41 !important;
        border-bottom: 2px solid #00ff41 !important;
        box-shadow: 0 0 12px rgba(0,255,65,0.2);
    }
    .stTabs [data-baseweb="tab-highlight"] { background-color: transparent !important; }

    /* === DATAFRAMES === */
    .dataframe {
        border-collapse: collapse !important;
        width: 100% !important;
        background: rgba(0,0,0,0.5) !important;
        color: #00ff41 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.8rem !important;
        border: 1px solid rgba(0,255,65,0.2) !important;
        border-radius: 8px;
    }
    .dataframe th {
        background: rgba(255,0,60,0.1) !important;
        color: #ff003c !important;
        border: 1px solid rgba(0,255,65,0.15) !important;
        padding: 10px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-family: 'Rajdhani', sans-serif !important;
    }
    .dataframe td {
        border: 1px solid rgba(0,255,65,0.08) !important;
        padding: 8px !important;
        transition: background 0.2s;
    }
    .dataframe tr:hover td { background: rgba(0,255,65,0.05) !important; }

    /* === DIVIDERS === */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #00ff41, #00ffff, #00ff41, transparent);
        box-shadow: 0 0 8px rgba(0,255,65,0.3);
        margin: 1.5rem 0;
    }

    /* === HERO HEADER === */
    .hero-banner {
        position: relative;
        text-align: center;
        padding: 30px 20px 20px 20px;
        margin-bottom: 10px;
        background: linear-gradient(135deg, rgba(0,255,65,0.03), rgba(0,255,255,0.02), rgba(168,85,247,0.02));
        border: 1px solid rgba(0,255,65,0.15);
        border-radius: 20px;
        overflow: hidden;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 300px;
        height: 300px;
        border: 1px solid rgba(0,255,65,0.1);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        animation: radarPulse 3s ease-out infinite;
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 200px;
        height: 200px;
        border: 1px solid rgba(0,255,255,0.08);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        animation: radarPulse 3s ease-out infinite 1s;
    }
    @keyframes radarPulse {
        0% { width: 50px; height: 50px; opacity: 0.6; }
        100% { width: 500px; height: 500px; opacity: 0; }
    }
    .hero-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.8rem;
        font-weight: 900;
        text-transform: uppercase;
        color: #00ff41;
        text-shadow: 0 0 20px rgba(0,255,65,0.5), 0 0 40px rgba(0,255,65,0.2),
            0.05em 0 0 rgba(255,0,60,0.4), -0.025em -0.025em 0 rgba(0,255,255,0.4);
        animation: heroGlitch 4s infinite;
        position: relative;
        z-index: 2;
        margin: 0;
    }
    @keyframes heroGlitch {
        0%,87%,100% { text-shadow: 0 0 20px rgba(0,255,65,0.5), 0.05em 0 0 rgba(255,0,60,0.4), -0.025em -0.025em 0 rgba(0,255,255,0.4); }
        88% { text-shadow: -0.05em 0.02em 0 rgba(255,0,60,0.7), 0.025em -0.02em 0 rgba(0,255,255,0.7), 0 0 30px rgba(0,255,65,0.8); }
        89% { text-shadow: 0.05em -0.02em 0 rgba(255,0,60,0.5), -0.05em 0.02em 0 rgba(0,255,255,0.5); }
        90% { text-shadow: 0 0 20px rgba(0,255,65,0.5), 0.05em 0 0 rgba(255,0,60,0.4), -0.025em -0.025em 0 rgba(0,255,255,0.4); }
    }
    .hero-subtitle {
        font-family: 'Rajdhani', sans-serif;
        font-size: 1rem;
        color: #8b949e;
        letter-spacing: 4px;
        text-transform: uppercase;
        position: relative;
        z-index: 2;
        margin-top: 5px;
    }
    .hero-subtitle span { color: #00ffff; }
    .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(0,255,65,0.15), rgba(0,255,255,0.1));
        border: 1px solid rgba(0,255,65,0.3);
        border-radius: 20px;
        padding: 4px 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #00ff41;
        margin-top: 10px;
        position: relative;
        z-index: 2;
    }
    .hero-badge .live-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        background: #00ff41;
        border-radius: 50%;
        margin-right: 6px;
        animation: blink 1.5s infinite;
        box-shadow: 0 0 6px #00ff41;
    }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

    /* === SIDEBAR BRAND === */
    .sidebar-brand {
        text-align: center;
        padding: 15px 10px;
        border-bottom: 1px solid rgba(0,255,65,0.15);
        margin-bottom: 15px;
    }
    .sidebar-brand-icon {
        font-size: 2.5rem;
        display: block;
        margin-bottom: 4px;
        filter: drop-shadow(0 0 8px rgba(0,255,65,0.5));
    }
    .sidebar-brand-name {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.1rem;
        font-weight: 900;
        color: #00ff41;
        text-shadow: 0 0 10px rgba(0,255,65,0.4);
        letter-spacing: 3px;
    }
    .sidebar-brand-sub {
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.65rem;
        color: #8b949e;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* === HEALTH CARDS === */
    .health-card {
        background: rgba(0,0,0,0.3);
        border: 1px solid rgba(0,255,65,0.12);
        border-radius: 8px;
        padding: 6px 10px;
        margin: 4px 0;
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        transition: border-color 0.3s;
    }
    .health-card:hover { border-color: rgba(0,255,65,0.35); }
    .health-card .h-icon { font-size: 1rem; }
    .health-card .h-name { color: #8b949e; flex: 1; }
    .health-card .h-status { font-weight: 700; }
    .h-online { color: #00ff41; text-shadow: 0 0 6px rgba(0,255,65,0.4); }
    .h-offline { color: #ff003c; text-shadow: 0 0 6px rgba(255,0,60,0.4); }
    .h-warn { color: #ff6600; }

    /* === ATTACK REPLAY TERMINAL === */
    .replay-terminal {
        background: rgba(0,0,0,0.7);
        border: 1px solid rgba(0,255,65,0.25);
        padding: 20px;
        font-family: 'JetBrains Mono', monospace;
        color: #00ff41;
        border-radius: 12px;
        max-height: 450px;
        overflow-y: auto;
        position: relative;
        font-size: 0.85rem;
        line-height: 1.8;
        box-shadow: inset 0 0 30px rgba(0,0,0,0.5), 0 0 15px rgba(0,255,65,0.05);
    }
    .replay-terminal::before {
        content: '● ● ●';
        display: block;
        color: #ff003c;
        font-size: 0.6rem;
        letter-spacing: 4px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(0,255,65,0.1);
        margin-bottom: 10px;
    }

    /* === SECTION HEADERS === */
    .section-hdr {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }
    .section-hdr .s-icon {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, rgba(0,255,65,0.15), rgba(0,255,255,0.1));
        border: 1px solid rgba(0,255,65,0.3);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        box-shadow: 0 0 10px rgba(0,255,65,0.1);
    }
    .section-hdr .s-text {
        font-family: 'Orbitron', sans-serif;
        font-size: 1rem;
        color: #00ffff;
        text-shadow: 0 0 8px rgba(0,255,255,0.3);
        letter-spacing: 2px;
    }

    /* === BUTTONS === */
    .stButton > button {
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        background: linear-gradient(135deg, rgba(0,255,65,0.1), rgba(0,255,255,0.05)) !important;
        border: 1px solid rgba(0,255,65,0.3) !important;
        color: #00ff41 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        border-color: #00ff41 !important;
        box-shadow: 0 0 15px rgba(0,255,65,0.2) !important;
        transform: translateY(-1px);
    }

    /* === SCROLLBAR === */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0a0a0f; }
    ::-webkit-scrollbar-thumb { background: rgba(0,255,65,0.3); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(0,255,65,0.5); }

    /* === MISC === */
    .stSelectbox label, .stMultiSelect label, .stSlider label {
        font-family: 'Rajdhani', sans-serif !important;
        color: #8b949e !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    [data-testid="stExpander"] {
        background: rgba(0,0,0,0.3);
        border: 1px solid rgba(0,255,65,0.12);
        border-radius: 10px;
    }
    .stInfo, .stWarning { border-radius: 10px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)


# === HELPER FUNCTIONS ===

LOG_FILE = os.path.join("logs", "honeypot.json")
PROFILES_FILE = os.path.join("logs", "attacker_profiles.json")

NEON_COLORS = ['#00ff41', '#00ffff', '#ff003c', '#ff6600', '#a855f7', '#f43f5e', '#fbbf24']

def neon_layout(fig, showlegend=False):
    """Apply premium neon styling to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#8b949e', family='JetBrains Mono, monospace', size=11),
        showlegend=showlegend,
        xaxis=dict(gridcolor='rgba(0,255,65,0.08)', zerolinecolor='rgba(0,255,65,0.15)'),
        yaxis=dict(gridcolor='rgba(0,255,65,0.08)', zerolinecolor='rgba(0,255,65,0.15)'),
        margin=dict(l=40, r=20, t=30, b=40),
    )
    return fig

def load_data():
    """Load JSON logs OR MongoDB events into a Pandas DataFrame"""
    # Phase 1: Try MongoDB first
    try:
        import sys
        _server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'server'))
        if _server_dir not in sys.path:
            sys.path.insert(0, _server_dir)
        import mongo_client
        
        events_col = mongo_client.get_events_col()
        if events_col is not None:
            # Get all events, drop the _id field which pandas doesn't need
            mongo_data = list(events_col.find({}, {"_id": 0}))
            if mongo_data:
                df = pd.DataFrame(mongo_data)
                df['timestamp'] = pd.to_datetime(
                    df['timestamp'].astype(str).str.replace(r'[+-]\d{2}:\d{2}$', '', regex=True),
                    errors='coerce'
                )
                return df
    except Exception as e:
        st.warning(f"MongoDB connection failed: {e}. Falling back to local JSON logs.")

    data = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                for line in f:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue 
        except Exception as e:
            st.error(f"Error reading log file: {e}")
    else:
        st.warning(f"Log file not found at {LOG_FILE}. Waiting for attacks...")
        return pd.DataFrame()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(
        df['timestamp'].astype(str).str.replace(r'[+-]\d{2}:\d{2}$', '', regex=True),
        errors='coerce'
    )
    return df

def load_profiles():
    """Load attacker intelligence profiles"""
    profiles = []
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, 'r') as f:
                for line in f:
                    try:
                        profiles.append(json.loads(line.strip()))
                    except:
                        continue
        except:
            pass
    return profiles


def compute_tools_from_events(df):
    """Detect hacking tools directly from MongoDB events — works without profiles file."""
    import re
    tools = Counter()
    if df.empty:
        return tools

    CMD_PATTERNS = {
        'nmap': r'\bnmap\b', 'hydra': r'\bhydra\b', 'masscan': r'\bmasscan\b',
        'sqlmap': r'\bsqlmap\b', 'wget': r'\bwget\b', 'base64': r'\bbase64\b',
        'netcat/nc': r'\bnc\s', 'metasploit': r'\bmsfconsole\b|\bmsfvenom\b',
        'curl': r'\bcurl\b', 'chmod +x': r'\bchmod\b.*\+x',
    }

    for _, row in df.iterrows():
        details = row.get('details', {}) or {}
        if isinstance(details, str):
            try: details = json.loads(details)
            except: details = {}
        if not isinstance(details, dict): details = {}

        etype = str(row.get('event_type', ''))

        # SSH shell commands
        cmd = str(details.get('command', ''))
        if cmd and cmd != 'None':
            for tool, pattern in CMD_PATTERNS.items():
                if re.search(pattern, cmd, re.IGNORECASE):
                    tools[tool] += 1

        # SSH client fingerprints (AUTH_LOGIN, FINGERPRINT events)
        ssh_c = str(details.get('ssh_client', '')).lower()
        if ssh_c and ssh_c not in ('none', '', 'unknown'):
            if 'libssh' in ssh_c: tools['libssh (Brute-forcer)'] += 1
            if 'paramiko' in ssh_c: tools['Paramiko (Python SSH)'] += 1
            if 'hydra' in ssh_c or 'thc' in ssh_c: tools['THC Hydra'] += 1
            if 'ssh-2.0-go' in ssh_c or 'go-' in ssh_c: tools['Go SSH Client'] += 1
            if 'nmap' in ssh_c: tools['Nmap'] += 1
            if 'medusa' in ssh_c: tools['Medusa'] += 1
            if 'ncrack' in ssh_c: tools['Ncrack'] += 1
            if 'putty' in ssh_c: tools['PuTTY'] += 1

        # FINGERPRINT event message field
        msg = str(row.get('message', '')).lower()
        if etype == 'FINGERPRINT':
            if 'libssh' in msg: tools['libssh (Brute-forcer)'] += 1
            if 'ssh-2.0-go' in msg: tools['Go SSH Client'] += 1
            if 'paramiko' in msg: tools['Paramiko (Python SSH)'] += 1
            if 'hydra' in msg or 'thc' in msg: tools['THC Hydra'] += 1
            if 'ncrack' in msg: tools['Ncrack'] += 1
            if 'medusa' in msg: tools['Medusa'] += 1
            if 'dropbear' in msg: tools['Dropbear SSH'] += 1

        # HTTP user agents (HTTP_SCAN events)
        ua = str(details.get('user_agent', '')).lower()
        if ua and ua not in ('none', '', 'unknown', '-'):
            if 'masscan' in ua: tools['Masscan (Scanner)'] += 1
            if 'zgrab' in ua: tools['ZGrab (Scanner)'] += 1
            if 'sqlmap' in ua: tools['SQLMap'] += 1
            if 'nmap' in ua: tools['Nmap Scripting Engine'] += 1
            if 'nikto' in ua: tools['Nikto (Web Scanner)'] += 1
            if 'nuclei' in ua: tools['Nuclei Scanner'] += 1
            if 'python-requests' in ua or 'python/' in ua: tools['Python Scripts'] += 1
            if 'curl' in ua: tools['curl (Web Probe)'] += 1
            if 'censys' in ua: tools['Censys Internet Scanner'] += 1
            if 'shodan' in ua: tools['Shodan Crawler'] += 1
            if 'l9explore' in ua or 'l9tcpid' in ua: tools['l9s (LeakIX Scanner)'] += 1
            if 'go-http' in ua or 'go/1.' in ua: tools['Go HTTP Client'] += 1
            if 'dirbuster' in ua or 'gobuster' in ua: tools['DirBuster/GoBuster'] += 1
            if 'hydra' in ua: tools['THC Hydra'] += 1
            if 'palo alto' in ua: tools['Palo Alto Scanner'] += 1

    return tools

def get_stats(df):
    """Calculate key metrics"""
    if df.empty:
        return 0, 0, "N/A", "N/A"
    
    total_attacks = len(df[df['event_type'] == 'AUTH_LOGIN'])
    unique_ips = df['ip'].nunique()
    
    auth_events = df[df['event_type'] == 'AUTH_LOGIN']
    top_user = "N/A"
    top_pass = "N/A"
    
    if not auth_events.empty:
        users = auth_events['details'].apply(lambda x: x.get('username') if isinstance(x, dict) else None).dropna()
        if not users.empty: top_user = users.mode()[0]
        
        passes = auth_events['details'].apply(lambda x: x.get('password') if isinstance(x, dict) else None).dropna()
        if not passes.empty: top_pass = passes.mode()[0]
        
    return total_attacks, unique_ips, top_user, top_pass

@st.cache_data(ttl=3600, show_spinner=False)
def batch_geoip_lookup(ips):
    """Batch GeoIP lookup (cached for 1 hour) to avoid API rate limits."""
    results = {}
    if not ips:
        return results
        
    public_ips = [ip for ip in ips if ip and not str(ip).startswith(('127.', '10.', '192.168.', '172.', '0.', 'unknown', 'local')) and ip != 'N/A']
    
    import requests
    for i in range(0, min(len(public_ips), 300), 100):  # limit to 300 for dashboard
        batch = public_ips[i:i+100]
        try:
            payload = [{'query': ip, 'fields': 'query,status,country,city,lat,lon'} for ip in batch]
            resp = requests.post('http://ip-api.com/batch', json=payload, timeout=5)
            if resp.status_code == 200:
                for entry in resp.json():
                    if entry.get('status') == 'success':
                        results[entry['query']] = {
                            'lat': entry.get('lat', 0),
                            'lon': entry.get('lon', 0),
                            'origin': f"{entry.get('country','?')} ({entry.get('city','?')})"
                        }
        except Exception as e:
            pass
            
    return results

def get_geo_for_ip(ip, geo_dict):
    """Helper to map a single IP from the cached batch results or generate fake if local."""
    if not isinstance(ip, str) or not ip or ip in ('127.0.0.1', 'localhost', 'N/A', 'local'):
        return generate_fake_geo(ip)
        
    if ip in geo_dict:
        g = geo_dict[ip]
        return pd.Series([g['lat'], g['lon'], g['origin']])
        
    return generate_fake_geo(ip)

def generate_fake_geo(ip):
    """Fallback: Deterministic fake geo for local/private IPs"""
    if not isinstance(ip, str) or not ip:
        return pd.Series([0.0, 0.0, "Unknown"])

    hotspots = [
        (55.75, 37.61, "Russia (Moscow)"),
        (39.90, 116.40, "China (Beijing)"),
        (37.77, -122.41, "USA (San Francisco)"),
        (51.50, -0.12, "UK (London)"),
        (35.68, 139.69, "Japan (Tokyo)"),
        (-23.55, -46.63, "Brazil (São Paulo)"),
        (28.61, 77.20, "India (New Delhi)"),
        (48.85, 2.35, "France (Paris)"),
        (40.71, -74.00, "USA (New York)"),
        (31.23, 121.47, "China (Shanghai)")
    ]
    
    h = int(hashlib.md5(ip.encode()).hexdigest(), 16)
    idx = h % len(hotspots)
    jitter_lat = (h % 100) / 1000.0 - 0.05
    jitter_lon = ((h // 100) % 100) / 1000.0 - 0.05
    
    lat = hotspots[idx][0] + jitter_lat
    lon = hotspots[idx][1] + jitter_lon
    country = hotspots[idx][2]
    
    return pd.Series([lat, lon, country])

@st.cache_data(ttl=30, show_spinner=False)
def check_health():
    """Innovation 3: Check health of all honeypot components"""
    status = {}
    
    # Cloud Database (MongoDB)
    try:
        import sys
        _server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'server'))
        if _server_dir not in sys.path:
            sys.path.insert(0, _server_dir)
        import mongo_client
        if mongo_client.get_db() is not None:
            status['Cloud Database (MongoDB)'] = ('🟢', 'ONLINE')
        else:
            status['Cloud Database (MongoDB)'] = ('🔴', 'OFFLINE')
    except Exception:
        status['Cloud Database (MongoDB)'] = ('🔴', 'ERROR')

    # SSH Server (try Docker service name first, then localhost)
    ssh_online = False
    for host in ['honeypot', '127.0.0.1']:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((host, 2222))
            s.close()
            ssh_online = True
            break
        except:
            continue
    status['SSH Server'] = ('🟢', 'ONLINE') if ssh_online else ('🔴', 'OFFLINE')
    
    # AI Engine Health (Groq Cloud + Ollama)
    try:
        import requests as _req
        # Check Groq Cloud
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            try:
                r = _req.get("https://api.groq.com/openai/v1/models",
                            headers={"Authorization": f"Bearer {groq_key}"}, timeout=3)
                if r.status_code == 200:
                    status['AI Engine (Groq Cloud)'] = ('🟢', 'ONLINE')
                elif r.status_code == 403:
                    # Groq blocks cloud provider IPs (Azure/AWS/GCP) but key is valid
                    status['AI Engine (Groq Cloud)'] = ('🟢', 'KEY SET')
                else:
                    status['AI Engine (Groq Cloud)'] = ('🟡', f'ERROR {r.status_code}')
            except:
                status['AI Engine (Groq Cloud)'] = ('🔴', 'OFFLINE')
        else:
            status['AI Engine (Groq Cloud)'] = ('⚪', 'NO KEY')
        
        # Check Ollama (local fallback)
        try:
            r2 = _req.get('http://localhost:11434/api/tags', timeout=2)
            if r2.status_code == 200:
                status['AI Fallback (Ollama)'] = ('🟢', 'STANDBY')
            else:
                status['AI Fallback (Ollama)'] = ('🟡', 'ERROR')
        except:
            status['AI Fallback (Ollama)'] = ('⚪', 'NOT RUNNING')
    except:
        status['AI Engine'] = ('🔴', 'OFFLINE')
    
    # Docker (detect if we're running inside a container)
    if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER'):
        status['Docker Sandbox'] = ('🟢', 'CONTAINERIZED')
    else:
        try:
            import subprocess
            result = subprocess.run(['docker', '--version'], capture_output=True, timeout=3)
            if result.returncode == 0:
                status['Docker Sandbox'] = ('🟢', 'AVAILABLE')
            else:
                status['Docker Sandbox'] = ('🔴', 'UNAVAILABLE')
        except:
            status['Docker Sandbox'] = ('🔴', 'NOT INSTALLED')
    
    # Log File
    if os.path.exists(LOG_FILE):
        size = os.path.getsize(LOG_FILE)
        status['Log Database'] = ('🟢', f'{size:,} bytes')
    else:
        status['Log Database'] = ('🔴', 'NO DATA')
    
    return status


# === MAIN UI ===

# Hero Banner
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">NEURO-TRAP</div>
    <div class="hero-subtitle">AI-Powered <span>Cyber Immune System</span> — Threat Intelligence Network</div>
    <div class="hero-badge"><span class="live-dot"></span> SYSTEM ACTIVE — ALL SENSORS ONLINE</div>
</div>
""", unsafe_allow_html=True)

# === SIDEBAR ===
with st.sidebar:
    # Brand section
    st.markdown("""
    <div class="sidebar-brand">
        <span class="sidebar-brand-icon">🕸️</span>
        <div class="sidebar-brand-name">NEURO-TRAP</div>
        <div class="sidebar-brand-sub">Cyber Immune System v2.0</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Health Monitor
    st.markdown("### 🩺 SYSTEM HEALTH")
    health = check_health()
    for component, (icon, state) in health.items():
        css_class = 'h-online' if '🟢' in icon else ('h-offline' if '🔴' in icon else 'h-warn')
        st.markdown(f"""
        <div class="health-card">
            <span class="h-icon">{icon}</span>
            <span class="h-name">{component}</span>
            <span class="h-status {css_class}">{state}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### ⚡ ENGINE")
    st.markdown("""
    <div class="health-card" style="border-color: rgba(0,255,255,0.3);">
        <span class="h-icon">⚡</span>
        <span class="h-name">Groq Cloud</span>
        <span class="h-status h-online">● PRIMARY</span>
    </div>
    <div class="health-card" style="border-color: rgba(0,255,65,0.15); margin-top: 4px;">
        <span class="h-icon">🧠</span>
        <span class="h-name">Ollama Local</span>
        <span class="h-status" style="color: #8b949e;">↩ FALLBACK</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button('🔄 RE-SYNC SENSORS'):
        st.rerun()
    
    st.divider()
    st.markdown(f"""
    <div style="text-align:center; font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#555;">
        <div style="color:#00ff41; font-size:0.7rem;">⏱ {datetime.now().strftime('%H:%M:%S')}</div>
        <div style="margin-top:4px;">Neuro-Trap v2.0 | Port 2222</div>
    </div>
    """, unsafe_allow_html=True)

# Load Data
df = load_data()

if not df.empty:
    # === 4 TABS ===
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 CORE INTELLIGENCE",
        "📊 THREAT ANALYTICS", 
        "🧬 CYBER IMMUNE SYSTEM",
        "🔁 ATTACK REPLAY"
    ])
    
    # =============================================
    # TAB 1: CORE INTELLIGENCE (Phase 1)
    # =============================================
    with tab1:
        # --- METRICS ROW --- (Bug 1 fix: properly inside tab1)
        col1, col2, col3, col4 = st.columns(4)
        total_attacks, unique_ips, top_user, top_pass = get_stats(df)
        
        col1.metric("CRITICAL INCIDENTS", total_attacks, "Active Threats")
        col2.metric("UNIQUE ADVERSARIES", unique_ips, "- Tracking")
        col3.metric("TOP TARGET VECTOR", top_user, "Username")
        col4.metric("MOST BREACHED KEY", top_pass, "Password")

        st.divider()

        # --- MAP & CHART ROW ---
        col_map, col_pie = st.columns([2, 1])

        with col_map:
            st.subheader("🌍 LIVE GLOBAL THREAT MAP")
            unique_ips_df = df.drop_duplicates(subset=['ip']).copy()
            if not unique_ips_df.empty and 'ip' in unique_ips_df.columns:
                # Innovation 2: Fast Batched GeoIP caching real locations
                ip_list = unique_ips_df['ip'].tolist()
                geo_dict = batch_geoip_lookup(ip_list)
                unique_ips_df[['lat', 'lon', 'origin']] = unique_ips_df['ip'].apply(lambda x: get_geo_for_ip(x, geo_dict))
                
                # Bug 8 fix: use scatter_map instead of deprecated scatter_mapbox
                fig_map = px.scatter_map(
                    unique_ips_df, 
                    lat="lat", 
                    lon="lon", 
                    hover_name="ip", 
                    hover_data=["origin"],
                    color_discrete_sequence=["#ff003c"], 
                    zoom=1.5, 
                    height=400
                )
                fig_map.update_layout(
                    map_style="carto-darkmatter",
                    margin={"r":0,"t":0,"l":0,"b":0},
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_map, use_container_width=True, theme=None)
            else:
                st.info("No IP data available for mapping.")

        with col_pie:
            st.subheader("📊 THREAT VECTORS")
            if 'event_type' in df.columns:
                event_counts = df['event_type'].value_counts()
                fig = px.bar(
                    x=event_counts.index, 
                    y=event_counts.values,
                    color=event_counts.index,
                    color_discrete_sequence=px.colors.sequential.Aggrnyl,
                    labels={'x': 'Event Type', 'y': 'Count'}
                )
                neon_layout(fig)
                st.plotly_chart(fig, use_container_width=True, theme=None)

        st.divider()
        
        # --- TIMELINE & PASSWORDS ---
        col_time, col_pass = st.columns([2, 1])
        
        with col_time:
            st.subheader("📈 ATTACK VELOCITY (TIMELINE)")
            timeline_df = df.set_index('timestamp').resample('1min').size().reset_index(name='count')
            fig_time = px.line(
                timeline_df, 
                x='timestamp', 
                y='count',
                markers=True
            )
            fig_time.update_traces(line=dict(color='#00ffff', width=3), marker=dict(size=8, color='#ff003c', symbol='diamond'))
            neon_layout(fig_time)
            fig_time.update_layout(xaxis_title="Time", yaxis_title="Events / Minute")
            st.plotly_chart(fig_time, use_container_width=True, theme=None)
            
        with col_pass:
             st.subheader("🔑 BREACHED CREDENTIALS")
             auth_events = df[df['event_type'] == 'AUTH_LOGIN']
             if not auth_events.empty:
                 passes = auth_events['details'].apply(lambda x: x.get('password') if isinstance(x, dict) else None).dropna()
                 if not passes.empty:
                     pass_counts = passes.value_counts().head(5)
                     fig_pass = px.pie(
                         values=pass_counts.values, 
                         names=pass_counts.index,
                         hole=0.4,
                         color_discrete_sequence=px.colors.sequential.Plasma
                     )
                     neon_layout(fig_pass)
                     st.plotly_chart(fig_pass, use_container_width=True, theme=None)

        st.divider()

        # --- RAW TERMINAL LOGS ---
        st.subheader("📜 TERMINAL INTERCEPT LOGS")
        
        event_filter = st.multiselect("FILTER BY TYPE", options=df['event_type'].unique(), default=df['event_type'].unique())
        filtered_df = df[df['event_type'].isin(event_filter)]
        filtered_df = filtered_df.sort_values(by='timestamp', ascending=False)
        
        def format_details(x):
            try:
                return json.dumps(x)
            except:
                return str(x)
                
        filtered_df['details_str'] = filtered_df['details'].apply(format_details)
        
        html_table = filtered_df[['timestamp', 'event_type', 'ip', 'message', 'details_str']].to_html(
            classes=['dataframe'],
            index=False,
            escape=False
        )
        st.markdown(html_table, unsafe_allow_html=True)

    # =============================================
    # TAB 2: THREAT ANALYTICS (Phase 2)
    # =============================================
    with tab2:
        st.markdown("## MATHEMATICAL THREAT PROFILING")
        st.markdown("Algorithms active: Time-Based Analytics, Cosine Similarity, Standard Deviation, Markov Chains.")
        
        @st.cache_data(ttl=300, show_spinner="Running AI threat analysis...")
        def cached_analyze(data_json):
            import io
            _df = pd.read_json(io.StringIO(data_json))
            return analyze_threats(_df)

        @st.cache_data(ttl=300, show_spinner="Building Markov Chain...")
        def cached_markov(data_json):
            import io
            _df = pd.read_json(io.StringIO(data_json))
            return build_markov_chain(_df)

        data_json = df.to_json()
        analytics_df = cached_analyze(data_json)
        
        if not analytics_df.empty:
            st.subheader("1. BEHAVIORAL PROFILING & MALWARE MATCHING")
            st.markdown("Identifies Automated Botnets vs Human Adversaries and mathematically matches commands to known payload vectors.")
            st.dataframe(analytics_df, use_container_width=True, hide_index=True)
            
            st.divider()
            
            st.subheader("2. PREDICTIVE ATTACKER MODELING (MARKOV CHAINS)")
            st.markdown("Uses probabilistic matrices to predict the adversary's next move based on global historical data.")
            
            predictions_df = cached_markov(data_json)
            if not predictions_df.empty:
                st.dataframe(predictions_df, use_container_width=True, hide_index=True)
            else:
                st.info("Gathering more command sequence data to build the Markov Chain...")
        else:
            st.warning("Insufficient COMMAND data to generate mathematical profiles. Waiting for an adversary to interact with the shell...")

    # =============================================
    # TAB 3: CYBER IMMUNE SYSTEM (Phase 5)
    # =============================================
    with tab3:
        st.markdown("## 🧬 CYBER IMMUNE SYSTEM")
        st.markdown("*Biological defense: Antibodies → Counter-Intel | White Blood Cells → Auto-Firewall | Immune Memory → AI Psychology*")
        
        profiles = load_profiles()
        
        # --- Counter-Intelligence Profiles ---
        st.subheader("🔬 ATTACKER INTELLIGENCE PROFILES")
        if profiles:
            profile_data = []
            for p in profiles:
                profile_data.append({
                    "IP": p.get('ip', '?'),
                    "SSH Client": p.get('ssh_client', '?')[:40],
                    "OS": p.get('os_fingerprint', '?'),
                    "DNA Hash": p.get('attacker_dna', '?')[:12] + '...',
                    "Typing Bio-Hash": p.get('biometric_typing_hash', 'Processing...'),
                    "Threat": p.get('threat_level', '?'),
                    "Classification": p.get('classification', '?'),
                    "Automated?": p.get('is_automated', '?'),
                    "Commands": p.get('total_commands', 0),
                })
            st.dataframe(pd.DataFrame(profile_data), use_container_width=True, hide_index=True)
        else:
            st.info("No attacker profiles yet. Connect to the honeypot via SSH to generate profiles.")
        
        st.divider()
        
        # --- Psychology Analysis ---
        st.subheader("🔮 AI PSYCHOLOGY ANALYSIS")
        psych_events = df[df['event_type'] == 'PSYCHOLOGY'] if 'event_type' in df.columns else pd.DataFrame()
        if not psych_events.empty:
            for _, row in psych_events.iterrows():
                details = row.get('details', {})
                if isinstance(details, dict):
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Classification", details.get('classification', '?'))
                    col_b.metric("Danger Rating", f"{details.get('danger_rating', '?')}/10")
                    col_c.metric("Skill Level", details.get('skill_level', '?'))
                    
                    with st.expander(f"📋 Full Profile — {row.get('ip', '?')}"):
                        st.json(details)
        else:
            st.info("Psychology analysis runs after attacker disconnects. Connect and run 3+ commands to trigger.")
        
        st.divider()
        
        # --- Auto-Firewall Status ---
        st.subheader("🛡️ AUTO-FIREWALL STATUS")
        auth_events = df[df['event_type'] == 'AUTH_LOGIN']
        if not auth_events.empty:
            ip_attempts = auth_events['ip'].value_counts()
            blocked_ips = ip_attempts[ip_attempts >= 3]
            
            col_fw1, col_fw2 = st.columns(2)
            col_fw1.metric("🔴 BLOCKED IPs", len(blocked_ips))
            col_fw2.metric("🟡 MONITORED IPs", len(ip_attempts[ip_attempts < 3]))
            
            if not blocked_ips.empty:
                st.markdown("**Blocked (3+ login attempts):**")
                fw_data = [{"IP": ip, "Attempts": count, "Status": "🔴 BLOCKED"} for ip, count in blocked_ips.items()]
                st.dataframe(pd.DataFrame(fw_data), use_container_width=True, hide_index=True)
        else:
            st.info("No authentication data yet.")
        
        st.divider()
        
        # --- Tools Detected ---
        st.subheader("🔧 DETECTED HACKING TOOLS")

        # Primary: scan events directly from MongoDB
        event_tools = compute_tools_from_events(df)

        # Secondary: also check profiles file if it exists
        profile_tools = Counter()
        if profiles:
            all_tools = []
            for p in profiles:
                all_tools.extend(p.get('tools_detected', []))
            profile_tools = Counter(all_tools)

        # Merge both sources
        merged_tools = event_tools + profile_tools

        if merged_tools:
            fig_tools = px.bar(
                x=list(merged_tools.keys()),
                y=list(merged_tools.values()),
                color=list(merged_tools.keys()),
                color_discrete_sequence=px.colors.sequential.Reds,
                labels={'x': 'Tool / Scanner', 'y': 'Detections'}
            )
            neon_layout(fig_tools)
            st.plotly_chart(fig_tools, use_container_width=True, theme=None)

            st.markdown(f"**{len(merged_tools)} distinct hacking tools/scanners identified from {len(df):,} events.**")
        else:
            st.info("No hacking tools detected yet. Scanners will be identified automatically as they connect.")

    # =============================================
    # TAB 4: LIVE ATTACK REPLAY (Innovation 1)
    # =============================================
    with tab4:
        st.markdown("## 🔁 LIVE ATTACK REPLAY")
        st.markdown("*Watch every attacker's session — SSH commands, FTP logins, HTTP scans, Telnet interactions*")

        # Include ALL meaningful event types — not just COMMAND
        REPLAY_TYPES = ['COMMAND', 'AUTH_LOGIN', 'AUTH_SUCCESS', 'HTTP_SCAN', 'HTTP_AUTH',
                        'TELNET_LOGIN', 'TELNET_COMMAND', 'FTP_LOGIN', 'FTP_COMMAND']
        replay_df = df[df['event_type'].isin(REPLAY_TYPES)].copy()

        if not replay_df.empty:
            replay_df = replay_df.sort_values('timestamp')
            session_ips = replay_df['ip'].dropna().unique().tolist()
            selected_ip = st.selectbox("🎯 Select Attacker Session", session_ips)

            if selected_ip:
                session_events = replay_df[replay_df['ip'] == selected_ip].copy()
                duration_s = (session_events['timestamp'].max() - session_events['timestamp'].min()).total_seconds()

                col_s1, col_s2, col_s3 = st.columns(3)
                col_s1.metric("IP Address", selected_ip)
                col_s2.metric("Total Events", len(session_events))
                col_s3.metric("Session Duration", f"{duration_s:.0f}s")

                speed = st.slider("⏩ Events to Display", 10, 200, 50)

                replay_lines = []
                replay_lines.append(f'<span style="color:#ffcc00">═══ SESSION START: {selected_ip} ═══</span>')
                replay_lines.append(f'<span style="color:#666">Neuro-Trap Honeypot — Connection Established</span>')
                replay_lines.append('')

                for _, row in session_events.head(speed).iterrows():
                    ts = row['timestamp'].strftime('%H:%M:%S') if pd.notna(row['timestamp']) else '??:??:??'
                    etype = row.get('event_type', 'UNKNOWN')
                    details = row.get('details', {}) or {}
                    if isinstance(details, str):
                        try: details = json.loads(details)
                        except: details = {}

                    if etype == 'COMMAND':
                        cmd = details.get('command', row.get('message', '?')) if isinstance(details, dict) else str(details)
                        replay_lines.append(f'<span style="color:#666">[{ts}]</span> <span style="color:#ff003c">root@honeypot:~#</span> <span style="color:#00ff41">{cmd}</span>')
                    elif etype in ('AUTH_LOGIN', 'AUTH_SUCCESS', 'TELNET_LOGIN', 'FTP_LOGIN'):
                        un = details.get('username', '?') if isinstance(details, dict) else '?'
                        pw = details.get('password', '?') if isinstance(details, dict) else '?'
                        color = '#00ff41' if 'SUCCESS' in etype else '#ffcc00'
                        label = '✅ LOGIN SUCCESS' if 'SUCCESS' in etype else '⚡ LOGIN ATTEMPT'
                        replay_lines.append(f'<span style="color:#666">[{ts}]</span> <span style="color:{color}">{label}</span> <span style="color:#ffffff">user={un} pass={pw}</span>')
                    elif etype == 'HTTP_SCAN':
                        method = details.get('method', 'GET') if isinstance(details, dict) else 'GET'
                        path = details.get('path', '/') if isinstance(details, dict) else '/'
                        ua = (details.get('user_agent', '') if isinstance(details, dict) else '')[:40]
                        replay_lines.append(f'<span style="color:#666">[{ts}]</span> <span style="color:#a855f7">🌐 HTTP {method}</span> <span style="color:#00ffff">{path}</span> <span style="color:#555">{ua}</span>')
                    elif etype in ('TELNET_COMMAND', 'FTP_COMMAND'):
                        cmd = details.get('command', '?') if isinstance(details, dict) else '?'
                        proto = '📡 TELNET' if 'TELNET' in etype else '📂 FTP'
                        replay_lines.append(f'<span style="color:#666">[{ts}]</span> <span style="color:#ff6600">{proto}</span> <span style="color:#00ff41">{cmd}</span>')

                replay_lines.append('')
                replay_lines.append(f'<span style="color:#ffcc00">═══ SESSION END ═══</span>')

                replay_html = '<br>'.join(replay_lines)
                st.markdown(f'<div class="replay-terminal">{replay_html}</div>', unsafe_allow_html=True)

                # Command frequency chart (COMMAND events only)
                cmd_only = session_events[session_events['event_type'] == 'COMMAND']
                if not cmd_only.empty:
                    st.subheader("📊 Command Frequency Analysis")
                    cmds = cmd_only['details'].apply(
                        lambda x: x.get('command', '?').split()[0] if isinstance(x, dict) and x.get('command') else '?'
                    )
                    cmd_freq = cmds.value_counts().head(10)
                    fig_cmds = px.bar(
                        x=cmd_freq.index,
                        y=cmd_freq.values,
                        color=cmd_freq.index,
                        color_discrete_sequence=px.colors.sequential.Viridis,
                        labels={'x': 'Command', 'y': 'Count'}
                    )
                    neon_layout(fig_cmds)
                    st.plotly_chart(fig_cmds, use_container_width=True, theme=None)
        else:
            st.warning("No session data yet. Connect to the honeypot to generate replay data.")

else:
    st.markdown("""
    <div style="text-align:center; padding:60px 20px; margin-top:30px;">
        <div style="font-size:4rem; margin-bottom:15px; filter:drop-shadow(0 0 12px rgba(0,255,65,0.4));">🕸️</div>
        <div style="font-family:'Orbitron',sans-serif; font-size:1.4rem; color:#00ff41; text-shadow:0 0 15px rgba(0,255,65,0.4); letter-spacing:3px;">
            DECOY FILESYSTEM INTACT
        </div>
        <div style="font-family:'Rajdhani',sans-serif; font-size:1rem; color:#8b949e; margin-top:10px; letter-spacing:2px;">
            NO INTRUSIONS DETECTED — WAITING FOR CONNECTION ON PORT 2222
        </div>
        <div style="margin-top:20px; font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#555;">
            Connect with: <span style="color:#00ffff;">ssh root@localhost -p 2222</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
