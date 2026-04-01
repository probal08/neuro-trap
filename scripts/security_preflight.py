"""Quick security and operations preflight for Neuro-Trap."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _status(ok: bool, text: str) -> str:
    return f"[{'OK' if ok else 'WARN'}] {text}"


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    env_example_path = project_root / ".env.example"

    warnings = 0

    print("=" * 56)
    print("  NEURO-TRAP SECURITY PREFLIGHT")
    print("=" * 56)

    print(_status(env_example_path.exists(), ".env.example present"))
    if not env_example_path.exists():
        warnings += 1

    print(_status(env_path.exists(), ".env present for local runs"))
    if not env_path.exists():
        warnings += 1
    else:
        # Load .env for local preflight convenience.
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

    sentry_dsn = os.environ.get("NEUROTRAP_SENTRY_DSN", "").strip()
    print(_status(bool(sentry_dsn) or not os.environ.get("NEUROTRAP_SENTRY_DSN"), "Sentry DSN controlled via environment"))

    include_replay = os.environ.get("NEUROTRAP_PUBLIC_INCLUDE_REPLAY", "false").strip().lower() == "true"
    include_details = os.environ.get("NEUROTRAP_PUBLIC_INCLUDE_EVENT_DETAILS", "false").strip().lower() == "true"

    print(_status(not include_replay, "Public replay export disabled"))
    if include_replay:
        warnings += 1

    print(_status(not include_details, "Public event details export disabled"))
    if include_details:
        warnings += 1

    mongo_uri = os.environ.get("MONGODB_URI", "").strip()
    print(_status(bool(mongo_uri), "MONGODB_URI available in environment"))
    if not mongo_uri:
        warnings += 1

    print("=" * 56)
    if warnings:
        print(f"Preflight completed with {warnings} warning(s).")
        print("For production/public deployment, resolve warnings before publishing.")
        return 1

    print("Preflight passed with no warnings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
