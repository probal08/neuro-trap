"""
Virtual Filesystem for Neuro-Trap
Provides consistent, stateful storage for the honeypot.
Handles: ls, cd, pwd, mkdir, touch
"""
import os
import posixpath  # Use posixpath for Linux-style paths (/) even on Windows
import json

SAVE_FILE = os.path.join(os.path.dirname(__file__), 'fs_state.json')
FS_VERSION = 3  # Bump this when default filesystem changes to invalidate old state

class VirtualFS:
    def __init__(self):
        self.fs = self._load_state()
        self.current_path = '/root'

    def _load_state(self):
        """Load filesystem state from JSON file if it exists and version matches"""
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r') as f:
                    data = json.load(f)
                # Check version — discard old state if structure has changed
                if data.get('_fs_version') == FS_VERSION:
                    return data
                else:
                    print("[INFO] Filesystem upgraded — loading fresh bait files")
            except Exception as e:
                print(f"[WARN] Failed to load FS state: {e}")
        
        # Default state if no save file
        return {
            'root': {
                'Desktop': {},
                'Documents': {
                    'project_notes.txt': 'Confidential project details...',
                    'passwords.txt': 'admin:12345',
                    'passwords.pdf': '[RADIOACTIVE_TOKEN]',  # Module 15: Bait file
                    'company_financials.xlsx': '[Protected spreadsheet — use LibreOffice]',
                    'important.txt': '========================================\nCONFIDENTIAL - INTERNAL SETTINGS ONLY\n========================================\n\nDB_HOST=192.168.1.100\nDB_USER=root\nDB_PASS=P@ssw0rd2024!_secure\nDB_NAME=production_db\n\nSTRIPE_API_KEY=sk_live_51Mabcde12345XYZ...\nAWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\nAWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n\nADMIN_PORTAL=https://admin.company.internal/login\nNOTE: DO NOT SHARE THIS DOCUMENT WITH ANYONE OUTSIDE DEVOPS.',
                },
                'Downloads': {},
                'secret_data': {
                    'backup_credentials.txt': 'AWS Key: AKIA5EXAMPLE\\nSecret: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
                    'vpn_config.ovpn': 'client\\ndev tun\\nproto udp\\nremote vpn.company.com 1194',
                },
                '.bash_history': '',
                '.bashrc': '# ~/.bashrc: executed by bash(1) for non-login shells.\\n',
                '.ssh': {
                    'known_hosts': '10.0.0.5 ssh-rsa AAAAB3NzaC1yc2EAAAADAQAB...\\n10.0.0.10 ssh-rsa AAAAB3NzaC1yc2EAAAADAQAB...\\n192.168.1.100 ssh-rsa AAAAB3NzaC1yc2EAAAADAQAB...',
                    'config': 'Host database-server\\n  HostName 10.0.0.5\\n  User admin\\n\\nHost web-server\\n  HostName 10.0.0.10\\n  User root\\n\\nHost backup-node\\n  HostName 10.0.0.15\\n  User backup',
                },
            },
            'etc': {
                'passwd': 'root:x:0:0:root:/root:/bin/bash\nuser:x:1000:1000:user:/home/user:/bin/bash',
                'hostname': 'production-server'
            },
            'var': {
                'log': {
                    'syslog': 'Jan 10 10:00:00 server systemd[1]: Started Session 1 of user root.',
                    'auth.log': 'Jan 10 10:00:00 server sshd[123]: Accepted password for root'
                }
            },
            'home': {
                'user': {}
            },
            '_fs_version': FS_VERSION
        }

    def _save_state(self):
        """Save filesystem state to JSON file"""
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(self.fs, f, indent=4)
        except Exception as e:
            print(f"[WARN] Failed to save FS state: {e}")



    def _get_node(self, path):
        """Helper to navigate to a specific node in the FS dict"""
        if path == '/':
            return self.fs
        
        parts = [p for p in path.split('/') if p]
        current = self.fs
        
        # Handle root path specially if needed, but our FS starts at keys like 'root', 'etc'
        # To make it simpler, we'll treat self.fs as the contents of '/'
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _resolve_path(self, path):
        """Resolve absolute or relative paths to absolute"""
        if path.startswith('/'):
            return posixpath.normpath(path)
        return posixpath.normpath(posixpath.join(self.current_path, path))

    def get_pwd(self):
        return self.current_path

    def change_dir(self, path):
        target_path = self._resolve_path(path)
        
        # Virtual root check
        if target_path == '/':
            self.current_path = '/'
            return ""
            
        # Get the node (skip first slash for internal lookup)
        # Internal structure keys are top level: 'root', 'etc'
        # So /root -> look for 'root' in self.fs
        
        lookup_path = target_path.strip('/')
        node = self._get_node(lookup_path)
        
        if node is not None and isinstance(node, dict):
            self.current_path = target_path
            return ""
        else:
            return f"-bash: cd: {path}: No such file or directory"

    def list_dir(self, args_str='.'):
        # Parse flags
        flags = []
        path = '.'
        for arg in args_str.split():
            if arg.startswith('-'):
                flags.extend(list(arg[1:]))
            else:
                path = arg
                
        show_all = 'a' in flags
        show_long = 'l' in flags

        target_path = self._resolve_path(path)
        
        if target_path == '/':
            node = self.fs
        else:
            lookup_path = target_path.strip('/')
            node = self._get_node(lookup_path)
        
        if node is None:
            return f"ls: cannot access '{path}': No such file or directory"
        
        def format_item(name, item_node):
            if not show_long:
                return name
                
            # Fake realistic stats
            is_dir = isinstance(item_node, dict)
            perms = "drwxr-xr-x" if is_dir else "-rw-r--r--"
            links = "2" if is_dir else "1"
            owner = "root"
            group = "root"
            
            # Special ownership for certain files
            if target_path.startswith('/home/user'):
                owner = "user"
                group = "user"
                
            size = "4096" if is_dir else str(len(str(item_node)))
            date = "Feb 10 10:00" # Static for realism, could be dynamic
            
            return f"{perms} {links:>2} {owner:<5} {group:<5} {size:>5} {date} {name}"

        if isinstance(node, dict):
            items = []
            if show_all:
                items.append(format_item('.', node))
                items.append(format_item('..', {})) # Mock parent
            
            for k, v in node.items():
                if not show_all and k.startswith('.'):
                    continue
                items.append(format_item(k, v))
                
            if show_long:
                # Add "total X" line for realistic ls -l
                total = sum(4 for _ in items) # Fake block size
                return f"total {total}\n" + "\n".join(items)
            else:
                return "  ".join(items) # Space separated for normal ls
        else:
            # It's a file
            return format_item(posixpath.basename(target_path), node)

    def make_dir(self, path):
        target_path = self._resolve_path(path)
        parent_path = posixpath.dirname(target_path)
        dirname = posixpath.basename(target_path)
        
        if parent_path == '/':
            parent_node = self.fs
        else:
            parent_node = self._get_node(parent_path.strip('/'))
            
        if parent_node is not None and isinstance(parent_node, dict):
            if dirname in parent_node:
                return f"mkdir: cannot create directory '{path}': File exists"
            parent_node[dirname] = {}
            self._save_state()
            return "" # Success
        else:
            return f"mkdir: cannot create directory '{path}': No such file or directory"

    def touch(self, path):
        target_path = self._resolve_path(path)
        parent_path = posixpath.dirname(target_path)
        filename = posixpath.basename(target_path)
        
        if parent_path == '/':
            parent_node = self.fs
        else:
            parent_node = self._get_node(parent_path.strip('/'))
            
        if parent_node is not None and isinstance(parent_node, dict):
            # If exists, update timestamp (in a real FS), here just ensure existence
            if filename not in parent_node:
                parent_node[filename] = "" 
                self._save_state()
            return ""
        else:
            return f"touch: cannot touch '{path}': No such file or directory"

    def read_file(self, path):
        """Read content for 'cat' command if file exists in virtual FS"""
        target_path = self._resolve_path(path)
        lookup_path = target_path.strip('/')
        node = self._get_node(lookup_path)
        
        if node is not None and not isinstance(node, dict):
            return node
        return None  # Return None so AI handles it if not found/empty

    def write_file(self, path, content):
        """Write content to a file (echo "text" > file)"""
        target_path = self._resolve_path(path)
        parent_path = posixpath.dirname(target_path)
        filename = posixpath.basename(target_path)
        
        if parent_path == '/':
            parent_node = self.fs
        else:
            parent_node = self._get_node(parent_path.strip('/'))
            
        if parent_node is not None and isinstance(parent_node, dict):
            parent_node[filename] = content
            self._save_state()
            return ""
        else:
            return f"bash: {path}: No such file or directory"

    def remove_path(self, path, recursive=False):
        """Remove a file or directory"""
        target_path = self._resolve_path(path)
        parent_path = posixpath.dirname(target_path)
        target_name = posixpath.basename(target_path)
        
        if parent_path == '/':
            parent_node = self.fs
        else:
            parent_node = self._get_node(parent_path.strip('/'))
            
        if parent_node is not None and isinstance(parent_node, dict):
            if target_name in parent_node:
                node = parent_node[target_name]
                if isinstance(node, dict) and not recursive:
                    if len(node) > 0:
                        return f"rm: cannot remove '{path}': Is a directory"
                del parent_node[target_name]
                self._save_state()
                return ""
            else:
                return f"rm: cannot remove '{path}': No such file or directory"
        return f"rm: cannot remove '{path}': No such file or directory"

