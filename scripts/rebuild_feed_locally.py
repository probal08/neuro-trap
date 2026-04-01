"""
Local feed rebuilder - generates data.json with full GeoIP globe data.
Run this from your PC when GitHub Actions isn't cooperating.
"""
import os, sys, json, certifi, hashlib, urllib.request
from collections import Counter
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

try:
    from public_feed_privacy import sanitize_public_payload, env_bool
except ImportError:
    from scripts.public_feed_privacy import sanitize_public_payload, env_bool

IST = timezone(timedelta(hours=5, minutes=30))
PROJECT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUTPUT = os.path.join(PROJECT, 'public_web', 'data.json')

print("=" * 50)
print("  LOCAL FEED REBUILDER (with GeoIP)")
print("=" * 50)

# --- 1. Connect to MongoDB ---
uri = os.environ.get('MONGODB_URI', '')
if not uri:
    print("[!] Set MONGODB_URI environment variable first!")
    print("    Example: set MONGODB_URI=mongodb+srv://user:pass@host/db")
    sys.exit(1)
client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
db = client['neurotrap']
events = list(db.events.find({}, {'_id': 0}))
print(f"[+] Retrieved {len(events)} events from MongoDB Atlas")

if not events:
    print("[!] No events found. Exiting.")
    sys.exit(1)

# --- 2. Process events ---
ip_counter = Counter()
password_counter = Counter()
username_counter = Counter()
command_counter = Counter()
event_type_counter = Counter()
ssh_client_counter = Counter()
threat_dist = Counter()
tools_detected = Counter()
timeline = {}
sessions = {}

for e in events:
    ip = e.get('ip', 'unknown') or 'unknown'
    if ip and ip != 'N/A' and ip != 'local':
        ip_counter[ip] += 1

    etype = e.get('event_type') or e.get('type', 'UNKNOWN')
    event_type_counter[etype] += 1

    details = e.get('details', {}) or {}
    if isinstance(details, str):
        try: details = json.loads(details)
        except: details = {}
    if not isinstance(details, dict):
        details = {}

    pw = details.get('password')
    if pw: password_counter[pw] += 1
    un = details.get('username')
    if un: username_counter[un] += 1
    cmd = details.get('command')
    if cmd:
        command_counter[cmd] += 1
        if ip not in sessions: sessions[ip] = []
        sessions[ip].append({'command': cmd, 'time': e.get('timestamp', '')})
        for tool in ['nmap','hydra','metasploit','masscan','sqlmap','curl','wget','nc','netcat']:
            if tool in cmd.lower(): tools_detected[tool] += 1

    ssh_c = details.get('ssh_client', '')
    if ssh_c: ssh_client_counter[ssh_c] += 1
    threat = details.get('threat_level', '')
    if threat: threat_dist[threat] += 1

    ts = e.get('timestamp', '')
    if ts:
        try:
            dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
            hour_key = dt.strftime('%Y-%m-%d %H:00')
            timeline[hour_key] = timeline.get(hour_key, 0) + 1
        except: pass

# --- 3. GeoIP Lookup ---
print("[*] Running GeoIP batch lookup...")
public_ips = [ip for ip in ip_counter.keys() 
              if not ip.startswith(('127.', '10.', '192.168.', '172.', '0.', 'unknown', 'local'))]
print(f"[+] {len(public_ips)} public IPs to resolve")

geo_data = {}
# Process in batches of 100 (ip-api.com limit)
for i in range(0, min(len(public_ips), 200), 100):
    batch = public_ips[i:i+100]
    try:
        payload = json.dumps([
            {'query': ip, 'fields': 'query,status,country,city,lat,lon,isp'} 
            for ip in batch
        ])
        req = urllib.request.Request(
            'http://ip-api.com/batch',
            data=payload.encode(),
            headers={'Content-Type': 'application/json'}
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode())
        for entry in data:
            if entry.get('status') == 'success':
                geo_data[entry['query']] = {
                    'lat': entry.get('lat', 0),
                    'lng': entry.get('lon', 0),
                    'country': entry.get('country', 'Unknown'),
                    'city': entry.get('city', 'Unknown'),
                    'isp': entry.get('isp', 'Unknown')
                }
    except Exception as ex:
        print(f"[!] GeoIP batch {i} failed: {ex}")

print(f"[+] GeoIP resolved {len(geo_data)}/{len(public_ips)} IPs")

# --- 4. Build globe points ---
globe_points = []
country_counter = Counter()
for ip_addr, count in ip_counter.most_common(200):
    if ip_addr in geo_data:
        g = geo_data[ip_addr]
        globe_points.append({
            'lat': g['lat'], 'lng': g['lng'],
            'country': g['country'], 'city': g['city'],
            'ip': ip_addr, 'count': count,
            'size': min(count / 3, 1.5)
        })
        country_counter[g['country']] += count

print(f"[+] Built {len(globe_points)} globe points across {len(country_counter)} countries")
for p in globe_points[:5]:
    print(f"    {p['ip']:18s} -> {p['city']}, {p['country']} ({p['count']} attacks)")

# --- 5. Build all data ---
top_ips = [{'ip': ip, 'count': c} for ip, c in ip_counter.most_common(10)]

recent_events = []
for e in events[-200:]:
    recent_events.append({
        'timestamp': e.get('timestamp', ''),
        'type': e.get('event_type') or e.get('type', 'UNKNOWN'),
        'ip': e.get('ip', 'N/A'),
        'message': e.get('message', ''),
        'details': json.dumps(e.get('details', ''))[:120] if e.get('details') else ''
    })
recent_events.reverse()

replay_sessions = []
for ip, cmds in list(sessions.items())[:5]:
    if cmds:
        replay_sessions.append({'ip': ip, 'commands': cmds})

profiles = []
seen_ips = {}
for e in events:
    ip = e.get('ip', 'unknown') or 'unknown'
    details = e.get('details', {}) or {}
    if isinstance(details, str):
        try: details = json.loads(details)
        except: details = {}
    if not isinstance(details, dict): details = {}
    if ip not in seen_ips:
        seen_ips[ip] = {
            'ip': ip,
            'ssh_client': details.get('ssh_client', 'Unknown'),
            'os': details.get('os_fingerprint', 'Unknown'),
            'dna': hashlib.sha256(ip.encode()).hexdigest()[:12],
            'bio_hash': hashlib.md5(ip.encode()).hexdigest()[:8],
            'threat': details.get('threat_level', 'MEDIUM'),
            'classification': details.get('attacker_class', 'Scanner'),
            'automated': details.get('is_automated', 'Unknown'),
            'commands': 0
        }
    seen_ips[ip]['commands'] += 1

profiles = list(seen_ips.values())[:20]
for p in profiles:
    p['automated'] = 'YES' if p['automated'] else 'NO'

blocked_ips = [{'ip': ip, 'attempts': count} for ip, count in ip_counter.most_common() if count >= 3][:10]
top_creds = [{'cred': f"{u}:{p}", 'count': 1} for u, p in zip(username_counter.keys(), password_counter.keys())][:8]
attacks_over_time = [{'time': t, 'count': c} for t, c in sorted(timeline.items())[-24:]]

data = {
    'last_updated': datetime.now(IST).isoformat(),
    'total_attacks': len(events),
    'unique_ips': len(ip_counter),
    'top_user': username_counter.most_common(1)[0][0] if username_counter else '-',
    'top_pass': password_counter.most_common(1)[0][0] if password_counter else '-',
    'event_distribution': dict(event_type_counter.most_common(8)),
    'top_countries': [{'country': c, 'count': n} for c, n in country_counter.most_common(10)],
    'globe_points': globe_points,
    'attacks_over_time': attacks_over_time,
    'top_ips': top_ips,
    'top_creds': top_creds,
    'top_passwords': [{'password': p, 'count': c} for p, c in password_counter.most_common(8)],
    'threat_distribution': dict(threat_dist) if threat_dist else {'HIGH': 1},
    'tools_detected': dict(tools_detected),
    'profiles': profiles,
    'blocked_ips': blocked_ips,
    'monitored_ips_count': len(blocked_ips),
    'monitored_ips': blocked_ips,
    'replay_sessions': replay_sessions,
    'recent_events': recent_events
}

include_replay = env_bool(os.environ.get('NEUROTRAP_PUBLIC_INCLUDE_REPLAY'), default=False)
include_event_details = env_bool(os.environ.get('NEUROTRAP_PUBLIC_INCLUDE_EVENT_DETAILS'), default=False)
data = sanitize_public_payload(
    data,
    include_replay=include_replay,
    include_event_details=include_event_details,
)
print(f"[+] Public feed privacy mode active (replay={include_replay}, event_details={include_event_details})")

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, 'w') as f:
    json.dump(data, f, indent=2, default=str)

print(f"\n[+] data.json written: {OUTPUT}")
print(f"    Total Events:  {data['total_attacks']}")
print(f"    Unique IPs:    {data['unique_ips']}")
print(f"    Globe Points:  {len(globe_points)}")
print(f"    Countries:     {len(country_counter)}")
print("=" * 50)
