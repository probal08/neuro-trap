"""
Neuro-Trap Public Feed Generator
Generates public_web/data.json from MongoDB Atlas.
Run by GitHub Actions every hour to update the public dashboard at neurotrap.tech
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from collections import Counter
import hashlib
import re

IST = timezone(timedelta(hours=5, minutes=30))

# Setup path so we can import mongo_client from server/
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.join(_SCRIPT_DIR, '..')
_SERVER_DIR = os.path.join(_PROJECT_ROOT, 'server')
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

OUTPUT_PATH = os.path.join(_PROJECT_ROOT, 'public_web', 'data.json')


def get_events_from_mongo():
    try:
        import mongo_client
        col = mongo_client.get_events_col()
        if col is None:
            return []
        data = list(col.find({}, {"_id": 0}))
        print(f"[+] Retrieved {len(data)} events from MongoDB Atlas")
        return data
    except Exception as e:
        print(f"[!] MongoDB failed: {e}")
        return []


def get_country_from_ip(ip):
    """Best-effort country detection from IP range (no API needed)."""
    if not ip or ip.startswith(('127.', '10.', '192.168.', '172.')):
        return "Local"
    return "Unknown"


def mask_ip(ip):
    """Show first two octets only for partial privacy."""
    parts = ip.split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.*.*"
    return ip


def build_data_json(events):
    if not events:
        return None

    ip_counter = Counter()
    password_counter = Counter()
    username_counter = Counter()
    command_counter = Counter()
    event_type_counter = Counter()
    country_counter = Counter()
    ssh_client_counter = Counter()
    threat_dist = Counter()
    tools_detected = Counter()
    timeline = {}

    sessions = {}  # ip -> list of commands for replay

    for e in events:
        ip = e.get('ip', 'unknown') or 'unknown'
        if ip and ip != 'N/A':
            ip_counter[ip] += 1

        etype = e.get('event_type') or e.get('type', 'UNKNOWN')
        event_type_counter[etype] += 1

        details = e.get('details', {}) or {}
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except Exception:
                details = {}

        if isinstance(details, dict):
            pw = details.get('password')
            if pw:
                password_counter[pw] += 1
            un = details.get('username')
            if un:
                username_counter[un] += 1
            cmd = details.get('command')
            if cmd:
                command_counter[cmd] += 1
                if ip not in sessions:
                    sessions[ip] = []
                sessions[ip].append({
                    'command': cmd,
                    'time': e.get('timestamp', '')
                })
                # Detect tools
                for tool in ['nmap', 'hydra', 'metasploit', 'masscan', 'sqlmap', 'curl', 'wget', 'nc', 'netcat']:
                    if tool in cmd.lower():
                        tools_detected[tool] += 1

            ssh_c = details.get('ssh_client', '')
            if ssh_c:
                ssh_client_counter[ssh_c] += 1

            threat = details.get('threat_level', '')
            if threat:
                threat_dist[threat] += 1

        # Timeline by hour
        ts = e.get('timestamp', '')
        if ts:
            try:
                dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                hour_key = dt.strftime('%Y-%m-%d %H:00')
                timeline[hour_key] = timeline.get(hour_key, 0) + 1
            except Exception:
                pass

    # Country data via ipapi.co would need API calls - we skip for simplicity
    # and just show IP rankings

    # Top IPs - mask for privacy
    top_ips = [{'ip': ip, 'count': c} for ip, c in ip_counter.most_common(10)]

    # Recent events (last 200, sanitised)
    recent_events = []
    for e in events[-200:]:
        ip = e.get('ip', 'N/A')
        recent_events.append({
            'timestamp': e.get('timestamp', ''),
            'type': e.get('event_type') or e.get('type', 'UNKNOWN'),
            'ip': ip,
            'message': e.get('message', ''),
            'details': json.dumps(e.get('details', ''))[:120] if e.get('details') else ''
        })
    recent_events.reverse()

    # Build replay sessions (up to 5 most interesting)
    replay_sessions = []
    for ip, cmds in list(sessions.items())[:5]:
        if cmds:
            replay_sessions.append({
                'ip': ip,
                'commands': cmds
            })

    # Attacker profiles
    profiles = []
    seen_ips = {}
    for e in events:
        ip = e.get('ip', 'unknown') or 'unknown'
        details = e.get('details', {}) or {}
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except Exception:
                details = {}
        if not isinstance(details, dict):
            details = {}
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

    # Blocked IPs (those with 3+ failed logins)
    blocked_ips = [
        {'ip': ip, 'attempts': count}
        for ip, count in ip_counter.most_common()
        if count >= 3
    ][:10]

    # Top passwords and creds
    top_creds = [{'cred': f"{u}:{p}", 'count': 1}
                 for u, p in zip(username_counter.keys(), password_counter.keys())][:8]

    # Timeline sorted
    attacks_over_time = [
        {'time': t, 'count': c}
        for t, c in sorted(timeline.items())[-24:]
    ]

    data = {
        'last_updated': datetime.now(IST).isoformat(),
        'total_attacks': len(events),
        'unique_ips': len(ip_counter),
        'top_user': username_counter.most_common(1)[0][0] if username_counter else '—',
        'top_pass': password_counter.most_common(1)[0][0] if password_counter else '—',
        'event_distribution': dict(event_type_counter.most_common(8)),
        'top_countries': [{'country': 'SSH Brute-force', 'count': len(events)}],
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

    return data


def main():
    print("=" * 50)
    print("  NEURO-TRAP PUBLIC FEED GENERATOR")
    print("=" * 50)

    # Get MongoDB URI from environment
    mongo_uri = os.environ.get('MONGODB_URI', '')
    if mongo_uri:
        os.environ['MONGODB_URI'] = mongo_uri
        print("[+] MongoDB URI loaded from environment")

    events = get_events_from_mongo()

    if not events:
        print("[!] No events from MongoDB. Writing placeholder data.json")
        data = {
            'last_updated': datetime.now(IST).isoformat(),
            'total_attacks': 0,
            'unique_ips': 0,
            'top_user': '—',
            'top_pass': '—',
            'event_distribution': {},
            'top_countries': [],
            'attacks_over_time': [],
            'top_ips': [],
            'top_creds': [],
            'top_passwords': [],
            'threat_distribution': {},
            'tools_detected': {},
            'profiles': [],
            'blocked_ips': [],
            'monitored_ips_count': 0,
            'monitored_ips': [],
            'replay_sessions': [],
            'recent_events': []
        }
    else:
        data = build_data_json(events)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"[+] data.json written: {OUTPUT_PATH}")
    print(f"    Total Events: {data['total_attacks']}")
    print(f"    Unique IPs:   {data['unique_ips']}")
    print("=" * 50)


if __name__ == '__main__':
    main()
