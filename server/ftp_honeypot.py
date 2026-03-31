"""
Neuro-Trap FTP Honeypot — Port 2121
Enterprise Module: Captures brute-force login attempts and file exfiltration scans.

Mimics a standard FTP server. Accepts any credentials.
"""
import os
import sys
import json
from datetime import datetime, timezone, timedelta
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

IST = timezone(timedelta(hours=5, minutes=30))

# Add parent for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from server import logger, firewall
except ImportError:
    logger = None
    firewall = None

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'ftp_honeypot.json')
FTP_ROOT = os.path.join(os.path.dirname(__file__), '..', 'server', 'ftp_root')

def log_ftp_event(ip, event_type, message, details=None):
    """Log FTP event to file and MongoDB."""
    event = {
        'timestamp': datetime.now(IST).isoformat(),
        'ip': ip,
        'event_type': event_type,
        'message': message,
        'details': details or {}
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(event) + '\n')
    
    if logger:
        logger.log_event('WARNING', event_type, message, ip=ip, details=details or {})

class HoneypotFTPHandler(FTPHandler):
    """Custom FTP handler to log all activities."""
    
    def on_connect(self):
        ip = self.remote_ip
        log_ftp_event(ip, 'FTP_CONNECTION', f"New FTP connection from {ip}")
        print(f"\033[93m[FTP] Connection from {ip}\033[0m")
    
    def on_login(self, username):
        ip = self.remote_ip
        log_ftp_event(ip, 'FTP_LOGIN', f"FTP login successful: {username}", {'username': username})
        print(f"\033[92m[FTP] {ip} logged in as {username}\033[0m")
    
    def on_login_failed(self, username, password):
        ip = self.remote_ip
        log_ftp_event(ip, 'FTP_LOGIN_FAILED', f"FTP login failed: {username}:{password}", {'username': username, 'password': password})
        print(f"\033[91m[FTP] {ip} login failed: {username}:{password}\033[0m")
        if firewall:
            firewall.alert_login(ip, username, password)

    def on_file_received(self, file_path):
        ip = self.remote_ip
        filename = os.path.basename(file_path)
        log_ftp_event(ip, 'FTP_UPLOAD', f"File uploaded: {filename}", {'filename': filename})
        print(f"\033[91m[FTP] {ip} uploaded file: {filename}\033[0m")
        if firewall:
            firewall.alert_danger(ip, f"FTP UPLOAD: {filename}")

    def on_file_sent(self, file_path):
        ip = self.remote_ip
        filename = os.path.basename(file_path)
        log_ftp_event(ip, 'FTP_DOWNLOAD', f"File downloaded: {filename}", {'filename': filename})
        print(f"\033[93m[FTP] {ip} downloaded file: {filename}\033[0m")

def main():
    PORT = 2121
    print(f"\n{'='*50}")
    print(f"  NEURO-TRAP FTP HONEYPOT — Port {PORT}")
    print(f"  Mimicking: Standard Linux FTP Server")
    print(f"{'='*50}\n")
    
    # Create a fake root directory for FTP
    os.makedirs(FTP_ROOT, exist_ok=True)
    # Create some bait files
    with open(os.path.join(FTP_ROOT, 'README.txt'), 'w') as f:
        f.write("CONFIDENTIAL: Access restricted to authorized personnel only.\n")
    with open(os.path.join(FTP_ROOT, 'backups.tar.gz'), 'w') as f:
        f.write("FAKE_BACKUP_DATA")
    
    # Use a permissive authorizer for the honeypot
    authorizer = DummyAuthorizer()
    # Permit anyone to login with any password and have full read/write access to root
    authorizer.add_anonymous(FTP_ROOT, perm="elradfmwMT")
    
    handler = HoneypotFTPHandler
    handler.authorizer = authorizer
    handler.banner = "220 (vsFTPd 3.0.3)" # Fake banner
    
    server = FTPServer(('0.0.0.0', PORT), handler)
    print(f"[+] FTP honeypot listening on 0.0.0.0:{PORT}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] FTP honeypot shutting down...")


if __name__ == '__main__':
    main()
