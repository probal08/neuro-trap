"""
AI Engine for Neuro-Trap
Hybrid Mode: Groq Cloud (Primary) + Ollama Local (Fallback)

The engine uses ai_provider.py which automatically:
  1. Tries Groq Cloud API (Llama 3.2, ~500 tokens/sec)
  2. Falls back to local Ollama (offline mode)
  3. Falls back to hardcoded responses (both down)
"""
import ai_provider  # Hybrid Groq + Ollama provider

# Configuration
MODEL_NAME = "llama3.2"

# The System Prompt defines the AI's "Acting Role"
PERSONAS = {
    "DEFAULT": """
You are a Ubuntu 22.04 LTS Linux terminal. 
You are NOT an AI assistant. You do NOT explain things.
You ONLY output the exact text that the command would produce.
Current directory: /root
Current user: root
Hostname: production-server

Rules:
1. If the user runs 'ls', list fake files.
2. If the user runs 'cat', show fake content.
3. If the command is wrong, output: "-bash: [command]: command not found"
4. NEVER say "Here is the output". JUST THE OUTPUT.
5. Be concise. Real terminals are quiet.
""",
    "MYSQL": """
You are a MySQL Database command line interface.
You are currently connected as root.
Output results in standard ASCII table format typical of mysql.
If they type 'show databases;', list fake databases (wordpress, users, secret_db).
If they type a wrong query, return a realistic SQL syntax error.
""",
    "REDIS": """
You are a Redis datastore CLI.
Respond to commands like keys *, get, set, info with realistic redis-cli responses.
""",
    "APACHE": """
You are an Apache2 configuration terminal or shell reacting to web server commands.
""",
    "WINDOWS": """
You are a Windows Server 2019 Command Prompt (cmd.exe).
You are NOT an AI. You ONLY output what cmd.exe would output.
Current directory: C:\\Users\\Administrator
Hostname: WIN-PROD-SRV01

Rules:
1. If they type 'dir', list fake Windows files and folders with dates and sizes.
2. If they type 'ipconfig', show fake network adapters with realistic IPs.
3. If they type 'net user', list fake Windows user accounts.
4. If they type 'systeminfo', show realistic Windows Server 2019 system info.
5. Unknown commands: "'[command]' is not recognized as an internal or external command"
6. NEVER explain. JUST OUTPUT.
"""
}

def generate_response(command, context_history=[]):
    """
    Send command to AI (Groq Cloud → Ollama → Fallback) and get fake terminal output.
    """
    selected_persona = "DEFAULT"  # Bug 7 fix: Initialize before try
    try:
        # Module 11: Dynamic Persona Selection (Expanded for stateless SQL queries)
        cmd_lower = command.lower()
        
        # Check for Database/SQL keywords
        sql_keywords = ['mysql', 'sql', 'show databases', 'show tables', 'select ', 'insert ', 'update ', 'drop ', 'use ']
        if any(x in cmd_lower for x in sql_keywords):
            selected_persona = "MYSQL"
        elif 'redis' in cmd_lower:
            selected_persona = "REDIS"
        elif any(x in cmd_lower for x in ['apache', 'nginx', 'http']):
            selected_persona = "APACHE"
        # Module 16 (Chameleon): Auto-detect Windows commands
        elif any(x in cmd_lower for x in ['dir', 'ipconfig', 'net user', 'systeminfo', 'whoami /all', 'tasklist', 'netstat -an', 'type ', 'reg query']):
            selected_persona = "WINDOWS"

        # Call hybrid AI provider (Groq Cloud → Ollama → None)
        result = ai_provider.generate(
            PERSONAS[selected_persona],
            f"The user typed: '{command}'. Generate the terminal output."
        )
        
        if result is None:
            # Both Groq and Ollama are down — use hardcoded fallback
            return _hardcoded_fallback(command, selected_persona)
        
        # Cleanup: Remove markdown code blocks if the AI adds them
        clean_text = result.replace("```bash", "").replace("```sql", "").replace("```", "").strip()
        
        return clean_text

    except Exception as e:
        error_msg = str(e).lower()
        if "memory" in error_msg or "500" in error_msg:
            return _hardcoded_fallback(command, selected_persona)
        
        # Final fallback
        return f"-bash: {command.split()[0] if command else ''}: command not found"


def _hardcoded_fallback(command, persona):
    """Ultra-reliable fallback when all AI providers are down."""
    if persona == "MYSQL":
        return "ERROR 1045 (28000): Access denied for user 'root'@'localhost' (using password: NO)"
    elif persona == "REDIS":
        return "(error) NOAUTH Authentication required."
    elif persona == "APACHE":
        return "apache2: Could not reliably determine the server's fully qualified domain name."
    elif persona == "WINDOWS":
        cmd = command.split()[0] if command else 'cmd'
        return f"'{cmd}' is not recognized as an internal or external command,\noperable program or batch file."
    else:
        return f"-bash: {command.split()[0] if command else ''}: command not found"


def apply_cognitive_mirror(command, fs):
    """
    Module 30: Cognitive Mirror (Adaptive Deception)
    Analyzes hacker intent and dynamically injects targeted bait files 
    into their current environment to keep them trapped longer.
    """
    cmd_lower = command.lower()
    
    # Intent: Looking for databases / SQL
    if any(x in cmd_lower for x in ['mysql', 'sql', 'db', 'database', 'dump']):
        if fs.make_dir('/root/db_backups') == "":
            fs.write_file('/root/db_backups/production_users.sql', 'INSERT INTO users VALUES (1, "admin", "hashed_password_123");\n')
            fs.write_file('/root/db_backups/finance_q4.sql', 'INSERT INTO accounts VALUES (1001, 5000000.00);\n')

    # Intent: Looking for crypto / financial
    elif any(x in cmd_lower for x in ['bitcoin', 'crypto', 'wallet', 'btc', 'eth']):
        if fs.make_dir('/home/user/.bitcoin') == "":
            fs.write_file('/home/user/.bitcoin/wallet.dat', '[ENCRYPTED_WALLET_DATA_0x8283726]...\n')
            fs.write_file('/home/user/.bitcoin/seed_phrase.txt', 'abandon ability able about above absent absorb abstract absurd abuse access accident\n')

    # Intent: Looking for source code / IP
    elif any(x in cmd_lower for x in ['git', 'python', 'code', 'build', 'npm']):
        if fs.make_dir('/root/project_beta') == "":
            fs.write_file('/root/project_beta/config.py', 'API_KEY = "sk_live_123456789"\nDB_PASS = "super_secret"\n')
            fs.write_file('/root/project_beta/main.py', 'print("Proprietary Trading Algorithm v2.0")\n')

if __name__ == "__main__":
    # Test it directly
    print("Testing AI Engine (Hybrid: Groq Cloud + Ollama Fallback)...")
    print(f"Active Provider: {ai_provider.get_provider_status()['active_provider']}")
    cmd = "cat /etc/passwd"
    print(f"Command: {cmd}")
    print("Response:")
    print(generate_response(cmd))
    print(f"\nProvider used: {ai_provider.get_provider_status()['active_provider']}")
