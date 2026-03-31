"""
Module 15: Counter-Intelligence + Radioactive Token
Cyber Immune System — Antibody Layer

Silently extracts intelligence ABOUT the attacker:
  - SSH client version & OS fingerprint
  - Timezone estimation from activity patterns
  - Tool signatures (automated vs manual)
  - Unique "Attacker DNA" hash
"""
import hashlib
import time
import json
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')

class AttackerProfile:
    """Builds a comprehensive intelligence profile for each attacker session."""
    
    def __init__(self, ip, transport=None):
        self.ip = ip
        self.created_at = datetime.now().isoformat()
        self.ssh_client = "Unknown"
        self.os_fingerprint = "Unknown"
        self.geo_location = self._get_geolocation(ip)
        self.commands = []
        self.keystroke_timings = [] # For command intervals
        self.keystroke_times = []   # For keystroke dynamics (Innovation 1)
        self.last_command_time = time.time()
        self.tools_detected = set()
        self.threat_level = "LOW"
        self.classification = "Unknown"
        
        # Extract SSH banner from Paramiko transport
        if transport:
            try:
                remote_version = transport.remote_version or "Unknown"
                self.ssh_client = remote_version
                self.os_fingerprint = self._detect_os(remote_version)
            except:
                pass
    
    def _get_geolocation(self, ip):
        """Fetch real-world location data for the attacker IP."""
        if ip in ['127.0.0.1', 'localhost', '0.0.0.0'] or ip.startswith('192.168.') or ip.startswith('10.'):
            return {"country": "Local Network", "city": "Local", "isp": "Local"}
            
        try:
            import urllib.request
            import json
            # Using ip-api which is free and requires no API key for low-volume tracking
            url = f"http://ip-api.com/json/{ip}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data.get('status') == 'success':
                    return {
                        "country": data.get('country', 'Unknown'),
                        "city": data.get('city', 'Unknown'),
                        "isp": data.get('isp', 'Unknown'),
                        "lat": data.get('lat', 0.0),
                        "lon": data.get('lon', 0.0)
                    }
        except Exception as e:
            print(f"[WARN] Geolocation failed for {ip}: {e}")
            
        return {"country": "Unknown", "city": "Unknown", "isp": "Unknown"}
    
    def _detect_os(self, banner):
        """Fingerprint attacker's OS from their SSH client banner."""
        banner_lower = banner.lower()
        if 'windows' in banner_lower or 'putty' in banner_lower:
            return "Windows"
        elif 'ubuntu' in banner_lower or 'debian' in banner_lower:
            return "Linux (Debian/Ubuntu)"
        elif 'centos' in banner_lower or 'redhat' in banner_lower:
            return "Linux (RHEL/CentOS)"
        elif 'openssh' in banner_lower:
            return "Linux/Unix (OpenSSH)"
        elif 'libssh' in banner_lower:
            return "Automated Tool (libssh)"
        elif 'paramiko' in banner_lower:
            return "Python Script (Paramiko)"
        elif 'dropbear' in banner_lower:
            return "Embedded/IoT Device"
        else:
            return f"Unknown ({banner[:30]})"
    
    def record_command(self, command):
        """Record a command and analyze behavior."""
        now = time.time()
        interval = now - self.last_command_time
        self.last_command_time = now
        self.keystroke_timings.append(interval)
        self.commands.append(command)
        
        # Detect known hacking tools
        cmd_lower = command.lower()
        tool_signatures = {
            'nmap': 'Nmap Scanner',
            'hydra': 'Hydra Brute-Forcer',
            'sqlmap': 'SQLMap Injector',
            'metasploit': 'Metasploit Framework',
            'nikto': 'Nikto Web Scanner',
            'gobuster': 'GoBuster Dir Scanner',
            'john': 'John The Ripper',
            'hashcat': 'Hashcat Cracker',
            'masscan': 'Masscan Port Scanner',
            'wget': 'Payload Downloader',
            'curl': 'Payload Downloader',
            'chmod +x': 'Payload Executor',
            'rm -rf': 'Destructive Command',
            'base64': 'Obfuscation Attempt',
            'python -c': 'Script Injection',
            'perl -e': 'Script Injection',
            'nc ': 'Netcat Reverse Shell',
            'bash -i': 'Reverse Shell',
            '/dev/tcp': 'Reverse Shell',
        }
        
        for sig, tool_name in tool_signatures.items():
            if sig in cmd_lower:
                self.tools_detected.add(tool_name)
        
        # Update threat level
        self._update_threat_level()
    
    def _update_threat_level(self):
        """Dynamically classify threat severity."""
        danger_cmds = sum(1 for c in self.commands if any(d in c.lower() for d in 
            ['wget', 'curl', 'chmod', 'rm -rf', 'nc ', 'bash -i', '/dev/tcp', 'base64']))
        
        if danger_cmds >= 3 or len(self.tools_detected) >= 2:
            self.threat_level = "CRITICAL"
            self.classification = "Advanced Persistent Threat"
        elif danger_cmds >= 1 or len(self.commands) > 15:
            self.threat_level = "HIGH"
            self.classification = "Skilled Hacker"
        elif len(self.commands) > 5:
            self.threat_level = "MEDIUM"
            self.classification = "Script Kiddie"
        else:
            self.threat_level = "LOW"
            self.classification = "Reconnaissance"
    
    def get_attacker_dna(self):
        """Generate a unique behavioral fingerprint hash for this attacker."""
        dna_data = f"{self.ssh_client}|{self.os_fingerprint}|{','.join(self.commands[:20])}"
        avg_typing = sum(self.keystroke_timings) / len(self.keystroke_timings) if self.keystroke_timings else 0
        dna_data += f"|typing_speed:{avg_typing:.2f}"
        return hashlib.sha256(dna_data.encode()).hexdigest()[:16]
    
    def estimate_timezone(self):
        """Estimate attacker's timezone from activity patterns."""
        hour = datetime.now().hour
        if 0 <= hour < 6:
            return "Likely Asia/Pacific (active during Asian business hours)"
        elif 6 <= hour < 12:
            return "Likely Europe/Middle East"
        elif 12 <= hour < 18:
            return "Likely Americas (East)"
        else:
            return "Likely Americas (West)"
    
    def is_automated(self):
        """Detect if the attacker is a bot or human."""
        if len(self.keystroke_timings) < 3:
            return "Insufficient data"
        avg = sum(self.keystroke_timings) / len(self.keystroke_timings)
        if avg < 0.5:
            return "AUTOMATED BOT (avg delay: {:.2f}s)".format(avg)
        return "HUMAN OPERATOR (avg delay: {:.2f}s)".format(avg)
    
    def get_biometric_hash(self):
        """Innovation 1: Calculate Biometric Typing Profile (Keystroke Dynamics)"""
        if not hasattr(self, 'keystroke_times') or not self.keystroke_times:
            return "Insufficient Data"
            
        all_delays = []
        for cmd_times in self.keystroke_times:
            if len(cmd_times) > 1:
                # Calculate delays between consecutive keystrokes
                delays = [cmd_times[i] - cmd_times[i-1] for i in range(1, len(cmd_times))]
                all_delays.extend(delays)
                
        if len(all_delays) < 5:
            return "Insufficient Data (Need >5 keystrokes)"
            
        # Biometric features: Mean delay and Standard deviation of delays
        mean_delay = sum(all_delays) / len(all_delays)
        variance = sum((x - mean_delay) ** 2 for x in all_delays) / len(all_delays)
        std_dev = variance ** 0.5
        
        # Create a fuzzy hash: bucket the mean to nearest 20ms, std_dev to nearest 10ms
        fuzzy_mean = round(mean_delay * 50) / 50 
        fuzzy_std = round(std_dev * 100) / 100
        
        bio_string = f"IKD_M:{fuzzy_mean:.3f}_S:{fuzzy_std:.3f}"
        return hashlib.sha256(bio_string.encode()).hexdigest()[:12]
    
    def to_dict(self):
        """Export full profile as dictionary."""
        return {
            "ip": self.ip,
            "timestamp": self.created_at,
            "ssh_client": self.ssh_client,
            "os_fingerprint": self.os_fingerprint,
            "attacker_dna": self.get_attacker_dna(),
            "biometric_typing_hash": self.get_biometric_hash(),
            "timezone_estimate": self.estimate_timezone(),
            "is_automated": self.is_automated(),
            "threat_level": self.threat_level,
            "classification": self.classification,
            "tools_detected": list(self.tools_detected),
            "total_commands": len(self.commands),
            "commands": self.commands[-20:],  # Last 20 for privacy
        }
    
    def save_profile(self):
        """Save the attacker profile to a JSON log file."""
        os.makedirs(LOG_DIR, exist_ok=True)
        profile_path = os.path.join(LOG_DIR, 'attacker_profiles.json')
        try:
            with open(profile_path, 'a') as f:
                f.write(json.dumps(self.to_dict()) + '\n')
        except Exception as e:
            print(f"[WARN] Failed to save attacker profile: {e}")


# --- RADIOACTIVE TOKEN ---
RADIOACTIVE_TOKEN_CONTENT = """
========================================
  CONFIDENTIAL - INTERNAL USE ONLY
========================================
  System: production-server
  Last Updated: 2026-01-15

  --- Admin Portal (VPN BYPASS) ---
  URL: http://{host_ip}:8080/admin/login?token=sess_8f934jd023md
  User: superadmin
  Pass: P@ssw0rd2025!

  --- Service Credentials ---
  MySQL Root:     admin / Tr0ub4dor&3
  Redis:          default / s3cur3R3d1s!
  AWS Console:    devops@company.com / CloudP@ss2025
  Jenkins:        admin / j3nk1ns_m4st3r
  
  --- API Keys ---
  Stripe:         sk_live_placeholder_key_for_honeypot_1234
  SendGrid:       SG.xxxxxxxxxxxxxxxxxxxxx
  
  --- Recovery Codes ---
  Bitcoin Wallet: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
  
  For the full credential vault, visit:
  https://grabify.link/GMCZKR

========================================
  DO NOT SHARE THIS FILE
========================================
"""
