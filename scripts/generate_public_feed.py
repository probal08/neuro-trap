"""
Neuro-Trap — Advanced Public Threat Intel Feed Generator
Extracts ALL data from MongoDB for the public cyberpunk dashboard.
Runs hourly via GitHub Actions.
"""
import os
import json
import hashlib
from collections import Counter, defaultdict
from datetime import datetime
from pymongo import MongoClient


def generate_feed():
    uri = os.environ.get('MONGODB_URI')
    if not uri:
        print("WARNING: MONGODB_URI not set. Generating sample data.")
        data = _sample_data()
    else:
        data = _fetch_from_mongo(uri)
        if data is None:
            return

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public_web')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'data.json')
    with open(out_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Generated {out_file} — {data['total_attacks']} attacks tracked.")


def _fetch_from_mongo(uri):
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        db = client['neurotrap']
        events_coll = db['events']
        profiles_coll = db['attacker_profiles']

        events = list(events_coll.find({}, {"_id": 0}).sort('timestamp', -1).limit(5000))
        total_attacks = events_coll.count_documents({})
        profiles = list(profiles_coll.find({}, {"_id": 0}).limit(500))

        # --- Metrics ---
        auth_events = [e for e in events if e.get('event_type') == 'AUTH_LOGIN']
        command_events = [e for e in events if e.get('event_type') == 'COMMAND']
        unique_ips = len(set(e.get('ip') or e.get('attacker_ip', '') for e in events))

        usernames = []
        passwords = []
        for e in auth_events:
            d = e.get('details', {})
            if isinstance(d, dict):
                if d.get('username'): usernames.append(d['username'])
                if d.get('password'): passwords.append(d['password'])
        top_user = Counter(usernames).most_common(1)[0][0] if usernames else "N/A"
        top_pass = Counter(passwords).most_common(1)[0][0] if passwords else "N/A"

        # --- Top IPs ---
        ips = [e.get('ip') or e.get('attacker_ip', '') for e in events if (e.get('ip') or e.get('attacker_ip'))]
        top_ips = [{'ip': ip, 'count': c} for ip, c in Counter(ips).most_common(10)]

        # --- Top Credentials ---
        cred_list = []
        for e in auth_events:
            d = e.get('details', {})
            if isinstance(d, dict):
                cred_list.append(f"{d.get('username','?')}:{d.get('password','?')}")
        top_creds = [{'cred': cr, 'count': c} for cr, c in Counter(cred_list).most_common(10)]

        # --- Attack Timeline (hourly buckets) ---
        timeseries = defaultdict(int)
        for e in events:
            ts = e.get('timestamp')
            if ts:
                try:
                    if isinstance(ts, str):
                        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    else:
                        dt = ts
                    timeseries[dt.strftime("%Y-%m-%d %H:00")] += 1
                except:
                    pass
        sorted_times = sorted(timeseries.keys())[-24:]
        attacks_over_time = [{'time': t, 'count': timeseries[t]} for t in sorted_times]

        # --- Event Type Distribution ---
        event_types = [e.get('event_type', 'UNKNOWN') for e in events]
        event_distribution = {k: v for k, v in Counter(event_types).most_common(10)}

        # --- Threat Levels (from profiles) ---
        threats = [p.get('threat_level', 'LOW') for p in profiles]
        threat_distribution = dict(Counter(threats))

        # --- Countries (from profiles geo_location) ---
        countries = []
        for p in profiles:
            geo = p.get('geo_location', {})
            if isinstance(geo, dict):
                c = geo.get('country', 'Unknown')
                if c not in ('Unknown', 'Local Network'):
                    countries.append(c)
        top_countries = [{'country': c, 'count': n} for c, n in Counter(countries).most_common(8)]

        # --- Attacker Profiles Table ---
        profile_table = []
        for p in profiles:
            profile_table.append({
                'ip': p.get('ip', '?'),
                'ssh_client': (p.get('ssh_client', '?') or '?')[:40],
                'os': p.get('os_fingerprint', '?'),
                'dna': (p.get('attacker_dna', '') or '')[:12],
                'bio_hash': p.get('biometric_typing_hash', '—'),
                'threat': p.get('threat_level', '?'),
                'classification': p.get('classification', '?'),
                'automated': p.get('is_automated', '?'),
                'commands': p.get('total_commands', 0),
                'tools': p.get('tools_detected', []),
            })

        # --- Detected Hacking Tools ---
        all_tools = []
        for p in profiles:
            all_tools.extend(p.get('tools_detected', []))
        tools_count = {k: v for k, v in Counter(all_tools).most_common(10)}

        # --- Blocked IPs (Firewall — 3+ auth attempts) ---
        ip_auth_counts = Counter(e.get('ip') or e.get('attacker_ip', '') for e in auth_events)
        blocked_ips = [{'ip': ip, 'attempts': c} for ip, c in ip_auth_counts.items() if c >= 3]
        monitored_ips = [{'ip': ip, 'attempts': c} for ip, c in ip_auth_counts.items() if c < 3]

        # --- Top Passwords Pie ---
        top_passwords = [{'password': p, 'count': c} for p, c in Counter(passwords).most_common(8)]

        # --- Attack Replay (last session per IP) ---
        replays = {}
        for e in sorted(command_events, key=lambda x: x.get('timestamp', '')):
            ip = e.get('ip') or e.get('attacker_ip', 'unknown')
            d = e.get('details', {})
            cmd = d.get('command', e.get('message', '?')) if isinstance(d, dict) else str(d)
            ts = e.get('timestamp', '')
            if isinstance(ts, datetime):
                ts = ts.isoformat()
            if ip not in replays:
                replays[ip] = []
            replays[ip].append({'time': ts, 'command': cmd})

        # Keep last 5 sessions, trim to 30 commands each
        replay_sessions = []
        for ip, cmds in list(replays.items())[-5:]:
            replay_sessions.append({'ip': ip, 'commands': cmds[-30:]})

        # --- Recent Events ---
        recent_events = []
        for e in events[:25]:
            d = e.get('details', {})
            detail_str = ''
            if isinstance(d, dict):
                detail_str = d.get('command', '') or d.get('username', '') or json.dumps(d)[:60]
            else:
                detail_str = str(d)[:60]

            ts = e.get('timestamp', '')
            if isinstance(ts, datetime):
                ts = ts.isoformat()

            recent_events.append({
                'timestamp': ts,
                'ip': e.get('ip') or e.get('attacker_ip', 'Unknown'),
                'type': e.get('event_type', 'unknown'),
                'message': e.get('message', ''),
                'details': detail_str
            })

        return {
            'last_updated': datetime.utcnow().isoformat() + "Z",
            'total_attacks': total_attacks,
            'unique_ips': unique_ips,
            'top_user': top_user,
            'top_pass': top_pass,
            'top_ips': top_ips,
            'top_creds': top_creds,
            'top_passwords': top_passwords,
            'attacks_over_time': attacks_over_time,
            'event_distribution': event_distribution,
            'threat_distribution': threat_distribution,
            'top_countries': top_countries,
            'profiles': profile_table,
            'tools_detected': tools_count,
            'blocked_ips': blocked_ips,
            'monitored_ips_count': len(monitored_ips),
            'monitored_ips': monitored_ips,
            'replay_sessions': replay_sessions,
            'recent_events': recent_events,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        return None


def _sample_data():
    return {
        'last_updated': datetime.utcnow().isoformat() + "Z",
        'total_attacks': 43,
        'unique_ips': 5,
        'top_user': 'root',
        'top_pass': 'admin',
        'top_ips': [{'ip': '127.0.0.1', 'count': 43}],
        'top_creds': [{'cred': 'root:admin', 'count': 10}],
        'top_passwords': [{'password': 'admin', 'count': 10}],
        'attacks_over_time': [],
        'event_distribution': {'AUTH_LOGIN': 20, 'COMMAND': 23},
        'threat_distribution': {'LOW': 3, 'MEDIUM': 1, 'HIGH': 1},
        'top_countries': [],
        'profiles': [],
        'tools_detected': {},
        'blocked_ips': [],
        'monitored_ips_count': 0,
        'monitored_ips': [],
        'replay_sessions': [],
        'recent_events': [],
    }


if __name__ == '__main__':
    generate_feed()
