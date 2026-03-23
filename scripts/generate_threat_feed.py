"""
Neuro-Trap Threat Feed Generator
Phase 4: Automated CI/CD Intelligence Pipeline

Parses honeypot.json logs and generates:
  - threat_feed/blocklist.txt  (Firewall-ready IP blocklist)
  - threat_feed/report.json    (Structured threat intelligence)
"""
import json
import os
import sys
import uuid
from datetime import datetime
from collections import Counter

# Paths - absolute, based on script location
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.join(_SCRIPT_DIR, '..')
LOG_FILE = os.path.join(_PROJECT_ROOT, 'logs', 'honeypot.json')
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, 'threat_feed')

def parse_logs():
    """Read events from MongoDB or fallback to honeypot.json."""
    events = []
    
    # Phase 1: Try MongoDB first
    try:
        import sys
        _server_dir = os.path.join(_PROJECT_ROOT, 'server')
        if _server_dir not in sys.path:
            sys.path.insert(0, _server_dir)
        import mongo_client
        
        events_col = mongo_client.get_events_col()
        if events_col is not None:
            # Query all events, exclude ObjectId
            mongo_data = list(events_col.find({}, {"_id": 0}))
            if mongo_data:
                print(f"[+] Retrieved {len(mongo_data)} events from MongoDB Atlas", flush=True)
                return mongo_data
    except Exception as e:
        print(f"[!] MongoDB read failed: {e}. Falling back to local logs.", flush=True)

    abs_log = os.path.abspath(LOG_FILE)
    if not os.path.exists(abs_log):
        print(f"[!] Log file not found: {abs_log}", flush=True)
        return events
    
    with open(abs_log, 'r') as f:
        for line in f:
            try:
                events.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    return events

def generate_blocklist(events):
    """Extract unique attacker IPs into a firewall-ready blocklist."""
    ips = set()
    for e in events:
        ip = e.get('ip')
        if ip and ip != 'N/A' and ip is not None:
            ips.add(ip)
    return sorted(ips)

def generate_report(events):
    """Build a structured threat intelligence report."""
    ip_counter = Counter()
    password_counter = Counter()
    command_counter = Counter()
    usernames = Counter()
    
    for e in events:
        ip = e.get('ip', 'unknown')
        if ip:
            ip_counter[ip] += 1
        
        details = e.get('details', {})
        if isinstance(details, dict):
            if 'password' in details:
                password_counter[details['password']] += 1
            if 'username' in details:
                usernames[details['username']] += 1
            if 'command' in details:
                command_counter[details['command']] += 1
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_events": len(events),
        "unique_ips": len(ip_counter),
        "top_10_attackers": dict(ip_counter.most_common(10)),
        "top_10_passwords": dict(password_counter.most_common(10)),
        "top_10_usernames": dict(usernames.most_common(10)),
        "top_10_commands": dict(command_counter.most_common(10)),
        "threat_summary": {
            "auth_attempts": sum(1 for e in events if e.get('event_type') == 'AUTH_LOGIN'),
            "commands_executed": sum(1 for e in events if e.get('event_type') == 'COMMAND'),
            "sessions": sum(1 for e in events if e.get('event_type') == 'CONNECTION'),
        }
    }
    return report

def generate_stix_feed(blocklist):
    """Module 25: Generate STIX 2.1 compliant Threat Intelligence Feed."""
    stix_bundle = {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid4()}",
        "objects": []
    }
    
    now = datetime.utcnow().isoformat() + "Z"
    
    for ip in blocklist:
        indicator = {
            "type": "indicator",
            "spec_version": "2.1",
            "id": f"indicator--{uuid.uuid4()}",
            "created": now,
            "modified": now,
            "name": f"Malicious SSH Brute-forcer / Scanner ({ip})",
            "description": "IP detected performing unauthorized activities on Neuro-Trap honeypot.",
            "pattern": f"[ipv4-addr:value = '{ip}']",
            "pattern_type": "stix",
            "valid_from": now
        }
        stix_bundle["objects"].append(indicator)
        
    return stix_bundle

def main():
    print("=" * 50, flush=True)
    print("  NEURO-TRAP THREAT FEED GENERATOR", flush=True)
    print("=" * 50, flush=True)
    
    # Parse logs
    events = parse_logs()
    if not events:
        print("[!] No events found. Run the honeypot first to generate logs.", flush=True)
        return
    
    print(f"[+] Parsed {len(events)} events from honeypot.json", flush=True)
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate blocklist
    blocklist = generate_blocklist(events)
    blocklist_path = os.path.join(OUTPUT_DIR, 'blocklist.txt')
    with open(blocklist_path, 'w') as f:
        f.write(f"# Neuro-Trap IP Blocklist\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write(f"# Total IPs: {len(blocklist)}\n\n")
        for ip in blocklist:
            f.write(ip + '\n')
    print(f"[+] Blocklist written: {blocklist_path} ({len(blocklist)} IPs)", flush=True)
    
    # Generate report
    report = generate_report(events)
    report_path = os.path.join(OUTPUT_DIR, 'report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"[+] Report written: {report_path}", flush=True)

    # Generate STIX 2.1 Feed (Module 25)
    stix_feed = generate_stix_feed(blocklist)
    stix_path = os.path.join(OUTPUT_DIR, 'stix_feed.json')
    with open(stix_path, 'w') as f:
        json.dump(stix_feed, f, indent=2)
    print(f"[+] STIX 2.1 Feed written: {stix_path}", flush=True)
    
    # Summary
    print(f"\n--- THREAT INTELLIGENCE SUMMARY ---", flush=True)
    print(f"  Total Events:     {report['total_events']}", flush=True)
    print(f"  Unique Attackers: {report['unique_ips']}", flush=True)
    print(f"  Auth Attempts:    {report['threat_summary']['auth_attempts']}", flush=True)
    print(f"  Commands Exec'd:  {report['threat_summary']['commands_executed']}", flush=True)
    top_pass = list(report['top_10_passwords'].keys())[0] if report['top_10_passwords'] else 'N/A'
    print(f"  Top Password:     {top_pass}", flush=True)
    print("=" * 50, flush=True)

if __name__ == '__main__':
    main()
