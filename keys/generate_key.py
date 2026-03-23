"""
Generate RSA Host Key for SSH Server
Run this once before starting the server.
"""
import paramiko
import os

# Get the keys directory (one level up from this script)
KEYS_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(KEYS_DIR, "server_key")

def generate_key():
    print("[*] Generating RSA Host Key...")
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(KEY_PATH)
    print(f"[+] Key saved to: {KEY_PATH}")
    print("[+] Done! You can now run the server.")

if __name__ == "__main__":
    if os.path.exists(KEY_PATH):
        print(f"[!] Key already exists at {KEY_PATH}")
        response = input("Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            exit(0)
    generate_key()
