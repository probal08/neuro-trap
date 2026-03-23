"""
Simple key generator - run directly
"""
import paramiko

print("Generating key...")
key = paramiko.RSAKey.generate(2048)
key.write_private_key_file("server_key")
print("Done! server_key created.")
