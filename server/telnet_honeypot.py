"""
Neuro-Trap Telnet Honeypot — Port 2323
Enterprise Module: Captures IoT botnets (Mirai, Hajime, Mozi).

Mimics a router/camera Telnet login. Accepts any credentials.
"""
import socket
import threading
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from server import logger, firewall
except ImportError:
    logger = None
    firewall = None

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'telnet_honeypot.json')

def log_telnet_event(ip, event_type, message, details=None):
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


def handle_telnet_client(conn, addr):
    ip = addr[0]
    log_telnet_event(ip, 'TELNET_CONNECTION', f'New Telnet connection from {ip}')
    print(f"\033[93m[TELNET] Connection from {ip}\033[0m")
    
    try:
        # Mimic router/camera login
        conn.send(b"\r\n")
        conn.send(b"BusyBox v1.33.1 (2023-10-15 08:12:33 UTC) built-in shell\r\n")
        conn.send(b"\r\n")
        
        # Login prompt
        conn.send(b"login: ")
        username = b''
        while True:
            data = conn.recv(1)
            if not data or data in (b'\r', b'\n'):
                break
            username += data
        username = username.decode('utf-8', errors='ignore').strip()
        
        conn.send(b"\r\nPassword: ")
        password = b''
        while True:
            data = conn.recv(1)
            if not data or data in (b'\r', b'\n'):
                break
            password += data
        password = password.decode('utf-8', errors='ignore').strip()
        
        log_telnet_event(ip, 'TELNET_LOGIN', f'Telnet login: {username}:{password}', 
                        {'username': username, 'password': password})
        print(f"\033[91m[TELNET] Creds from {ip}: {username}:{password}\033[0m")
        
        if firewall:
            firewall.alert_login(ip, username, password)
        
        # Fake shell
        conn.send(b"\r\n\r\n")
        conn.send(b"Welcome to BusyBox!\r\n")
        conn.send(b"Type 'help' for a list of built-in commands.\r\n\r\n")
        
        # Command loop (simple)
        for _ in range(20):  # Max 20 commands then disconnect
            conn.send(f"root@router:~# ".encode())
            cmd = b''
            while True:
                data = conn.recv(1)
                if not data or data in (b'\r', b'\n'):
                    break
                cmd += data
                conn.send(data)  # Echo
            cmd_str = cmd.decode('utf-8', errors='ignore').strip()
            conn.send(b"\r\n")
            
            if not cmd_str:
                continue
            
            log_telnet_event(ip, 'TELNET_COMMAND', cmd_str, {'command': cmd_str})
            print(f"\033[96m[TELNET] {ip} > {cmd_str}\033[0m")
            
            if cmd_str == 'exit':
                break
            elif cmd_str in ('cat /proc/cpuinfo', 'uname -a'):
                conn.send(b"Linux router 4.14.90 #1 SMP MIPS GNU/Linux\r\n")
            elif cmd_str == 'cat /etc/passwd':
                conn.send(b"root:x:0:0:root:/root:/bin/sh\r\nadmin:x:1000:1000::/home/admin:/bin/sh\r\n")
            elif cmd_str in ('ls', 'ls -la'):
                conn.send(b"bin  dev  etc  lib  mnt  proc  root  sbin  sys  tmp  usr  var  www\r\n")
            elif 'wget' in cmd_str or 'curl' in cmd_str or 'tftp' in cmd_str:
                if firewall:
                    firewall.alert_danger(ip, f"TELNET download: {cmd_str}")
                conn.send(b"Connecting... connection timed out.\r\n")
            elif cmd_str == 'id':
                conn.send(b"uid=0(root) gid=0(root)\r\n")
            else:
                conn.send(f"-sh: {cmd_str.split()[0]}: not found\r\n".encode())
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except:
            pass
        log_telnet_event(ip, 'TELNET_DISCONNECT', f'Telnet session ended: {ip}')


def main():
    PORT = 2323
    print(f"\n{'='*50}")
    print(f"  NEURO-TRAP TELNET HONEYPOT — Port {PORT}")
    print(f"  Mimicking: BusyBox IoT device")
    print(f"{'='*50}\n")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', PORT))
    sock.listen(5)
    print(f"[+] Telnet honeypot listening on 0.0.0.0:{PORT}")
    print(f"[+] Test: telnet localhost {PORT}\n")
    
    try:
        while True:
            conn, addr = sock.accept()
            t = threading.Thread(target=handle_telnet_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[*] Telnet honeypot shutting down...")
    finally:
        sock.close()


if __name__ == '__main__':
    main()
