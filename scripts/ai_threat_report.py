"""
Module 19: AI Incident Report Generator
Cyber Immune System — Immune Memory Layer

Feeds honeypot logs + attacker profiles into Llama 3.2 to
auto-generate professional cybersecurity incident reports.
"""
import json
import os
from datetime import datetime
from collections import Counter
import sentry_sdk

def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# Optional telemetry: configured only through environment variables.
_SENTRY_DSN = os.environ.get("NEUROTRAP_SENTRY_DSN", "").strip()
if _SENTRY_DSN:
    sentry_sdk.init(
        dsn=_SENTRY_DSN,
        traces_sample_rate=_env_float("NEUROTRAP_SENTRY_TRACES_SAMPLE_RATE", 0.2),
        profiles_sample_rate=_env_float("NEUROTRAP_SENTRY_PROFILES_SAMPLE_RATE", 0.2),
    )

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs', 'honeypot.json')
PROFILES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs', 'attacker_profiles.json')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'threat_feed')

def load_logs():
    events = []
    
    # Phase 1: Try MongoDB first
    try:
        import sys
        _server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'server'))
        if _server_dir not in sys.path:
            sys.path.insert(0, _server_dir)
        import mongo_client
        
        events_col = mongo_client.get_events_col()
        if events_col is not None:
            mongo_data = list(events_col.find({}, {"_id": 0}))
            if mongo_data:
                return mongo_data
    except Exception:
        pass

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            for line in f:
                try:
                    events.append(json.loads(line.strip()))
                except:
                    continue
    return events

def load_profiles():
    profiles = []
    
    # Phase 1: Try MongoDB first
    try:
        import sys
        _server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'server'))
        if _server_dir not in sys.path:
            sys.path.insert(0, _server_dir)
        import mongo_client
        
        profiles_col = mongo_client.get_profiles_col()
        if profiles_col is not None:
            mongo_data = list(profiles_col.find({}, {"_id": 0}))
            if mongo_data:
                return mongo_data
    except Exception:
        pass

    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, 'r') as f:
            for line in f:
                try:
                    profiles.append(json.loads(line.strip()))
                except:
                    continue
    return profiles

def generate_report_with_ai(events, profiles):
    """Use AI (Groq Cloud → Ollama → Fallback) to generate a professional incident report."""
    try:
        # Add project root to path for ai_provider import
        import sys
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        _server_dir = os.path.join(_script_dir, '..', 'server')
        if _server_dir not in sys.path:
            sys.path.insert(0, _server_dir)
        import ai_provider  # Hybrid: Groq Cloud → Ollama → Fallback
        
        # Build a summary of the data for the AI
        ip_counter = Counter(e.get('ip','?') for e in events if e.get('ip'))
        password_counter = Counter()
        command_counter = Counter()
        
        for e in events:
            d = e.get('details', {})
            if isinstance(d, dict):
                if 'password' in d:
                    password_counter[d['password']] += 1
                if 'command' in d:
                    command_counter[d['command']] += 1
        
        data_summary = f"""
HONEYPOT DATA SUMMARY:
- Total events: {len(events)}
- Unique IPs: {len(ip_counter)}
- Top 5 attacking IPs: {dict(ip_counter.most_common(5))}
- Total auth attempts: {sum(1 for e in events if e.get('event_type')=='AUTH_LOGIN')}
- Top 5 passwords tried: {dict(password_counter.most_common(5))}
- Top 10 commands executed: {dict(command_counter.most_common(10))}
- Total sessions: {sum(1 for e in events if e.get('event_type')=='CONNECTION')}
- Date range: {events[0].get('timestamp','?')} to {events[-1].get('timestamp','?')}
"""
        
        if profiles:
            data_summary += f"\nATTACKER PROFILES:\n"
            for p in profiles[:5]:
                data_summary += f"- IP: {p.get('ip')} | OS: {p.get('os_fingerprint')} | Threat: {p.get('threat_level')} | Class: {p.get('classification')} | Tools: {p.get('tools_detected')}\n"
        
        prompt = f"""You are a senior cybersecurity analyst writing an official Incident Report.
Based on the following honeypot data, write a professional, detailed incident report in Markdown format.

Include these sections:
1. Executive Summary (2-3 sentences overview)
2. Attack Timeline (key events with timestamps)  
3. Attacker Profiles (based on behavioral analysis)
4. Techniques, Tactics, and Procedures (TTPs) observed
5. Risk Assessment (severity rating: LOW/MEDIUM/HIGH/CRITICAL)
6. Recommendations (specific defensive actions)

{data_summary}

Write the report now. Be professional, specific, and cite actual data from above."""

        result = ai_provider.generate(
            'You are a cybersecurity incident response analyst. Write formal, professional reports.',
            prompt
        )
        
        if result is None:
            return generate_report_fallback(events, profiles, "All AI providers unavailable")
        
        return result
    
    except Exception as e:
        return generate_report_fallback(events, profiles, str(e))


def generate_report_fallback(events, profiles, error=""):
    """Generate a structured report without AI if Ollama is unavailable."""
    ip_counter = Counter(e.get('ip','?') for e in events if e.get('ip'))
    password_counter = Counter()
    command_counter = Counter()
    
    for e in events:
        d = e.get('details', {})
        if isinstance(d, dict):
            if 'password' in d: password_counter[d['password']] += 1
            if 'command' in d: command_counter[d['command']] += 1
    
    auth_count = sum(1 for e in events if e.get('event_type') == 'AUTH_LOGIN')
    cmd_count = sum(1 for e in events if e.get('event_type') == 'COMMAND')
    sessions = sum(1 for e in events if e.get('event_type') == 'CONNECTION')
    
    report = f"""# NEURO-TRAP INCIDENT REPORT
## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 1. Executive Summary

The Neuro-Trap honeypot detected **{sessions} intrusion sessions** from **{len(ip_counter)} unique IP addresses** during the monitoring period. A total of **{auth_count} authentication attempts** were logged using **{len(password_counter)} unique passwords**. Attackers executed **{cmd_count} commands** during their sessions.

## 2. Attack Statistics

| Metric | Value |
|--------|-------|
| Total Events | {len(events)} |
| Unique Attackers | {len(ip_counter)} |
| Auth Attempts | {auth_count} |
| Commands Executed | {cmd_count} |
| Sessions | {sessions} |

## 3. Top Attacking IPs

| IP Address | Attempts |
|-----------|----------|
"""
    for ip, count in ip_counter.most_common(10):
        report += f"| {ip} | {count} |\n"
    
    report += f"\n## 4. Top Passwords Attempted\n\n| Password | Attempts |\n|----------|----------|\n"
    for pwd, count in password_counter.most_common(10):
        report += f"| `{pwd}` | {count} |\n"
    
    report += f"\n## 5. Top Commands Executed\n\n| Command | Count |\n|---------|-------|\n"
    for cmd, count in command_counter.most_common(10):
        report += f"| `{cmd}` | {count} |\n"
    
    if profiles:
        report += f"\n## 6. Attacker Profiles\n\n| IP | OS | Threat Level | Classification | Tools |\n|----|----|-------------|---------------|-------|\n"
        for p in profiles:
            tools = ', '.join(p.get('tools_detected', [])) or 'None'
            report += f"| {p.get('ip','-')} | {p.get('os_fingerprint','-')} | {p.get('threat_level','-')} | {p.get('classification','-')} | {tools} |\n"
    
    report += f"""
## 7. Recommendations

1. **Block** all identified attacking IPs at the network firewall level
2. **Enforce** multi-factor authentication on all SSH services
3. **Deploy** Neuro-Trap honeypots on additional network segments
4. **Monitor** for the specific tool signatures detected in attacker sessions
5. **Update** password policies — `{password_counter.most_common(1)[0][0] if password_counter else 'N/A'}` was the most attempted password

---
*Report generated by Neuro-Trap Cyber Immune System v2*
"""
    if error:
        report += f"\n> Note: AI-enhanced report unavailable ({error}). Using structured template.\n"
    
    return report


def main():
    print("=" * 50, flush=True)
    print("  NEURO-TRAP AI INCIDENT REPORT", flush=True)
    print("=" * 50, flush=True)
    
    events = load_logs()
    profiles = load_profiles()
    
    if not events:
        print("[!] No log data found. Run the honeypot first.", flush=True)
        return
    
    print(f"[+] Loaded {len(events)} events and {len(profiles)} profiles", flush=True)
    print("[*] Generating report (this may take a moment)...", flush=True)
    
    report = generate_report_with_ai(events, profiles)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(OUTPUT_DIR, 'incident_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"[+] Report saved to: {report_path}", flush=True)
    print("=" * 50, flush=True)

if __name__ == '__main__':
    main()
