# Neuro-Trap Honeypot

An AI-powered SSH honeypot that uses Llama 3 to generate dynamic, realistic responses.

## Security Defaults

- Secrets are expected via environment variables, not hardcoded in source.
- Copy `.env.example` to `.env` for local runs.
- Public feed generation now redacts sensitive attacker identifiers and credentials by default.

### Public Feed Privacy Flags

- `NEUROTRAP_PUBLIC_INCLUDE_REPLAY=false` (default)
- `NEUROTRAP_PUBLIC_INCLUDE_EVENT_DETAILS=false` (default)

Set either flag to `true` only for trusted private environments.

## Quick Start

```bash
# 1. Generate SSH key (one time only)
python keys/generate_key.py

# 2. Run the honeypot
python server/server.py

# 3. Test connection (from another terminal)
ssh root@localhost -p 2222

# 4. Generate public feed (sanitized by default)
python scripts/generate_public_feed.py

# 5. Run security preflight checks
python scripts/security_preflight.py
```

### Windows PowerShell Tip

If your path has spaces, run Python executables with quotes and the call operator:

```powershell
& "D:/End sem project_honeypot/.venv/Scripts/python.exe" -m pip install --upgrade pip
```

## Quality Checks

```bash
# Run unit tests
python -m pytest tests -q
```

## Project Structure

```
neuro-trap/
├── server/         # SSH server code
├── logging/        # Attack logging
├── dashboard/      # Streamlit UI
├── data/logs/      # Log files
├── keys/           # SSH host key
└── tests/          # Unit tests
```
