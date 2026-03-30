"""
Neuro-Trap SSH Honeypot Server
Phase 2: AI-Powered "Smart" Server (Uses Llama 3.2 via Ollama)
"""
import socket
import threading
import time # <--- NEW: For keystroke timing and response jitter
import random # <--- NEW: For response jitter
import os
import sys
import select # <--- NEW: For non-blocking accept
from datetime import datetime, timezone, timedelta

# Indian Standard Time (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))
def now_ist():
    return datetime.now(IST)
import paramiko
import sentry_sdk

# Phase 2: Sentry Error Tracking (Centralized crash reporting)
sentry_sdk.init(
    dsn="https://e9fb21060f9563c4613b6202972d3cc2@o4511089686151168.ingest.us.sentry.io/4511089698340864",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

import ai_engine  # AI Engine
import virtual_fs # Virtual Filesystem
import logger # Logger
import sandbox # Containerized Sandbox
import counter_intel # Module 15: Counter-Intelligence + Radioactive Token
import tarpit # Module 17: Data Exhaustion Tar Pit
import firewall # Module 18: Auto-Firewall + Telegram Alerts
import psychology # Module 20: AI Psychology Profiler

# Add project root to path for scripts imports
_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Configuration
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 2222       # Use 2222 to avoid conflicts with real SSH (port 22)
KEY_PATH = os.path.join(os.path.dirname(__file__), '..', 'keys', 'server_key')

# Console colors
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'


class HoneypotServer(paramiko.ServerInterface):
    """
    Fake SSH Server that accepts any credentials
    """
    def __init__(self, client_addr):
        self.event = threading.Event()
        self.client_addr = client_addr
        self.username = None
        self.password = None
    
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
    def check_auth_password(self, username, password):
        """Accept ANY password - this is the honeypot trap!"""
        self.username = username
        self.password = password
        logger.log_event('WARNING', 'AUTH_LOGIN', f"Login attempt: {username}:{password}", 
                        ip=self.client_addr[0], 
                        details={'username': username, 'password': password})
        # Module 18: Telegram alert on login
        firewall.alert_login(self.client_addr[0], username, password)
        return paramiko.AUTH_SUCCESSFUL
    
    def get_allowed_auths(self, username):
        return 'password'
    
    def check_channel_shell_request(self, channel):
        self.event.set()
        return True
    
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True


def handle_connection(client_socket, client_addr):
    """
    Handle a single SSH connection from an attacker
    """
    ip = client_addr[0]
    logger.log_event('INFO', 'CONNECTION', f"New connection from {ip}", ip=ip)
    attacker_profile = None  # Bug 6 fix: Initialize before try block
    transport = None
    
    try:
        # Set up SSH transport
        transport = paramiko.Transport(client_socket)
        transport.local_version = "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1"  # Fake banner
        
        # Load host key
        host_key = paramiko.RSAKey(filename=KEY_PATH)
        transport.add_server_key(host_key)
        
        # Start SSH server
        server = HoneypotServer(client_addr)
        try:
            transport.start_server(server=server)
        except paramiko.SSHException as e:
            logger.log_event('WARNING', 'ERROR', f"SSH negotiation failed: {e}", ip=ip)
            return
        
        # Wait for client to request a channel (allow 5 minutes for them to type password)
        channel = transport.accept(timeout=300)
        if channel is None:
            logger.log_event('WARNING', 'ERROR', "No channel requested (Auth Timeout)", ip=ip)
            return
        
        logger.log_event('INFO', 'AUTH_SUCCESS', f"User {server.username} authenticated", ip=ip, details={'username': server.username})
        
        # ENTERPRISE: HASSH Fingerprinting — capture client's SSH algorithm preferences
        hassh = ''
        remote_version = ''
        try:
            remote_version = transport.remote_version or ''
            # HASSH = MD5 of kex_algorithms;encryption;mac;compression from client
            import hashlib
            sec_opts = transport.get_security_options()
            hassh_raw = ';'.join([
                ','.join(sec_opts.kex) if sec_opts.kex else '',
                ','.join(sec_opts.ciphers) if sec_opts.ciphers else '',
                ','.join(sec_opts.digests) if sec_opts.digests else '',
                ','.join(sec_opts.compression) if sec_opts.compression else ''
            ])
            hassh = hashlib.md5(hassh_raw.encode()).hexdigest()
            logger.log_event('INFO', 'FINGERPRINT', f"HASSH: {hassh} | Client: {remote_version}", ip=ip, 
                           details={'hassh': hassh, 'ssh_version': remote_version, 'hassh_raw': hassh_raw})
        except Exception as e:
            pass  # Non-critical — don't crash if fingerprinting fails
        
        # Wait for shell request
        server.event.wait(30)
        if not server.event.is_set():
            logger.log_event('WARNING', 'ERROR', "No shell requested", ip=ip)
            return
        
        # Send welcome banner
        channel.send("\r\n")
        channel.send("Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)\r\n")
        channel.send("\r\n")
        channel.send(" * Documentation:  https://help.ubuntu.com\r\n")
        channel.send(" * Management:     https://landscape.canonical.com\r\n")
        channel.send(" * Support:        https://ubuntu.com/advantage\r\n")
        channel.send("\r\n")
        channel.send(f"Last login: {now_ist().strftime('%a %b %d %H:%M:%S %Y')} from 10.0.0.1\r\n")
        
        # Initialize Virtual Filesystem for this session
        fs = virtual_fs.VirtualFS()
        
        # Module 15: Initialize Counter-Intelligence profiler
        attacker_profile = counter_intel.AttackerProfile(ip, transport)
        attacker_profile.keystroke_times = [] # NEW: Initialize keystroke times for profiling
        firewall.alert_connection(ip, attacker_profile.ssh_client)
        
        # Module 21: Network Illusion state
        current_fake_server = None  # None = real honeypot, else = fake internal server
        FAKE_SERVERS = {
            '10.0.0.5': ('admin', 'database-server', 'MySQL Database Node'),
            '10.0.0.10': ('root', 'web-server', 'Apache Web Frontend'),
            '10.0.0.15': ('backup', 'backup-node', 'Backup Storage Server'),
            '10.0.0.20': ('admin', 'admin-panel', 'Admin Control Panel'),
            '10.0.0.25': ('deploy', 'ci-server', 'Jenkins CI/CD Server'),
            '192.168.1.100': ('root', 'db-master', 'PostgreSQL Master'),
        }
        
        # Main command loop
        command_buffer = ""
        cursor_pos = 0
        command_history = []
        history_index = 0
        escape_sequence = ""
        in_escape = False
        keystroke_times = [] # Innovation 1: Keystroke Dynamics capture
        
        # Dynamic prompt based on current directory
        def get_prompt() -> str:
            pwd = fs.get_pwd()
            if current_fake_server:
                return f"root@{current_fake_server}:~# "
            if pwd == '/root':
                return "root@production-server:~# "
            return f"root@production-server:{pwd}# "

        while True:
            try:
                channel.send(get_prompt())
                
                command_buffer = ""
                cursor_pos = 0
                keystroke_times_for_command = [] # Store times for current command

                while True:
                    # Receive input character by character
                    data = channel.recv(1) # Receive one character at a time
                    if not data:
                        break
                    
                    # Innovation 1: Record keystroke timestamp
                    keystroke_times_for_command.append(time.time())
                    
                    if isinstance(data, bytes):
                        char = str(data.decode('utf-8', errors='replace'))
                    else:
                        char = str(data) # Should not happen with recv(1)

                    if in_escape:
                        escape_sequence += char
                        # ANSI escape sequences usually end with an alphabet letter or tilde
                        if char.isalpha() or char == '~':
                            if escape_sequence == '\x1b[A':  # Up Arrow
                                if command_history and history_index > 0:
                                    history_index -= 1
                                    command_buffer = command_history[history_index]
                                    cursor_pos = len(command_buffer)
                                    channel.send('\r\x1b[K' + get_prompt() + command_buffer)
                            elif escape_sequence == '\x1b[B':  # Down Arrow
                                if history_index < len(command_history):
                                    history_index += 1
                                    if history_index < len(command_history):
                                        command_buffer = command_history[history_index]
                                    else:
                                        command_buffer = ""
                                    cursor_pos = len(command_buffer)
                                    channel.send('\r\x1b[K' + get_prompt() + command_buffer)
                            elif escape_sequence == '\x1b[C':  # Right Arrow
                                if cursor_pos < len(command_buffer):
                                    cursor_pos += 1
                                    channel.send('\x1b[C')
                            elif escape_sequence == '\x1b[D':  # Left Arrow
                                if cursor_pos > 0:
                                    cursor_pos -= 1
                                    channel.send('\x1b[D')
                            elif escape_sequence in ('\x1b[H', '\x1b[1~'): # Home
                                if cursor_pos > 0:
                                    channel.send(f'\x1b[{cursor_pos}D')
                                    cursor_pos = 0
                            elif escape_sequence in ('\x1b[F', '\x1b[4~'): # End
                                if cursor_pos < len(command_buffer):
                                    channel.send(f'\x1b[{len(command_buffer) - cursor_pos}C')
                                    cursor_pos = len(command_buffer)
                            elif escape_sequence == '\x1b[3~': # Delete
                                if cursor_pos < len(command_buffer):
                                    command_buffer = command_buffer[:cursor_pos] + command_buffer[cursor_pos+1:]
                                    remainder = command_buffer[cursor_pos:]
                                    channel.send('\x1b[K' + remainder)
                                    if remainder:
                                        channel.send(f'\x1b[{len(remainder)}D')
                            in_escape = False
                            escape_sequence = ""
                        continue
                        
                    if char == '\x1b':  # Start of escape sequence (Escape key)
                        in_escape = True
                        escape_sequence = char
                        continue
                    
                    if char == '\r' or char == '\n':
                        # Command entered
                        channel.send("\r\n")
                        
                        cmd_str = command_buffer.strip()
                        if cmd_str:
                            logger.log_event('INFO', 'COMMAND', cmd_str, ip=ip, details={'command': cmd_str})
                            
                            # Add to history if unique
                            if not command_history or command_history[-1] != cmd_str:
                                command_history.append(cmd_str)
                            history_index = int(len(command_history))
                            
                            # Store keystroke times for this command
                            attacker_profile.keystroke_times.append(keystroke_times_for_command)

                            # Module 30: Cognitive Mirror (Adaptive Deception)
                            ai_engine.apply_cognitive_mirror(cmd_str, fs)

                            if cmd_str == 'exit':
                                channel.send("logout\r\n")
                                return

                            # Parse command and arguments
                            parts = cmd_str.split(maxsplit=1)
                            base_cmd = parts[0]
                            args = parts[1] if len(parts) > 1 else None

                            response = None

                            # --- PHASE 3: FILE SYSTEM LOGIC ---
                            if base_cmd == 'cd':
                                if args:
                                    err = fs.change_dir(args)
                                    if err: response = err
                                else:
                                    fs.change_dir('/root') 
                                    
                            elif base_cmd == '..':
                                err = fs.change_dir('..')
                                if err: response = err
                                
                            elif base_cmd in ('ll', 'la', 'l'):
                                args_to_pass = '-al' if base_cmd in ('ll', 'la') else ''
                                if args: 
                                    args_to_pass += f" {args}"
                                response = fs.list_dir(args_to_pass)
                                
                            elif base_cmd == 'ls':
                                args = parts[1] if len(parts) > 1 else '.'
                                response = fs.list_dir(args)
                                
                            elif base_cmd == 'pwd':
                                response = fs.get_pwd()
                                
                            elif base_cmd == 'mkdir':
                                if args:
                                    response = fs.make_dir(args)
                                else:
                                    response = "mkdir: missing operand"
                                    
                            elif base_cmd == 'touch':
                                if args:
                                    response = fs.touch(args)
                                else:
                                    response = "touch: missing file operand"
                                    
                            elif base_cmd == 'cat':
                                if args:
                                    # Module 15: Radioactive Token trap
                                    # Triggers on any sensitive-looking bait file
                                    bait_keywords = ['password', 'credential', 'secret', 'bitcoin', 'wallet', 'id_rsa', 'shadow', 'api_key', 'token']
                                    if any(bait in args.lower() for bait in bait_keywords) and 'log' not in args.lower():
                                        # Check if file exists in virtual FS first
                                        content = fs.read_file(args)
                                        if content is not None:
                                            # Append radioactive token to real bait file content
                                            response = content + "\n" + counter_intel.RADIOACTIVE_TOKEN_CONTENT
                                        else:
                                            response = counter_intel.RADIOACTIVE_TOKEN_CONTENT
                                        # Alert on bait access
                                        firewall.alert_danger(ip, f"BAIT FILE ACCESSED: {args}")
                                    else:
                                        content = fs.read_file(args)
                                        if content is not None:
                                            response = content
                                        else:
                                            response = f"cat: {args}: No such file or directory"
                                else:
                                    response = "cat: missing file operand"

                            elif base_cmd == 'rm':
                                if args:
                                    recursive = '-r' in args
                                    path = args.replace('-r', '').strip()
                                    if not path:
                                        response = "rm: missing operand"
                                    else:
                                        response = fs.remove_path(path, recursive)
                                else:
                                    response = "rm: missing operand"

                            elif base_cmd == 'echo':
                                if '>' in cmd_str:
                                    try:
                                        content_part, file_part = cmd_str.split('>', 1)
                                        content = content_part[5:].strip().strip('"').strip("'")
                                        filename = file_part.strip()
                                        response = fs.write_file(filename, content)
                                    except:
                                        response = "bash: syntax error near unexpected token `newline'"
                                else:
                                    response = cmd_str[5:]
                            
                            elif base_cmd == 'clear':
                                channel.send('\x1b[2J\x1b[H')
                                response = None
                                
                            # --- PHASE 3.5: STANDARD LINUX COMMANDS (Hyper-Realism) ---
                            elif base_cmd == 'whoami':
                                response = "root" if fs.get_pwd() != '/home/user' else "user"
                            elif base_cmd == 'id':
                                if fs.get_pwd() != '/home/user':
                                    response = "uid=0(root) gid=0(root) groups=0(root)"
                                else:
                                    response = "uid=1000(user) gid=1000(user) groups=1000(user),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),122(lpadmin),134(lxd),135(sambashare)"
                            elif base_cmd == 'uname':
                                if args and '-a' in args:
                                    response = "Linux production-server 5.15.0-91-generic #101-Ubuntu SMP Tue Nov 14 13:30:08 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux"
                                elif args and '-r' in args:
                                    response = "5.15.0-91-generic"
                                elif args and '-m' in args:
                                    response = "x86_64"
                                elif args and '-n' in args:
                                    response = "production-server"
                                else:
                                    response = "Linux"
                            elif base_cmd == 'hostname':
                                if args == '-I':
                                    response = "10.0.0.45"
                                elif args == '-f':
                                    response = "production-server.company.internal"
                                else:
                                    response = "production-server"
                            elif base_cmd == 'date':
                                response = now_ist().strftime('%a %b %d %H:%M:%S UTC %Y')
                            elif base_cmd == 'uptime':
                                response = f" {now_ist().strftime('%H:%M:%S')} up 47 days,  3:22,  1 user,  load average: 0.08, 0.03, 0.01"
                            elif base_cmd == 'ps':
                                response = "PID TTY          TIME CMD\n    1 ?        00:00:02 systemd\n  500 ?        00:00:00 sshd\n  501 pts/0    00:00:00 bash\n  502 pts/0    00:00:00 ps"
                                if args and 'a' in args:
                                    response = "USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\nroot           1  0.0  0.1 167576 11200 ?        Ss   Jan10   0:02 /sbin/init\nroot          23  0.0  0.0      0     0 ?        S    Jan10   0:00 [kworker/0:0H]\nroot         189  0.0  0.1  72300  6168 ?        Ss   Jan10   0:03 /usr/sbin/sshd -D\nroot         201  0.0  0.0   5600  1532 ?        Ss   Jan10   0:00 /usr/sbin/cron -f\nroot         214  0.0  0.1 281092 10388 ?        Ssl  Jan10   0:15 /usr/lib/snapd/snapd\nmysql        310  0.1  2.5 1789456 207648 ?      Ssl  Jan10   5:32 /usr/sbin/mysqld\nwww-data     450  0.0  0.3 214432 25800 ?        S    Jan10   0:44 /usr/sbin/apache2 -k start\nroot         500  0.0  0.0  12148  8332 ?        Ss   10:00   0:00 sshd: root@pts/0\nroot         501  0.0  0.0   7100  3240 pts/0    Ss   10:00   0:00 -bash\nroot         502  0.0  0.0   8400  3304 pts/0    R+   10:05   0:00 ps aux"
                            elif base_cmd in ('ifconfig', 'ip'):
                                if base_cmd == 'ip' and args and args.startswith('a'):
                                    response = "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000\n    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00\n    inet 127.0.0.1/8 scope host lo\n       valid_lft forever preferred_lft forever\n2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000\n    link/ether 00:15:5d:00:61:63 brd ff:ff:ff:ff:ff:ff\n    inet 10.0.0.45/24 brd 10.0.0.255 scope global eth0\n       valid_lft forever preferred_lft forever"
                                else:
                                    response = "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n        inet 10.0.0.45  netmask 255.255.255.0  broadcast 10.0.0.255\n        inet6 fe80::215:5dff:fe00:6163  prefixlen 64  scopeid 0x20<link>\n        ether 00:15:5d:00:61:63  txqueuelen 1000  (Ethernet)\n        RX packets 123456  bytes 102345678 (102.3 MB)\n        TX packets 654321  bytes 876543210 (876.5 MB)\n\nlo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536\n        inet 127.0.0.1  netmask 255.0.0.0\n        inet6 ::1  prefixlen 128  scopeid 0x10<host>\n        loop  txqueuelen 1000  (Local Loopback)\n        RX packets 123  bytes 12345 (12.3 KB)\n        TX packets 123  bytes 12345 (12.3 KB)"
                            elif base_cmd == 'netstat':
                                if args and '-t' in args:
                                    response = "Active Internet connections (w/o servers)\nProto Recv-Q Send-Q Local Address           Foreign Address         State\ntcp        0     64 10.0.0.45:22            10.0.0.1:54321          ESTABLISHED\ntcp        0      0 10.0.0.45:5432          192.168.1.100:3306      ESTABLISHED\ntcp        0      0 10.0.0.45:80            0.0.0.0:*               LISTEN"
                                else:
                                    response = "Active Internet connections (w/o servers)\nProto Recv-Q Send-Q Local Address           Foreign Address         State      \ntcp        0     64 10.0.0.45:22            10.0.0.1:54321          ESTABLISHED\ntcp        0      0 10.0.0.45:5432          192.168.1.100:3306      ESTABLISHED"
                            elif base_cmd == 'ss':
                                response = "Netid  State   Recv-Q  Send-Q   Local Address:Port    Peer Address:Port  Process\ntcp    ESTAB   0       64       10.0.0.45:22          10.0.0.1:54321\ntcp    ESTAB   0       0        10.0.0.45:5432        192.168.1.100:3306\ntcp    LISTEN  0       128      0.0.0.0:80            0.0.0.0:*\ntcp    LISTEN  0       128      0.0.0.0:22            0.0.0.0:*\ntcp    LISTEN  0       80       127.0.0.1:3306        0.0.0.0:*"
                            elif base_cmd == 'history':
                                response = "\n".join([f" {i+1}  {cmd}" for i, cmd in enumerate(command_history)])
                            elif base_cmd == 'ping':
                                target_host = args.split()[0] if args else '8.8.8.8'
                                response = f"PING {target_host} ({target_host}) 56(84) bytes of data.\n64 bytes from {target_host}: icmp_seq=1 ttl=116 time=14.2 ms\n64 bytes from {target_host}: icmp_seq=2 ttl=116 time=13.8 ms\n64 bytes from {target_host}: icmp_seq=3 ttl=116 time=14.5 ms\n--- {target_host} ping statistics ---\n3 packets transmitted, 3 received, 0% packet loss, time 2003ms\nrtt min/avg/max/mdev = 13.843/14.188/14.531/0.281 ms"
                            elif base_cmd == 'traceroute':
                                target_host = args if args else '8.8.8.8'
                                response = f"traceroute to {target_host} ({target_host}), 30 hops max, 60 byte packets\n 1  gateway (10.0.0.1)  0.543 ms  0.621 ms  0.712 ms\n 2  isp-router (203.0.113.1)  5.234 ms  5.312 ms  5.401 ms\n 3  core-router (198.51.100.1)  10.123 ms  10.234 ms  10.312 ms\n 4  {target_host} ({target_host})  14.234 ms  14.312 ms  14.401 ms"
                            elif base_cmd == 'free':
                                response = "               total        used        free      shared  buff/cache   available\nMem:         8154320     2345128     3456780      123456     2352412     5432100\nSwap:        2097148           0     2097148"
                            elif base_cmd == 'top':
                                response = f"top - {now_ist().strftime('%H:%M:%S')} up 47 days,  3:22,  1 user,  load average: 0.08, 0.03, 0.01\nTasks: 127 total,   1 running, 126 sleeping,   0 stopped,   0 zombie\n%Cpu(s):  1.3 us,  0.7 sy,  0.0 ni, 97.8 id,  0.2 wa,  0.0 hi,  0.0 si,  0.0 st\nMiB Mem :   7963.2 total,   3376.5 free,   2290.1 used,   2296.5 buff/cache\nMiB Swap:   2048.0 total,   2048.0 free,      0.0 used.   5308.7 avail Mem\n\n    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND\n    310 mysql     20   0 1789456 207648  36224 S   0.3   2.5   5:32.15 mysqld\n    450 www-data  20   0  214432  25800   8452 S   0.1   0.3   0:44.23 apache2\n      1 root      20   0  167576  11200   8400 S   0.0   0.1   0:02.34 systemd\n    189 root      20   0   72300   6168   5400 S   0.0   0.1   0:03.12 sshd"
                            elif base_cmd == 'htop':
                                response = f"  CPU[||                       1.3%]   Tasks: 127, 1 running\n  Mem[||||||||            2290M/7963M]   Load average: 0.08 0.03 0.01\n  Swp[                    0K/2048M]   Uptime: 47 days, 03:22:15\n\n  PID USER      PRI  NI  VIRT   RES   SHR S CPU% MEM%   TIME+  Command\n  310 mysql      20   0 1789M  207M 36224 S  0.3  2.5  5:32.15 /usr/sbin/mysqld\n  450 www-data   20   0  214M 25800  8452 S  0.1  0.3  0:44.23 /usr/sbin/apache2\n    1 root       20   0  167M 11200  8400 S  0.0  0.1  0:02.34 /sbin/init"
                            elif base_cmd == 'df':
                                response = "Filesystem     1K-blocks    Used Available Use% Mounted on\n/dev/sda1       51474044 12345672  36488596  26% /\ntmpfs            4077160        0   4077160   0% /dev/shm\ntmpfs             815432     1236    814196   1% /run\ntmpfs               5120        4      5116   1% /run/lock\n/dev/sda15        106858     6186    100672   6% /boot/efi"
                            elif base_cmd == 'du':
                                if args:
                                    response = f"4.0K\t{args}"
                                else:
                                    response = "12K\t./Documents\n8.0K\t./secret_data\n4.0K\t./.ssh\n4.0K\t./Desktop\n4.0K\t./Downloads\n36K\t."
                            elif base_cmd == 'mount':
                                response = "/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro)\nsysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)\nproc on /proc type proc (rw,nosuid,nodev,noexec,relatime)\ntmpfs on /run type tmpfs (rw,nosuid,nodev,noexec,relatime,size=815432k)\n/dev/sda15 on /boot/efi type vfat (rw,relatime,fmask=0077,dmask=0077)"
                            elif base_cmd == 'lsblk':
                                response = "NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT\nsda      8:0    0   50G  0 disk \n├─sda1   8:1    0 49.1G  0 part /\n├─sda14  8:14   0    4M  0 part \n└─sda15  8:15   0  106M  0 part /boot/efi\nsr0     11:0    1 1024M  0 rom"
                            elif base_cmd in ('w', 'who'):
                                response = f" {now_ist().strftime('%H:%M:%S')} up 47 days,  3:22,  1 user,  load average: 0.08, 0.03, 0.01\nUSER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT\nroot     pts/0    {ip:<16} {now_ist().strftime('%H:%M')}    0.00s  0.04s  0.00s w"
                            elif base_cmd == 'last':
                                response = f"root     pts/0        {ip:<16} {now_ist().strftime('%a %b %d %H:%M')}   still logged in\nroot     pts/0        10.0.0.1         Wed Feb 10 14:20 - 14:35  (00:15)\nroot     pts/0        10.0.0.1         Tue Feb  9 09:10 - 10:30  (01:20)\nreboot   system boot  5.15.0-91-generi Wed Feb  3 10:00   still running\n\nwtmp begins Wed Feb  3 10:00:00 2024"
                            elif base_cmd in ('env', 'printenv'):
                                response = "SHELL=/bin/bash\nPATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\nHOME=/root\nLOGNAME=root\nUSER=root\nLANG=en_US.UTF-8\nTERM=xterm-256color\nSSH_CONNECTION={ip} 54321 10.0.0.45 22\nSSH_CLIENT={ip} 54321 22\nSSH_TTY=/dev/pts/0\nHOSTNAME=production-server\nOLDPWD=/root"
                            elif base_cmd == 'export':
                                response = ""  # Silent success just like real bash
                            elif base_cmd in ('unset', 'alias', 'unalias'):
                                response = ""  # Silent success
                            elif base_cmd in ('systemctl', 'service'):
                                if args and 'status' in args:
                                    svc = args.split()[-1] if args else 'unknown'
                                    response = f"● {svc}.service - {svc.title()} Service\n     Loaded: loaded (/lib/systemd/system/{svc}.service; enabled; vendor preset: enabled)\n     Active: active (running) since Wed 2024-02-03 10:00:00 UTC; 47 days ago\n   Main PID: 310 ({svc})\n      Tasks: 31 (limit: 9451)\n     Memory: 207.6M\n        CPU: 5min 32.150s\n     CGroup: /system.slice/{svc}.service"
                                elif args and ('start' in args or 'stop' in args or 'restart' in args):
                                    response = ""  # Silent success like real systemctl
                                elif args and 'list-units' in args:
                                    response = "  UNIT                     LOAD   ACTIVE SUB       DESCRIPTION\n  cron.service             loaded active running   Regular background program processing\n  mysql.service            loaded active running   MySQL Community Server\n  apache2.service          loaded active running   Apache HTTP Server\n  ssh.service              loaded active running   OpenBSD Secure Shell server\n  snapd.service            loaded active running   Snap Daemon"
                                else:
                                    response = "Unit unknown.service could not be found."
                            elif base_cmd == 'crontab':
                                if args == '-l':
                                    response = "# m h  dom mon dow   command\n0 2 * * * /usr/local/bin/backup.sh\n*/5 * * * * /usr/bin/check_health.sh\n0 0 * * 0 /usr/local/bin/log_rotate.sh"
                                elif args == '-e':
                                    response = "no changes made to crontab"
                                else:
                                    response = "crontab: usage error: unrecognized option"
                            elif base_cmd == 'iptables':
                                if args and '-L' in args:
                                    response = "Chain INPUT (policy ACCEPT)\ntarget     prot opt source               destination\nACCEPT     all  --  anywhere             anywhere             state RELATED,ESTABLISHED\nACCEPT     tcp  --  anywhere             anywhere             tcp dpt:ssh\nACCEPT     tcp  --  anywhere             anywhere             tcp dpt:http\nDROP       all  --  anywhere             anywhere\n\nChain FORWARD (policy DROP)\ntarget     prot opt source               destination\n\nChain OUTPUT (policy ACCEPT)\ntarget     prot opt source               destination"
                                else:
                                    response = "iptables: no command specified\nTry `iptables -h' for more information."
                            elif base_cmd == 'nmap':
                                if args:
                                    target_host = args.split()[-1]
                                    response = f"Starting Nmap 7.80 ( https://nmap.org ) at {now_ist().strftime('%Y-%m-%d %H:%M')} UTC\nNmap scan report for {target_host}\nHost is up (0.0012s latency).\nNot shown: 997 closed ports\nPORT     STATE SERVICE\n22/tcp   open  ssh\n80/tcp   open  http\n3306/tcp open  mysql\n\nNmap done: 1 IP address (1 host up) scanned in 1.45 seconds"
                                else:
                                    response = "Nmap 7.80 ( https://nmap.org )\nUsage: nmap [Scan Type(s)] [Options] {target specification}"
                            elif base_cmd == 'head':
                                if args:
                                    fname = args.split()[-1]
                                    content = fs.read_file(fname)
                                    if content is not None:
                                        lines = content.split('\\n')
                                        response = '\n'.join(lines[:10])
                                    else:
                                        response = f"head: cannot open '{fname}' for reading: No such file or directory"
                                else:
                                    response = "head: missing file operand"
                            elif base_cmd == 'tail':
                                if args:
                                    fname = args.split()[-1]
                                    content = fs.read_file(fname)
                                    if content is not None:
                                        lines = content.split('\\n')
                                        response = '\n'.join(lines[-10:])
                                    else:
                                        response = f"tail: cannot open '{fname}' for reading: No such file or directory"
                                else:
                                    response = "tail: missing file operand"
                            elif base_cmd == 'wc':
                                if args:
                                    fname = args.split()[-1]
                                    content = fs.read_file(fname)
                                    if content is not None:
                                        lines = content.count('\\n') + 1
                                        words = len(content.split())
                                        chars = len(content)
                                        response = f"  {lines}   {words}  {chars} {fname}"
                                    else:
                                        response = f"wc: {fname}: No such file or directory"
                                else:
                                    response = "wc: missing file operand"
                            elif base_cmd == 'file':
                                if args:
                                    fname = args.strip()
                                    content = fs.read_file(fname)
                                    if content is not None:
                                        if fname.endswith('.txt') or fname.endswith('.log') or fname.endswith('.conf') or fname.endswith('.cfg'):
                                            response = f"{fname}: ASCII text"
                                        elif fname.endswith('.pdf'):
                                            response = f"{fname}: PDF document, version 1.7"
                                        elif fname.endswith('.xlsx') or fname.endswith('.xls'):
                                            response = f"{fname}: Microsoft Excel 2007+"
                                        elif fname.endswith('.ovpn'):
                                            response = f"{fname}: ASCII text"
                                        else:
                                            response = f"{fname}: ASCII text"
                                    else:
                                        node = fs._get_node(fs._resolve_path(fname).strip('/'))
                                        if node is not None and isinstance(node, dict):
                                            response = f"{fname}: directory"
                                        else:
                                            response = f"{fname}: cannot open `{fname}' (No such file or directory)"
                                else:
                                    response = "Usage: file [-bcEhikLlNnprsSvzZ0] [--apple] [--mime-encoding] [--mime-type] [-f namefile] [-m magicfiles] file"
                            elif base_cmd == 'grep':
                                if args:
                                    parts_g = args.split()
                                    if len(parts_g) >= 2:
                                        pattern = parts_g[0].strip('"').strip("'")
                                        fname = parts_g[-1]
                                        content = fs.read_file(fname)
                                        if content is not None:
                                            matching = [l for l in content.split('\\n') if pattern.lower() in l.lower()]
                                            response = '\n'.join(matching) if matching else ""
                                        else:
                                            response = f"grep: {fname}: No such file or directory"
                                    else:
                                        response = "Usage: grep [OPTION]... PATTERNS [FILE]..."
                                else:
                                    response = "Usage: grep [OPTION]... PATTERNS [FILE]..."
                            elif base_cmd == 'find':
                                if args:
                                    # Simulate basic find output
                                    response = f".\n./Documents\n./Documents/project_notes.txt\n./Documents/passwords.txt\n./Documents/important.txt\n./Documents/company_financials.xlsx\n./secret_data\n./secret_data/backup_credentials.txt\n./secret_data/vpn_config.ovpn\n./Desktop\n./Downloads\n./.ssh\n./.ssh/known_hosts\n./.ssh/config"
                                else:
                                    response = f".\n./Documents\n./Documents/project_notes.txt\n./Documents/passwords.txt\n./Documents/important.txt\n./Documents/company_financials.xlsx\n./secret_data\n./secret_data/backup_credentials.txt\n./secret_data/vpn_config.ovpn\n./Desktop\n./Downloads\n./.ssh\n./.ssh/known_hosts\n./.ssh/config"
                            elif base_cmd in ('sort', 'uniq', 'tr', 'cut', 'awk', 'sed'):
                                if args:
                                    # For piped operations or file args, try to read the file
                                    fname = args.split()[-1]
                                    content = fs.read_file(fname)
                                    if content is not None:
                                        response = content  # Passthrough for simplicity
                                    else:
                                        response = f"{base_cmd}: {fname}: No such file or directory"
                                else:
                                    response = ""  # Waiting for stdin (just return empty like real)
                            elif base_cmd in ('vi', 'vim', 'nano'):
                                if args:
                                    response = f"Error: Terminal type 'dumb' is not supported by {base_cmd}."
                                else:
                                    response = f"Error: Terminal type 'dumb' is not supported by {base_cmd}."
                            elif base_cmd in ('less', 'more'):
                                if args:
                                    content = fs.read_file(args)
                                    if content is not None:
                                        response = content
                                    else:
                                        response = f"{args}: No such file or directory"
                                else:
                                    response = f"Missing filename (\"{base_cmd} --help\" for help)"
                            elif base_cmd == 'man':
                                if args:
                                    response = f"No manual entry for {args}\nSee 'man 7 undocumented' for help."
                                else:
                                    response = "What manual page do you want?\nFor example, try 'man man'."
                            elif base_cmd in ('apt', 'apt-get'):
                                if args and 'update' in args:
                                    response = "Reading package lists... Done\nE: Could not open lock file /var/lib/apt/lists/lock - open (13: Permission denied)\nE: Unable to lock directory /var/lib/apt/lists/"
                                elif args and 'install' in args:
                                    pkg = args.split()[-1]
                                    response = f"Reading package lists... Done\nBuilding dependency tree... Done\nE: Unable to locate package {pkg}"
                                else:
                                    response = "Usage: apt [options] command\n\nMost used commands:\n  list - list packages\n  search - search in package descriptions\n  install - install packages\n  update - update list of available packages"
                            elif base_cmd in ('yum', 'dnf'):
                                response = f"bash: {base_cmd}: command not found"
                            elif base_cmd == 'chmod':
                                if args:
                                    response = ""  # Silent success like real chmod
                                else:
                                    response = "chmod: missing operand\nTry 'chmod --help' for more information."
                            elif base_cmd == 'chown':
                                if args:
                                    response = ""  # Silent success
                                else:
                                    response = "chown: missing operand\nTry 'chown --help' for more information."
                            elif base_cmd == 'cp':
                                if args and len(args.split()) >= 2:
                                    response = ""  # Silent success
                                else:
                                    response = "cp: missing file operand\nTry 'cp --help' for more information."
                            elif base_cmd == 'mv':
                                if args and len(args.split()) >= 2:
                                    response = ""  # Silent success
                                else:
                                    response = "mv: missing file operand\nTry 'mv --help' for more information."
                            elif base_cmd == 'which':
                                known_bins = {'ls': '/usr/bin/ls', 'cat': '/usr/bin/cat', 'grep': '/usr/bin/grep', 'find': '/usr/bin/find', 'python3': '/usr/bin/python3', 'python': '/usr/bin/python3', 'ssh': '/usr/bin/ssh', 'scp': '/usr/bin/scp', 'curl': '/usr/bin/curl', 'wget': '/usr/bin/wget', 'nmap': '/usr/bin/nmap', 'bash': '/usr/bin/bash', 'sh': '/usr/bin/sh', 'mysql': '/usr/bin/mysql', 'docker': '/usr/bin/docker', 'git': '/usr/bin/git', 'vim': '/usr/bin/vim', 'nano': '/usr/bin/nano', 'awk': '/usr/bin/awk', 'sed': '/usr/bin/sed', 'tar': '/usr/bin/tar', 'zip': '/usr/bin/zip', 'unzip': '/usr/bin/unzip', 'nc': '/usr/bin/nc', 'netstat': '/usr/bin/netstat', 'ss': '/usr/sbin/ss'}
                                if args and args in known_bins:
                                    response = known_bins[args]
                                elif args:
                                    response = f"{args} not found"
                                else:
                                    response = ""
                            elif base_cmd == 'type':
                                if args:
                                    builtins = ['cd', 'echo', 'export', 'alias', 'source', 'exit', 'history', 'pwd']
                                    if args in builtins:
                                        response = f"{args} is a shell builtin"
                                    else:
                                        response = f"{args} is /usr/bin/{args}"
                                else:
                                    response = ""
                            elif base_cmd == 'docker':
                                if args and 'ps' in args:
                                    response = "CONTAINER ID   IMAGE          COMMAND       CREATED        STATUS        PORTS     NAMES\na1b2c3d4e5f6   nginx:latest   \"nginx -g…\"   3 days ago     Up 3 days     80/tcp    web-frontend\nf6e5d4c3b2a1   mysql:8.0      \"mysqld\"      5 days ago     Up 5 days     3306/tcp  db-primary"
                                elif args and 'images' in args:
                                    response = "REPOSITORY   TAG       IMAGE ID       CREATED        SIZE\nnginx        latest    a1b2c3d4e5f6   2 weeks ago    187MB\nmysql        8.0       f6e5d4c3b2a1   3 weeks ago    564MB\nubuntu       22.04     1234abcd5678   4 weeks ago    77.8MB"
                                else:
                                    response = "Usage:  docker [OPTIONS] COMMAND\n\nA self-sufficient runtime for containers"
                            elif base_cmd == 'git':
                                if args and 'status' in args:
                                    response = "fatal: not a git repository (or any of the parent directories): .git"
                                elif args and 'log' in args:
                                    response = "fatal: not a git repository (or any of the parent directories): .git"
                                else:
                                    response = "usage: git [-v | --version] [-h | --help] [-C <path>] [-c <name>=<value>]"
                            elif base_cmd in ('mysql', 'psql'):
                                response = f"ERROR 1045 (28000): Access denied for user 'root'@'localhost' (using password: NO)"
                            elif base_cmd == 'scp':
                                response = "usage: scp [-346ABCpqrTv] [-c cipher] [-F ssh_config] [-i identity_file]\n           [-J destination] [-l limit] [-o ssh_option] [-P port]\n           [-S program] source ... target"
                            elif base_cmd == 'sudo':
                                if args:
                                    response = f"[sudo] password for root: \nroot is not in the sudoers file.  This incident will be reported."
                                else:
                                    response = "usage: sudo -h | -K | -k | -V\nusage: sudo [-ABbEHnPS] [-C num] [-D directory] [-g group] [-h host]"
                            elif base_cmd in ('reboot', 'shutdown', 'halt', 'poweroff', 'init'):
                                response = f"Failed to issue method call: Access denied"
                                firewall.alert_danger(ip, cmd_str)
                            elif base_cmd == 'dmesg':
                                response = "[    0.000000] Linux version 5.15.0-91-generic (buildd@lgw01-amd64-060) (gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0)\n[    0.000000] Command line: BOOT_IMAGE=/boot/vmlinuz-5.15.0-91-generic root=UUID=a1b2c3d4 ro quiet splash\n[    2.345678] EXT4-fs (sda1): mounted filesystem with ordered data mode.\n[    3.456789] systemd[1]: Detected architecture x86-64.\n[    3.456800] systemd[1]: Hostname set to <production-server>."
                            elif base_cmd in ('lscpu', 'lshw'):
                                response = "Architecture:                    x86_64\nCPU op-mode(s):                  32-bit, 64-bit\nByte Order:                      Little Endian\nCPU(s):                          2\nThread(s) per core:              1\nCore(s) per socket:              2\nModel name:                      Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz\nCPU MHz:                         2400.000\nBogoMIPS:                        4800.06"
                            elif base_cmd in ('cat', 'tac'):
                                # Should not reach here (handled above), but fallback
                                if args:
                                    response = f"cat: {args}: No such file or directory"
                                else:
                                    response = "cat: missing file operand"
                            
                            # --- PHASE 3: CONTAINERIZED MALWARE SANDBOX ---
                            elif base_cmd in ('wget', 'curl', './payload', 'bash'):
                                response = sandbox.deploy_payload(cmd_str, ip)
                                firewall.alert_danger(ip, cmd_str)
                            
                            # --- MODULE 17, 31, 32: DATA EXHAUSTION TAR PITS & STRIKE-BACK ---
                            elif base_cmd in ('mysqldump', 'pg_dump', 'mongodump', 'tar', 'zip', 'nc'):
                                response = tarpit.activate_tarpit(cmd_str, channel)
                                if response == "":
                                    return # Channel was closed during tarpit/black hole
                                firewall.alert_danger(ip, cmd_str)
                            
                            # --- MODULE 21: INFINITE NETWORK ILLUSION ---
                            elif base_cmd == 'ssh':
                                if args:
                                    # Parse ssh target: ssh user@host or ssh host
                                    target = args.split()[-1] if args else ''
                                    target_ip = target.split('@')[-1] if '@' in target else target
                                    
                                    if target_ip in FAKE_SERVERS:
                                        fake_user, fake_host, fake_desc = FAKE_SERVERS[target_ip]
                                        current_fake_server = fake_host
                                        response = f"{fake_user}@{target_ip}'s password: \n"
                                        response += f"Welcome to Ubuntu 22.04.3 LTS — {fake_desc}\n"
                                        response += f"Last login: {now_ist().strftime('%a %b %d %H:%M:%S %Y')} from 10.0.0.45\n"
                                        # Switch prompt to fake server
                                        if response is not None:
                                            # Module 22: Anti-Fingerprinting (Response Jitter)
                                            # Adds 50-200ms delay to simulate human/server realism
                                            time.sleep(random.uniform(0.05, 0.2))
                                            
                                            # Send response with \r\n conversion
                                            channel.send(response.replace('\n', '\r\n') + '\r\n')
                                        response = None  # Already sent
                                    else:
                                        response = f"ssh: connect to host {target_ip} port 22: Connection refused"
                                else:
                                    response = "usage: ssh [-46AaCfGgKkMNnqsTtVvXxYy] destination"
                            
                            # --- REALISTIC FALLBACK: Unknown command = bash error ---
                            else:
                                response = f"bash: {base_cmd}: command not found"
                            
                            # Module 15: Record command for DNA profiling
                            attacker_profile.record_command(cmd_str)
                            
                            # Module 18: Alert on dangerous commands
                            if any(d in cmd_str.lower() for d in ['rm -rf', 'chmod +x', 'bash -i', '/dev/tcp', 'nc ']):
                                firewall.alert_danger(ip, cmd_str)
                            
                            # Send response back to attacker
                            if response:
                                formatted_response = response.replace('\n', '\r\n')
                                channel.send(formatted_response + "\r\n")
                        
                        command_buffer = ""
                        cursor_pos = 0
                        # Module 21: Dynamic prompt for Network Illusion
                        if current_fake_server:
                            channel.send(f"root@{current_fake_server}:~# ")
                        else:
                            channel.send(get_prompt())
                    
                    elif char in ('\x7f', '\x08'):  # Backspace
                        if cursor_pos > 0:
                            command_buffer = command_buffer[:cursor_pos-1] + command_buffer[cursor_pos:]
                            cursor_pos -= 1
                            remainder = command_buffer[cursor_pos:]
                            channel.send('\b\x1b[K' + remainder)
                            if remainder:
                                channel.send(f'\x1b[{len(remainder)}D')
                    
                    elif char == '\x01':  # Ctrl+A
                        if cursor_pos > 0:
                            channel.send(f'\x1b[{cursor_pos}D')
                            cursor_pos = 0
                    
                    elif char == '\x05':  # Ctrl+E
                        if cursor_pos < len(command_buffer):
                            channel.send(f'\x1b[{len(command_buffer) - cursor_pos}C')
                            cursor_pos = len(command_buffer)
                            
                    elif char == '\x0c':  # Ctrl+L (Clear screen)
                        channel.send('\x1b[2J\x1b[H' + get_prompt() + command_buffer)
                        if cursor_pos < len(command_buffer):
                            channel.send(f'\x1b[{len(command_buffer) - cursor_pos}D')
                            
                    elif char == '\x15':  # Ctrl+U (Clear line before cursor)
                        if cursor_pos > 0:
                            channel.send(f'\x1b[{cursor_pos}D\x1b[K' + command_buffer[cursor_pos:])
                            if len(command_buffer) > cursor_pos:
                                channel.send(f'\x1b[{len(command_buffer) - cursor_pos}D')
                            command_buffer = command_buffer[cursor_pos:]
                            cursor_pos = 0

                    elif char == '\x03':  # Ctrl+C
                        channel.send("^C\r\n")
                        command_buffer = ""
                        cursor_pos = 0
                        channel.send(get_prompt())
                    
                    elif char == '\x04':  # Ctrl+D (exit)
                        logger.log_event('INFO', 'DISCONNECT', "Session ended by user (Ctrl+D)", ip=ip)
                        channel.send("logout\r\n")
                        return
                    
                    elif char >= '\x20' and char <= '\x7e':
                        # Normal character
                        command_buffer = command_buffer[:cursor_pos] + char + command_buffer[cursor_pos:]
                        remainder = command_buffer[cursor_pos:]
                        cursor_pos += 1
                        channel.send(remainder)
                        if len(remainder) > 1:
                            channel.send(f'\x1b[{len(remainder)-1}D')
                        
            except Exception as e:
                logger.log_event('WARNING', 'ERROR', f"Error in session: {e}", ip=ip)
                break
        
    except Exception as e:
        logger.log_event('WARNING', 'ERROR', f"Connection error: {e}", ip=ip)
    
    finally:
        # Module 15: Save attacker profile and run psychology analysis
        try:
            if attacker_profile is not None:
                attacker_profile.save_profile()
                logger.log_event('INFO', 'SYSTEM', f"Attacker profile saved for {ip}", ip=ip)
                if len(attacker_profile.commands) >= 3:
                    bio_hash = "Processing..."
                    if hasattr(attacker_profile, 'get_biometric_hash'):
                        bio_hash = attacker_profile.get_biometric_hash()
                    
                    psych = psychology.classify_attacker(attacker_profile.commands, ip, bio_hash)
                    logger.log_event('INFO', 'PSYCHOLOGY', 
                        f"Classification: {psych.get('classification')} | Danger: {psych.get('danger_rating')}/10",
                        ip=ip, details=psych)
                    # Module 18: Alert on threat escalation
                    if psych.get('danger_rating', 0) >= 6:
                        firewall.alert_threat(ip, f"Danger {psych.get('danger_rating')}/10", psych.get('classification', 'Unknown'))
        except Exception as e:
            logger.log_event('WARNING', 'ERROR', f"Profile/psychology analysis failed: {e}", ip=ip)
        
        # Module 18: Auto-generate firewall rules after every session
        try:
            blocked = firewall.generate_firewall_rules(threshold=3)
            if blocked:
                logger.log_event('INFO', 'FIREWALL', f"Auto-firewall rules updated: {len(blocked)} IPs blocked", ip=ip)
        except Exception as e:
            logger.log_event('WARNING', 'ERROR', f"Firewall rule generation failed: {e}", ip=ip)
        
        # Module 14: Auto-generate threat feed
        try:
            from scripts.generate_threat_feed import parse_logs, generate_blocklist, generate_report
            events = parse_logs()
            if events:
                import json as _json
                feed_dir = os.path.join(_PROJECT_ROOT, 'threat_feed')
                os.makedirs(feed_dir, exist_ok=True)
                # Write blocklist
                blocklist = generate_blocklist(events)
                with open(os.path.join(feed_dir, 'blocklist.txt'), 'w') as f:
                    f.write(f"# Neuro-Trap IP Blocklist\n# Auto-generated: {now_ist().isoformat()}\n")
                    for blocked_ip in blocklist:
                        f.write(blocked_ip + '\n')
                # Write report
                report = generate_report(events)
                with open(os.path.join(feed_dir, 'report.json'), 'w') as f:
                    _json.dump(report, f, indent=2)
                logger.log_event('INFO', 'THREAT_FEED', f"Threat feed updated: {len(blocklist)} IPs, {len(events)} events", ip=ip)
        except Exception as e:
            logger.log_event('WARNING', 'ERROR', f"Threat feed generation failed: {e}", ip=ip)
        
        # Module 19: AI Incident Report (run in background thread to avoid blocking)
        def _generate_report_background():
            try:
                from scripts.ai_threat_report import load_logs, load_profiles as load_report_profiles, generate_report_with_ai
                events = load_logs()
                profiles = load_report_profiles()
                if events:
                    report_text = generate_report_with_ai(events, profiles)
                    report_dir = os.path.join(_PROJECT_ROOT, 'threat_feed')
                    os.makedirs(report_dir, exist_ok=True)
                    with open(os.path.join(report_dir, 'incident_report.md'), 'w', encoding='utf-8') as f:
                        f.write(report_text)
                    logger.log_event('INFO', 'REPORT', "AI incident report updated", ip=ip)
            except Exception as e:
                logger.log_event('WARNING', 'ERROR', f"AI report generation failed: {e}", ip=ip)
        
        report_thread = threading.Thread(target=_generate_report_background, daemon=True)
        report_thread.start()
        
        logger.log_event('INFO', 'DISCONNECT', f"Connection closed from {ip}", ip=ip)
        try:
            if transport is not None:
                transport.close()
        except:
            pass


def main():
    """
    Start the honeypot server
    """
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                    NEURO-TRAP HONEYPOT                    ║
    ║              AI-Powered SSH Deception System              ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check if key exists
    if not os.path.exists(KEY_PATH):
        print(f"{Colors.RED}[ERROR] Server key not found!{Colors.RESET}")
        print(f"Run this first: python keys/generate_key.py")
        sys.exit(1)
    
    # Create server socket
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(100)
        server_socket.settimeout(1.0) # <--- Allow Ctrl+C to interrupt
    except PermissionError:
        print(f"{Colors.RED}[ERROR] Cannot bind to port {PORT}. Try running as administrator.{Colors.RESET}")
        sys.exit(1)
    except OSError as e:
        print(f"{Colors.RED}[ERROR] {e}{Colors.RESET}")
        sys.exit(1)
    
    logger.log_event('INFO', 'SYSTEM', f"Honeypot listening on {HOST}:{PORT}")
    logger.log_event('INFO', 'SYSTEM', "AI Engine: Llama 3.2 (3B) 🧠")
    logger.log_event('INFO', 'SYSTEM', "Waiting for attackers...")
    print(f"\n[+] Connect with: ssh root@localhost -p {PORT}\n")
    
    try:
        while True:
            try:
                # Check if server_socket has a connection ready (wait max 1s)
                readable, _, _ = select.select([server_socket], [], [], 1.0)
                
                if server_socket in readable:
                    client_socket, client_addr = server_socket.accept()
                    # Handle each connection in a new thread
                    thread = threading.Thread(target=handle_connection, args=(client_socket, client_addr))
                    thread.daemon = True
                    thread.start()
                
            except socket.timeout:
                continue # Check for KeyboardInterrupt
            except OSError:
                break
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()
