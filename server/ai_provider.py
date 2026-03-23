"""
Hybrid AI Provider — Groq Cloud + Ollama Local Fallback
Neuro-Trap Cyber Immune System

Strategy:
  1. TRY Groq Cloud API (Llama 3.2, blazing fast, free tier)
  2. FALLBACK to local Ollama (offline mode)
  3. FALLBACK to hardcoded responses (both down)

This ensures the honeypot NEVER crashes due to AI being unavailable.
"""
import os
import json
import time
import requests

# ============================================================
# CONFIGURATION
# ============================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # Fast 8B model, available on Groq free tier

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"

# Track which provider is active (for dashboard health display)
_active_provider = "initializing"
_last_error = None
_groq_calls = 0
_ollama_calls = 0
_fallback_calls = 0

# ============================================================
# PROVIDER STATUS (for dashboard)
# ============================================================

def get_provider_status():
    """Return current AI provider status for dashboard health check."""
    return {
        "active_provider": _active_provider,
        "groq_available": _check_groq_available(),
        "ollama_available": _check_ollama_available(),
        "groq_calls": _groq_calls,
        "ollama_calls": _ollama_calls,
        "fallback_calls": _fallback_calls,
        "last_error": _last_error,
    }


def _check_groq_available():
    """Quick check if Groq API is reachable."""
    if not GROQ_API_KEY:
        return False
    try:
        r = requests.get("https://api.groq.com/openai/v1/models",
                         headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                         timeout=3)
        return r.status_code == 200
    except:
        return False


def _check_ollama_available():
    """Quick check if local Ollama is running."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return r.status_code == 200
    except:
        return False


# ============================================================
# CORE: HYBRID CHAT FUNCTION
# ============================================================

def chat(messages, model_override=None):
    """
    Send a chat completion request.
    
    Tries Groq first (fast, cloud), falls back to Ollama (local).
    
    Args:
        messages: List of dicts with 'role' and 'content' keys
                  (OpenAI-compatible format)
        model_override: Optional model name override
    
    Returns:
        str: The AI response text
    """
    global _active_provider, _last_error, _groq_calls, _ollama_calls, _fallback_calls

    # --- ATTEMPT 1: Groq Cloud API ---
    if GROQ_API_KEY:
        try:
            response = _call_groq(messages, model_override)
            _active_provider = "groq"
            _groq_calls += 1
            return response
        except Exception as e:
            _last_error = f"Groq: {str(e)}"

    # --- ATTEMPT 2: Local Ollama ---
    try:
        response = _call_ollama(messages, model_override)
        _active_provider = "ollama"
        _ollama_calls += 1
        return response
    except Exception as e:
        _last_error = f"Ollama: {str(e)}"

    # --- ATTEMPT 3: Hardcoded fallback ---
    _active_provider = "fallback"
    _fallback_calls += 1
    return None  # Caller handles the None case


def _call_groq(messages, model_override=None):
    """Call Groq Cloud API (OpenAI-compatible)."""
    model = model_override or GROQ_MODEL
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
        "stream": False,
    }
    
    response = requests.post(
        GROQ_API_URL,
        headers=headers,
        json=payload,
        timeout=15
    )
    
    if response.status_code == 429:
        # Rate limited — fall through to Ollama
        raise Exception("Rate limited (429)")
    
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def _call_ollama(messages, model_override=None):
    """Call local Ollama instance."""
    import ollama
    model = model_override or OLLAMA_MODEL
    response = ollama.chat(model=model, messages=messages)
    return response['message']['content']


# ============================================================
# CONVENIENCE: Direct prompt (simpler API)
# ============================================================

def generate(system_prompt, user_prompt, model_override=None):
    """
    Simple API: provide system prompt + user prompt, get response.
    
    Args:
        system_prompt: The system/persona instruction
        user_prompt: The user's input
        model_override: Optional model override
    
    Returns:
        str or None: AI response, or None if all providers fail
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return chat(messages, model_override)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  NEURO-TRAP AI PROVIDER TEST")
    print("=" * 50)
    
    # Test provider availability
    print(f"\n[*] Groq API Key: {'SET' if GROQ_API_KEY else 'NOT SET'}")
    print(f"[*] Groq Available: {_check_groq_available()}")
    print(f"[*] Ollama Available: {_check_ollama_available()}")
    
    # Test a command
    print("\n[*] Testing: 'ls /root'...")
    result = generate(
        "You are a Linux terminal. Output only what the command would produce.",
        "The user typed: 'ls /root'. Generate the terminal output."
    )
    
    if result:
        print(f"[+] Provider: {_active_provider}")
        print(f"[+] Response:\n{result}")
    else:
        print("[!] All providers failed.")
    
    print(f"\n[*] Stats: Groq={_groq_calls}, Ollama={_ollama_calls}, Fallback={_fallback_calls}")
