# Neuro-Trap Honeypot

An AI-powered SSH honeypot that uses Llama 3 to generate dynamic, realistic responses.

## Quick Start

```bash
# 1. Generate SSH key (one time only)
python keys/generate_key.py

# 2. Run the honeypot
python server/server.py

# 3. Test connection (from another terminal)
ssh root@localhost -p 2222
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
