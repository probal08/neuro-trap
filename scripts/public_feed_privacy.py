"""Privacy utilities for safe public threat-feed publishing."""

from __future__ import annotations

import copy
import ipaddress
import re
from typing import Any, Dict, List

_TRUE_VALUES = {"1", "true", "yes", "on"}
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_LOGIN_RE = re.compile(r"(Login attempt:\s*)([^:\s]+):([^\s]+)", re.IGNORECASE)


def env_bool(value: Any, default: bool = False) -> bool:
    """Parse common truthy strings for environment-based flags."""
    if value is None:
        return default
    return str(value).strip().lower() in _TRUE_VALUES


def is_public_indicator_ip(ip: str) -> bool:
    """Return True only for globally routable IP addresses."""
    if not ip or ip in {"unknown", "N/A", "local"}:
        return False
    try:
        parsed = ipaddress.ip_address(ip)
    except ValueError:
        return False

    if parsed.is_private or parsed.is_loopback or parsed.is_link_local:
        return False
    if parsed.is_multicast or parsed.is_reserved or parsed.is_unspecified:
        return False
    return True


def mask_ip(ip: str) -> str:
    """Mask IP while retaining coarse network shape for analytics visuals."""
    if not ip:
        return "masked"
    try:
        parsed = ipaddress.ip_address(ip)
        if isinstance(parsed, ipaddress.IPv4Address):
            octets = ip.split(".")
            return f"{octets[0]}.{octets[1]}.*.*"
        groups = parsed.exploded.split(":")
        return f"{groups[0]}:{groups[1]}:*:*:*:*:*:*"
    except ValueError:
        return "masked"


def mask_secret(secret: str) -> str:
    """Mask potentially sensitive values while preserving rough frequency context."""
    if not secret:
        return "-"
    if len(secret) <= 2:
        return "*" * len(secret)
    return secret[:2] + "*" * max(3, len(secret) - 2)


def sanitize_message(message: str) -> str:
    """Redact IP addresses and captured password pairs from event text."""
    if not message:
        return ""
    sanitized = _IPV4_RE.sub(lambda m: mask_ip(m.group(0)), message)
    sanitized = _LOGIN_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}:[redacted]", sanitized)
    return sanitized[:180]


def sanitize_public_payload(
    payload: Dict[str, Any],
    include_replay: bool = False,
    include_event_details: bool = False,
) -> Dict[str, Any]:
    """Return a privacy-safe copy of a public dashboard payload."""
    data = copy.deepcopy(payload)

    def sanitize_ip_records(records: List[Dict[str, Any]], ip_key: str = "ip") -> List[Dict[str, Any]]:
        sanitized: List[Dict[str, Any]] = []
        for item in records or []:
            raw_ip = str(item.get(ip_key, "")).strip()
            if not is_public_indicator_ip(raw_ip):
                continue
            item[ip_key] = mask_ip(raw_ip)
            sanitized.append(item)
        return sanitized

    data["top_ips"] = sanitize_ip_records(data.get("top_ips", []))
    data["blocked_ips"] = sanitize_ip_records(data.get("blocked_ips", []))
    data["monitored_ips"] = sanitize_ip_records(data.get("monitored_ips", []))
    data["profiles"] = sanitize_ip_records(data.get("profiles", []))

    for profile in data.get("profiles", []):
        profile.pop("dna", None)
        profile.pop("bio_hash", None)

    for point in data.get("globe_points", []):
        raw_ip = str(point.get("ip", "")).strip()
        if is_public_indicator_ip(raw_ip):
            point["ip"] = mask_ip(raw_ip)

    safe_creds: List[Dict[str, Any]] = []
    for item in data.get("top_creds", []):
        cred = str(item.get("cred", ""))
        username = cred.split(":", 1)[0] if ":" in cred else "user"
        safe_creds.append({"cred": f"{username}:[redacted]", "count": item.get("count", 0)})
    data["top_creds"] = safe_creds

    for item in data.get("top_passwords", []):
        item["password"] = mask_secret(str(item.get("password", "")))
    if "top_pass" in data:
        data["top_pass"] = mask_secret(str(data.get("top_pass", "")))

    sanitized_events: List[Dict[str, Any]] = []
    for event in data.get("recent_events", []):
        raw_ip = str(event.get("ip", "")).strip()
        if not is_public_indicator_ip(raw_ip):
            continue
        sanitized_events.append(
            {
                "timestamp": event.get("timestamp", ""),
                "type": event.get("type", "UNKNOWN"),
                "ip": mask_ip(raw_ip),
                "message": sanitize_message(str(event.get("message", ""))),
                "details": str(event.get("details", ""))[:120] if include_event_details else "",
            }
        )
    data["recent_events"] = sanitized_events[:200]

    if include_replay:
        safe_replay = []
        for session in data.get("replay_sessions", []):
            raw_ip = str(session.get("ip", "")).strip()
            if not is_public_indicator_ip(raw_ip):
                continue
            commands = []
            for cmd in session.get("commands", []):
                commands.append(
                    {
                        "command": "[redacted-command]",
                        "time": cmd.get("time", ""),
                    }
                )
            safe_replay.append({"ip": mask_ip(raw_ip), "commands": commands})
        data["replay_sessions"] = safe_replay[:5]
    else:
        data["replay_sessions"] = []

    data["monitored_ips_count"] = len(data.get("monitored_ips", []))
    data["privacy_mode"] = "sanitized"
    data["privacy_notice"] = "Sensitive attacker identifiers and credentials are redacted for public display."
    return data
