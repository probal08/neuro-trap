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


def batch_geoip_lookup(ips):
    """Batch GeoIP lookup using ip-api.com (free, no key, 45 req/min).
    Returns dict of ip -> {lat, lng, country, city, isp}"""
    import urllib.request
    results = {}
    # Filter out private/local IPs
    public_ips = [ip for ip in ips if ip and not ip.startswith(('127.', '10.', '192.168.', '172.', '0.', 'unknown'))]
    # ip-api.com supports batch of up to 100 IPs per request
    for i in range(0, min(len(public_ips), 100), 100):
        batch = public_ips[i:i+100]
        try:
            payload = json.dumps([{'query': ip, 'fields': 'query,status,country,city,lat,lon,isp'} for ip in batch])
            req = urllib.request.Request(
                'http://ip-api.com/batch',
                data=payload.encode(),
                headers={'Content-Type': 'application/json'}
            )
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read().decode())
            for entry in data:
                if entry.get('status') == 'success':
                    results[entry['query']] = {
                        'lat': entry.get('lat', 0),
                        'lng': entry.get('lon', 0),
                        'country': entry.get('country', 'Unknown'),
                        'city': entry.get('city', 'Unknown'),
                        'isp': entry.get('isp', 'Unknown')
                    }
            print(f"[+] GeoIP resolved {len(results)}/{len(public_ips)} IPs")
        except Exception as e:
            print(f"[!] GeoIP batch lookup failed: {e}")
    return results


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
    sessions = {}
    
    # Track tools specifically by IP for cross-filtering in the dashboard
    tools_by_ip = defaultdict(set)

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
                # Detect tools with word-boundary matching to avoid false positives
                # (This applies to commands typed in the shell)
                TOOL_PATTERNS = {
                    'nmap':       r'\bnmap\b',
                    'hydra':      r'\bhydra\b',
                    'metasploit': r'\bmetasploit\b|\bmsfconsole\b|\bmsfvenom\b',
                    'masscan':    r'\bmasscan\b',
                    'sqlmap':     r'\bsqlmap\b',
                    'curl':       r'\bcurl\b',
                    'wget':       r'\bwget\b',
                    'netcat':     r'\bnc\s+-|\bnc\s+\d|\bnetcat\b|\bncat\b',
                    'python':     r'\bpython[23]?\s+-c\b',
                    'base64':     r'\bbase64\b',
                    'chmod':      r'\bchmod\b.*\+x',
                    'bash_rev':   r'/dev/tcp|bash\s+-i|\bsh\s+-i',
                }
                for tool, pattern in TOOL_PATTERNS.items():
                    if re.search(pattern, cmd, re.IGNORECASE):
                        tools_detected[tool] += 1
                        tools_by_ip[ip].add(tool)

            # ENTERPRISE: Broadened Tool Detection (Connection Layer)
            # Detect protocol scanners (SSH clients, HTTP User-Agents)
            ssh_c = details.get('ssh_client', '')
            if ssh_c:
                ssh_client_counter[ssh_c] += 1
                ssh_c_lower = ssh_c.lower()
                if 'libssh' in ssh_c_lower: 
                    tools_detected['libssh (Brute-forcer)'] += 1
                    tools_by_ip[ip].add('libssh (Brute-forcer)')
                elif 'putty' in ssh_c_lower and 'scanner' in ssh_c_lower: 
                    tools_detected['putty-scanner'] += 1
                    tools_by_ip[ip].add('putty-scanner')
                elif 'go-http' in ssh_c_lower: 
                    tools_detected['Go-http-client'] += 1
                    tools_by_ip[ip].add('Go-http-client')

            ua = details.get('user_agent', '')
            if ua:
                ua_lower = ua.lower()
                if 'masscan' in ua_lower: 
                    tools_detected['Masscan (Scanner)'] += 1
                    tools_by_ip[ip].add('Masscan (Scanner)')
                elif 'zgrab' in ua_lower: 
                    tools_detected['ZGrab (Scanner)'] += 1
                    tools_by_ip[ip].add('ZGrab (Scanner)')
                elif 'sqlmap' in ua_lower: 
                    tools_detected['SQLMap'] += 1
                    tools_by_ip[ip].add('SQLMap')
                elif 'nmap' in ua_lower: 
                    tools_detected['Nmap Scripting Engine'] += 1
                    tools_by_ip[ip].add('Nmap Scripting Engine')
                elif 'nikto' in ua_lower: 
                    tools_detected['Nikto (Web Scanner)'] += 1
                    tools_by_ip[ip].add('Nikto (Web Scanner)')
                elif 'python-requests' in ua_lower: 
                    tools_detected['Python Scripts'] += 1
                    tools_by_ip[ip].add('Python Scripts')
                elif 'curl' in ua_lower: 
                    tools_detected['curl (Web Probe)'] += 1
                    tools_by_ip[ip].add('curl (Web Probe)')

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

    # GeoIP lookup for globe visualization
    unique_ips_list = list(ip_counter.keys())
    geo_data = batch_geoip_lookup(unique_ips_list[:100])  # Lookup top 100 IPs

    # Build globe points for 3D visualization
    globe_points = []
    for ip_addr, count in ip_counter.most_common(100):
        if ip_addr in geo_data:
            g = geo_data[ip_addr]
            globe_points.append({
                'lat': g['lat'],
                'lng': g['lng'],
                'country': g['country'],
                'city': g['city'],
                'ip': ip_addr,
                'count': count,
                'size': min(count / 3, 1.5)  # Scale for globe
            })
            country_counter[g['country']] += count

    # Top ISPs computation from GeoIP data
    isp_counter = Counter()
    for ip, count in ip_counter.items():
        if ip in geo_data and geo_data[ip].get('isp') and geo_data[ip]['isp'] != 'Unknown':
            isp_counter[geo_data[ip]['isp']] += count
    top_isps = [{'isp': isp, 'count': c} for isp, c in isp_counter.most_common(8)]

    # Top IPs
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

    # Attacker profiles — build from ALL events, enrich dynamically
    seen_ips = {}
    for e in events:
        ip = e.get('ip', 'unknown') or 'unknown'
        if ip in ('unknown', 'N/A', ''):
            continue
        details = e.get('details', {}) or {}
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except Exception:
                details = {}
        if not isinstance(details, dict):
            details = {}

        etype = e.get('event_type') or e.get('type', '')
        if ip not in seen_ips:
            seen_ips[ip] = {
                'ip': ip,
                'ssh_client': details.get('ssh_client', 'Unknown'),
                'os': details.get('os_fingerprint', 'Unknown'),
                'dna': hashlib.sha256(ip.encode()).hexdigest()[:12],
                'bio_hash': hashlib.md5(ip.encode()).hexdigest()[:8],
                'classification': details.get('attacker_class', 'Scanner'),
                'is_automated_raw': details.get('is_automated', None),
                'commands': 0,
                'logins': 0,
                'dangerous_cmds': 0,
            }
        if etype in ('COMMAND', 'command'):
            seen_ips[ip]['commands'] += 1
            cmd = details.get('command', '')
            DANGEROUS = ['wget', 'curl', '/dev/tcp', 'base64', 'chmod +x', 'rm -rf', 'bash -i', 'nc ', 'python -c', 'perl -e']
            if any(d in cmd.lower() for d in DANGEROUS):
                seen_ips[ip]['dangerous_cmds'] += 1
        if etype in ('AUTH_LOGIN', 'AUTH_SUCCESS'):
            seen_ips[ip]['logins'] += 1

    # Dynamic threat scoring from behaviour
    def compute_threat(p):
        score = 0
        score += min(p['commands'] * 2, 40)        # up to 40 pts for commands
        score += min(p['dangerous_cmds'] * 10, 40) # up to 40 pts for dangerous cmds
        score += min(p['logins'] * 1, 20)           # up to 20 pts for login attempts
        if score >= 60:   return 'CRITICAL'
        elif score >= 30: return 'HIGH'
        elif score >= 10: return 'MEDIUM'
        else:             return 'LOW'

    profiles = []
    for ip, p in list(seen_ips.items())[:20]:
        p['threat'] = compute_threat(p)
        auto = p.pop('is_automated_raw', None)
        p['automated'] = 'YES' if (auto or p['dangerous_cmds'] > 0 or p['commands'] > 5) else 'NO'
        p['tools'] = list(tools_by_ip.get(ip, set()))
        p['isp'] = geo_data.get(ip, {}).get('isp', 'Unknown')
        profiles.append(p)

    # Recompute threat_dist from dynamic profiles (accurate)
    threat_dist = Counter(p['threat'] for p in profiles)

    # Blocked IPs — those with high activity (proxy for blocked)
    blocked_ips = [
        {'ip': ip, 'attempts': count}
        for ip, count in ip_counter.most_common()
        if count >= 3
    ][:15]

    # Top passwords and creds
    top_creds = [{'cred': f"{u}:{p}", 'count': 1}
                 for u, p in zip(username_counter.keys(), password_counter.keys())][:8]

    # Timeline sorted
    attacks_over_time = [
        {'time': t, 'count': c}
        for t, c in sorted(timeline.items())[-24:]
    ]

    # ===== ENTERPRISE INTEL FEATURES =====

    # FEATURE: Reverse DNS Lookup — classify attacker infrastructure
    def reverse_dns_lookup(ip):
        """Classify attacker by PTR record."""
        try:
            import socket as _socket
            host = _socket.gethostbyaddr(ip)[0]
            if any(x in host.lower() for x in ['vpn', 'tor', 'proxy', 'exit']):
                return 'VPN/Proxy'
            elif any(x in host.lower() for x in ['amazon', 'aws', 'ec2', 'compute', 'cloud', 'azure', 'google', 'digital']):
                return 'Cloud Server'
            elif any(x in host.lower() for x in ['static', 'dynamic', 'dsl', 'cable', 'broadband', 'residential']):
                return 'Residential'
            else:
                return 'Hosting'
        except Exception:
            return 'Unknown'

    infra_types = Counter()
    for ip_addr in list(ip_counter.keys())[:30]:  # Top 30 only to stay fast
        infra_type = reverse_dns_lookup(ip_addr)
        infra_types[infra_type] += 1
    # Add infra_type to profiles
    for p in profiles:
        p['infra_type'] = reverse_dns_lookup(p['ip'])
    print(f"[+] Reverse DNS classified {len(infra_types)} infrastructure types")

    # FEATURE: Session Duration — how long each attacker stays
    ip_first_seen = {}
    ip_last_seen = {}
    for e in events:
        ip = e.get('ip', 'unknown') or 'unknown'
        ts = e.get('timestamp', '')
        if ts and ip != 'unknown':
            try:
                dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                if ip not in ip_first_seen or dt < ip_first_seen[ip]:
                    ip_first_seen[ip] = dt
                if ip not in ip_last_seen or dt > ip_last_seen[ip]:
                    ip_last_seen[ip] = dt
            except Exception:
                pass
    for p in profiles:
        ip = p['ip']
        if ip in ip_first_seen and ip in ip_last_seen:
            duration = (ip_last_seen[ip] - ip_first_seen[ip]).total_seconds()
            p['session_duration'] = int(duration)
        else:
            p['session_duration'] = 0
    avg_session = int(sum(p['session_duration'] for p in profiles) / max(len(profiles), 1))
    max_session = max((p['session_duration'] for p in profiles), default=0)

    # FEATURE: MITRE ATT&CK Kill Chain Mapping
    MITRE_MAP = {
        'Reconnaissance': ['whoami', 'id', 'uname', 'hostname', 'ifconfig', 'ip a', 'cat /etc/passwd', 'ls', 'pwd', 'ps', 'netstat', 'ss', 'w', 'last', 'env'],
        'Credential Access': ['cat /etc/shadow', 'password', 'credential', 'hash', 'passwd', '.ssh'],
        'Discovery': ['nmap', 'ping', 'traceroute', 'find', 'locate', 'grep'],
        'Lateral Movement': ['ssh ', 'scp', 'rsync', 'telnet'],
        'Exfiltration': ['wget', 'curl', 'nc ', 'base64', 'tar ', 'zip ', 'scp'],
        'Persistence': ['crontab', 'chmod', 'chown', '.bashrc', 'useradd', 'adduser'],
        'Execution': ['python', 'perl', 'bash', 'sh ', 'ruby', './'],
    }
    kill_chain_counts = Counter()
    for cmd, count in command_counter.items():
        for stage, keywords in MITRE_MAP.items():
            if any(kw in cmd.lower() for kw in keywords):
                kill_chain_counts[stage] += count
                break
    # Per-profile kill chain stage (highest stage reached)
    STAGE_ORDER = ['Reconnaissance', 'Credential Access', 'Discovery', 'Lateral Movement', 'Execution', 'Persistence', 'Exfiltration']
    for p in profiles:
        ip = p['ip']
        ip_cmds = [c['command'] for c in sessions.get(ip, [])]
        max_stage = 0
        for cmd in ip_cmds:
            for idx, stage in enumerate(STAGE_ORDER):
                if any(kw in cmd.lower() for kw in MITRE_MAP.get(stage, [])):
                    max_stage = max(max_stage, idx + 1)
        p['kill_chain_stage'] = max_stage
        p['kill_chain_label'] = STAGE_ORDER[max_stage - 1] if max_stage > 0 else 'None'

    # FEATURE: Paste Detection
    for p in profiles:
        ip = p['ip']
        ip_cmds = sessions.get(ip, [])
        if len(ip_cmds) >= 2:
            paste_count = 0
            for i in range(1, len(ip_cmds)):
                try:
                    t1 = datetime.fromisoformat(str(ip_cmds[i-1].get('time', '')).replace('Z', '+00:00'))
                    t2 = datetime.fromisoformat(str(ip_cmds[i].get('time', '')).replace('Z', '+00:00'))
                    if (t2 - t1).total_seconds() < 2:
                        paste_count += 1
                except Exception:
                    pass
            total = max(len(ip_cmds) - 1, 1)
            p['paste_ratio'] = round(paste_count / total * 100)
            p['input_method'] = 'Pasted Script' if p['paste_ratio'] > 60 else 'Manual Typing' if p['paste_ratio'] < 20 else 'Mixed'
        else:
            p['paste_ratio'] = 0
            p['input_method'] = 'Unknown'

    # FEATURE: Language/Origin Profiling
    CN_KEYWORDS = ['baidu', '微信', 'wget', 'base64', '/dev/tcp', 'crontab']
    RU_KEYWORDS = ['кошелек', 'yandex', 'passwd', 'shadow']
    for p in profiles:
        ip_cmds = ' '.join(c['command'] for c in sessions.get(p['ip'], []))
        if any(kw in ip_cmds.lower() for kw in CN_KEYWORDS):
            p['origin_hint'] = '🇨🇳 CN-Pattern'
        elif any(kw in ip_cmds.lower() for kw in RU_KEYWORDS):
            p['origin_hint'] = '🇷🇺 RU-Pattern'
        elif 'whoami' in ip_cmds and 'uname' in ip_cmds:
            p['origin_hint'] = '🏴‍☠️ Recon-Heavy'
        elif p['commands'] > 20:
            p['origin_hint'] = '🎯 Persistent'
        else:
            p['origin_hint'] = '🤖 Automated'

    # FEATURE: Top ISPs (from geo_data)
    isp_counter = Counter()
    for ip_addr in list(ip_counter.keys())[:100]:
        if ip_addr in geo_data and geo_data[ip_addr].get('isp'):
            isp_counter[geo_data[ip_addr]['isp']] += ip_counter[ip_addr]
    top_isps = [{'isp': isp, 'count': c} for isp, c in isp_counter.most_common(8)]

    # FEATURE: Timezone Inference (from activity hours)
    ip_hours = {}
    for e in events:
        ip = e.get('ip', 'unknown')
        ts = e.get('timestamp', '')
        if ts and ip != 'unknown':
            try:
                dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                if ip not in ip_hours:
                    ip_hours[ip] = []
                ip_hours[ip].append(dt.hour)
            except Exception:
                pass
    for p in profiles:
        hours = ip_hours.get(p['ip'], [])
        if hours:
            avg_hour = sum(hours) / len(hours)
            # Guess timezone offset: if avg activity hour is around 4 UTC, they're probably UTC+8 (working at noon)
            tz_guess = int((12 - avg_hour) % 24 - 12)
            p['tz_guess'] = f"UTC{'+' if tz_guess >= 0 else ''}{tz_guess}"
        else:
            p['tz_guess'] = 'Unknown'

    print(f"[+] Enterprise intel: {len(profiles)} profiles enriched with kill chain, paste detection, origin profiling")

    data = {
        'last_updated': datetime.now(IST).isoformat(),
        'total_attacks': len(events),
        'unique_ips': len(ip_counter),
        'top_user': username_counter.most_common(1)[0][0] if username_counter else '—',
        'top_pass': password_counter.most_common(1)[0][0] if password_counter else '—',
        'event_distribution': dict(event_type_counter.most_common(8)),
        'top_countries': [{'country': c, 'count': n} for c, n in country_counter.most_common(10)] or [{'country': 'Scanning...', 'count': 0}],
        'globe_points': globe_points,
        'attacks_over_time': attacks_over_time,
        'top_ips': top_ips,
        'top_creds': top_creds,
        'top_passwords': [{'password': p, 'count': c} for p, c in password_counter.most_common(15)],
        'threat_distribution': dict(threat_dist),
        'tools_detected': dict(tools_detected.most_common(10)),
        'profiles': profiles,
        'blocked_ips': blocked_ips,
        'monitored_ips_count': len(ip_counter),
        'monitored_ips': blocked_ips,
        'replay_sessions': replay_sessions,
        'recent_events': recent_events,
        # Enterprise intel
        'top_isps': top_isps,
        'infra_types': dict(infra_types),
        'kill_chain': kill_chain_counts,
        'avg_session_duration': avg_session,
        'max_session_duration': max_session,
    }

    return data


def main():
    print("=" * 50)
    print("  NEURO-TRAP PUBLIC FEED GENERATOR")
    print("=" * 50)

    # Load local .env file manually if running locally
    env_path = os.path.join(_PROJECT_ROOT, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()
        print("[+] Loaded environment variables from .env")

    # Get MongoDB URI from environment
    mongo_uri = os.environ.get('MONGODB_URI', '')
    if mongo_uri:
        print("[+] MongoDB URI found in environment")

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
            'recent_events': [],
            'globe_points': []
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
