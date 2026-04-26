"""
Neuro-Trap HTTP Honeypot — Port 8080
Enterprise Module: Captures web scanners, SQL injection bots, WordPress exploits.

Mimics an Apache/phpMyAdmin login page. Logs every request.
"""
import http.server
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from urllib.parse import parse_qs, urlparse

IST = timezone(timedelta(hours=5, minutes=30))

# Add parent for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from server import logger, firewall
except ImportError:
    logger = None
    firewall = None

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'http_honeypot.json')

def log_http_event(ip, method, path, headers, body=''):
    """Log HTTP event to file and MongoDB."""
    event = {
        'timestamp': datetime.now(IST).isoformat(),
        'ip': ip,
        'method': method,
        'path': path,
        'user_agent': headers.get('User-Agent', 'Unknown'),
        'body': body[:500],
        'headers': dict(headers)
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(event) + '\n')
    
    if logger:
        details = {'method': method, 'path': path, 'user_agent': event['user_agent']}
        if body:
            details['post_body'] = body[:200]
        logger.log_event('WARNING', 'HTTP_SCAN', f"{method} {path} from {ip}", ip=ip, details=details)
    
    # Alert on dangerous paths
    dangerous = ['admin', 'phpmyadmin', 'wp-login', 'shell', '.env', 'passwd', 'config']
    if any(d in path.lower() for d in dangerous):
        if firewall:
            firewall.alert_danger(ip, f"HTTP {method} {path}")

FAKE_LOGIN_PAGE = """<!DOCTYPE html>
<html><head><title>phpMyAdmin</title>
<style>body{font-family:Arial;background:#2c3e50;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.login{background:#fff;padding:40px;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,.3);width:350px}
h1{color:#e74c3c;text-align:center;margin-bottom:20px;font-size:1.4em}
input{width:100%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:4px;box-sizing:border-box}
button{width:100%;padding:12px;background:#3498db;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:1em}
button:hover{background:#2980b9}
.version{text-align:center;color:#999;font-size:.8em;margin-top:15px}</style></head>
<body><div class="login"><h1>phpMyAdmin</h1>
<form method="POST" action="/login">
<input name="username" placeholder="Username" required>
<input name="password" type="password" placeholder="Password" required>
<input name="server" placeholder="Server: localhost" value="localhost">
<button type="submit">Log In</button></form>
<div class="version">phpMyAdmin 5.2.1 | MySQL 8.0.28</div></div></body></html>"""

FAKE_401 = """<!DOCTYPE html><html><head><title>401 Unauthorized</title></head>
<body><h1>401 Unauthorized</h1><p>This server could not verify that you are authorized to access the document requested.</p>
<hr><address>Apache/2.4.52 (Ubuntu) Server at localhost Port 80</address></body></html>"""


class HoneypotHTTPHandler(http.server.BaseHTTPRequestHandler):
    """Fake HTTP server that mimics Apache + phpMyAdmin."""
    
    server_version = "Apache/2.4.52"
    sys_version = "(Ubuntu)"
    
    def log_message(self, format, *args):
        """Suppress default logging — we use our own."""
        pass
    
    def do_GET(self):
        ip = self.client_address[0]
        log_http_event(ip, 'GET', self.path, self.headers)
        print(f"\033[93m[HTTP] GET {self.path} from {ip}\033[0m")
        
        # Normalize path to ignore query parameters (?token=...)
        clean_path = self.path.split('?')[0]
        
        if clean_path in ('/', '/login', '/phpmyadmin', '/admin', '/admin/login'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(FAKE_LOGIN_PAGE.encode())
        elif '.env' in clean_path or 'config' in clean_path:
            # Bait: return fake credentials
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"DB_HOST=192.168.1.100\nDB_USER=admin\nDB_PASS=P@ssw0rd2024!\nAPI_KEY=sk_live_fake_key_12345\n")
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>404 Not Found</h1>")

    def do_POST(self):
        ip = self.client_address[0]
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8', errors='ignore') if content_length else ''
        log_http_event(ip, 'POST', self.path, self.headers, body)
        print(f"\033[91m[HTTP] POST {self.path} from {ip} | Body: {body[:100]}\033[0m")
        
        # Always return "Invalid credentials" to keep them trying
        self.send_response(401)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(FAKE_401.encode())
    
    def do_HEAD(self):
        log_http_event(self.client_address[0], 'HEAD', self.path, self.headers)
        self.send_response(200)
        self.end_headers()


def main():
    PORT = 8080
    print(f"\n{'='*50}")
    print(f"  NEURO-TRAP HTTP HONEYPOT — Port {PORT}")
    print(f"  Mimicking: Apache/2.4.52 + phpMyAdmin 5.2.1")
    print(f"{'='*50}\n")
    
    server = http.server.HTTPServer(('0.0.0.0', PORT), HoneypotHTTPHandler)
    print(f"[+] HTTP honeypot listening on 0.0.0.0:{PORT}")
    print(f"[+] Test: curl http://localhost:{PORT}/\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] HTTP honeypot shutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()
