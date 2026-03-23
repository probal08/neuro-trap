"""
Module 18: Auto-Firewall + Telegram Alerts
Cyber Immune System — Fever Response

Auto-blocks attackers after repeated attempts and
sends real-time notifications via Telegram.
"""
import json
import os
from datetime import datetime
from collections import Counter

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs', 'honeypot.json')
RULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'threat_feed')

# --- CONFIGURATION ---
# IPs that should NEVER be blocked (Localhost + Admin IP)
WHITELIST_IPS = ['127.0.0.1', '::1', 'localhost']


# --- AUTO-FIREWALL ---

def analyze_threats(threshold=3):
    """
    Scan honeypot logs and identify IPs that exceed the login attempt threshold.
    Returns dict of {ip: attempt_count} for IPs above threshold.
    """
    ip_attempts = Counter()
    
    if not os.path.exists(LOG_FILE):
        return {}
    
    with open(LOG_FILE, 'r') as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                if event.get('event_type') == 'AUTH_LOGIN':
                    ip = event.get('ip')
                    if ip and ip not in WHITELIST_IPS:
                        ip_attempts[ip] += 1
            except json.JSONDecodeError:
                continue
    
    return {ip: count for ip, count in ip_attempts.items() if count >= threshold}


def generate_firewall_rules(threshold=3):
    """
    Generate firewall block rules for repeat attackers.
    Creates both Windows (.bat) and Linux (.sh) scripts.
    """
    threats = analyze_threats(threshold)
    
    if not threats:
        print("[*] No IPs exceed the threshold. No rules generated.")
        return
    
    os.makedirs(RULES_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # --- Windows Firewall Rules ---
    bat_path = os.path.join(RULES_DIR, 'firewall_rules.bat')
    with open(bat_path, 'w') as f:
        f.write(f"@echo off\n")
        f.write(f"REM Neuro-Trap Auto-Firewall Rules\n")
        f.write(f"REM Generated: {timestamp}\n")
        f.write(f"REM Threshold: {threshold} login attempts\n\n")
        for ip, count in sorted(threats.items(), key=lambda x: x[1], reverse=True):
            if ip in WHITELIST_IPS: continue
            f.write(f'REM Blocked: {ip} ({count} attempts)\n')
            f.write(f'netsh advfirewall firewall add rule name="NEURO-TRAP Block {ip}" dir=in action=block remoteip={ip}\n\n')
    
    # --- Linux iptables Rules ---
    sh_path = os.path.join(RULES_DIR, 'firewall_rules.sh')
    with open(sh_path, 'w') as f:
        f.write(f"#!/bin/bash\n")
        f.write(f"# Neuro-Trap Auto-Firewall Rules\n")
        f.write(f"# Generated: {timestamp}\n")
        f.write(f"# Threshold: {threshold} login attempts\n\n")
        for ip, count in sorted(threats.items(), key=lambda x: x[1], reverse=True):
            if ip in WHITELIST_IPS: continue
            f.write(f'# Blocked: {ip} ({count} attempts)\n')
            f.write(f'iptables -A INPUT -s {ip} -j DROP\n\n')
    
    print(f"[+] Firewall rules generated:")
    print(f"    Windows: {bat_path}")
    print(f"    Linux:   {sh_path}")
    print(f"    Blocked IPs: {len(threats)}")
    
    for ip, count in sorted(threats.items(), key=lambda x: x[1], reverse=True):
        print(f"    🔴 {ip} — {count} attempts")
    
    return threats


# --- TELEGRAM ALERTS ---

# Load Telegram config from JSON file or environment variables
def _load_telegram_config():
    """Load Telegram bot credentials from config file or env vars."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'telegram_config.json')
    token = ''
    chat_id = ''
    
    # Priority 1: Config file
    if os.path.exists(config_path):
        try:
            import json as _json
            with open(config_path, 'r') as f:
                config = _json.load(f)
            token = config.get('token', '').strip()
            chat_id = config.get('chat_id', '').strip()
        except Exception:
            pass
    
    # Priority 2: Environment variables (fallback)
    if not token:
        token = os.environ.get('NEUROTRAP_TELEGRAM_TOKEN', '')
    if not chat_id:
        chat_id = os.environ.get('NEUROTRAP_TELEGRAM_CHAT', '')
    
    return token, chat_id

TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = _load_telegram_config()
_TELEGRAM_CONFIGURED = bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)

# Print visible warning on import
if not _TELEGRAM_CONFIGURED:
    print("\033[93m[⚠ TELEGRAM] Not configured. Edit server/telegram_config.json to enable real-time alerts.\033[0m")
else:
    print("\033[92m[✓ TELEGRAM] Bot configured. Real-time alerts active.\033[0m")

def send_telegram_alert(message):
    """Send a real-time alert to Telegram (if configured)."""
    if not _TELEGRAM_CONFIGURED:
        return  # Skip — warning already shown on startup
    
    try:
        import urllib.request
        import urllib.parse
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': TELEGRAM_CHAT_ID,
            'text': f"🛡️ NEURO-TRAP ALERT\n\n{message}",
            'parse_mode': 'HTML'
        }).encode()
        
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"\033[93m[⚠ TELEGRAM] Alert failed: {e}\033[0m")


def alert_connection(ip, ssh_client="Unknown"):
    """Alert on new SSH connection."""
    send_telegram_alert(f"🔴 <b>New Connection</b>\nIP: <code>{ip}</code>\nSSH Client: {ssh_client}")

def alert_login(ip, username, password):
    """Alert on login attempt."""
    send_telegram_alert(f"🟡 <b>Credentials Captured</b>\nIP: <code>{ip}</code>\nUser: <code>{username}</code>\nPass: <code>{password}</code>")

def alert_danger(ip, command):
    """Alert on dangerous command."""
    send_telegram_alert(f"🔵 <b>Dangerous Command</b>\nIP: <code>{ip}</code>\nCmd: <code>{command}</code>")

def alert_threat(ip, threat_level, classification):
    """Alert on threat level escalation."""
    send_telegram_alert(f"⚠️ <b>Threat Escalation</b>\nIP: <code>{ip}</code>\nLevel: <b>{threat_level}</b>\nType: {classification}")


# CLI entry point
if __name__ == '__main__':
    print("=" * 50)
    print("  NEURO-TRAP AUTO-FIREWALL")
    print("=" * 50)
    generate_firewall_rules(threshold=3)
