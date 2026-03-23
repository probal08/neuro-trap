"""
Neuro-Trap Analytics Engine
Phase 2: Mathematical & Algorithmic Threat Analytics
Implements Modules 7, 8, 9, 10 without heavy ML libraries.
"""
import math
from collections import defaultdict, Counter
import pandas as pd
from datetime import datetime

# --- MODULE 8: Command Sequence Similarity Engine (Cosine Similarity) ---
# Hardcoded profile of a known malicious script sequence
MALICIOUS_PROFILE = ["wget", "chmod", "sh", "./", "curl", "python", "base64", "nc"]

def get_cosine_similarity(vec1, vec2):
    """Calculates Cosine Similarity mathematically between two frequency dictionaries."""
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    
    if not denominator:
        return 0.0
    return float(numerator) / denominator

def analyze_threats(df):
    """
    Main Analytics Pipeline handling Modules 7, 8, 9, 10.
    Expects a Pandas DataFrame built from honeypot.json.
    """
    results = []
    
    if df.empty or 'event_type' not in df.columns or 'ip' not in df.columns:
        return pd.DataFrame()

    # Filter only for COMMAND events to calculate typing speed and sequences
    command_df = df[df['event_type'] == 'COMMAND'].copy()
    if command_df.empty:
        return pd.DataFrame()

    command_df['timestamp'] = pd.to_datetime(command_df['timestamp'])
    
    # Analyze per IP address
    grouped = command_df.groupby('ip')
    
    for ip, group in grouped:
        # Sort chronologically
        group = group.sort_values(by='timestamp')
        
        # Extract commands from JSON details wrapper
        def extract_cmd(row):
            if isinstance(row, dict) and 'command' in row:
                return str(row['command']).split()[0] # Get base command
            elif isinstance(row, str):
                return row.split()[0]
            return "unknown"
            
        cmds = [extract_cmd(x) for x in group['details']]
        cmd_count = len(cmds)
        
        # --- MODULE 7: Time-Based Anomaly Detection (Bot vs Human) ---
        # Calculate time diffs between consecutive commands
        time_diffs = group['timestamp'].diff().dt.total_seconds().dropna()
        
        avg_speed = time_diffs.mean() if not time_diffs.empty else 0.0
        
        # 1000 IQ Logic: Humans type at ~50-80 WPM. Consecutive commands under 0.8s avg = BOT
        classification = "🤖 Botnet" if avg_speed < 0.8 and cmd_count > 3 else "👤 Human"
        if cmd_count < 2:
            classification = "⚠️ Insufficient Data"

        # --- MODULE 8: Cosine Similarity ---
        # Vectorize attacker commands
        attacker_vec = Counter(cmds)
        malicious_vec = Counter(MALICIOUS_PROFILE)
        
        similarity_score = get_cosine_similarity(attacker_vec, malicious_vec)
        threat_level = "CRITICAL 🚨" if similarity_score > 0.4 else "ELEVATED ⚠️" if similarity_score > 0.2 else "LOW 🟢"

        # --- MODULE 9: Behavioral Profiling (Standard Deviation) ---
        # Calculate standard deviation of command pacing
        std_dev = time_diffs.std() if not time_diffs.empty and len(time_diffs) > 1 else 0.0
        
        # High deviation = human pausing to think. Low deviation = scripted payload execution.
        behavior = "Scripted" if std_dev < 1.0 and cmd_count > 3 else "Erratic/Interactive"

        # Bundle results
        results.append({
            "IP Address": ip,
            "Total Commands": cmd_count,
            "Avg Speed (sec)": round(avg_speed, 2),
            "Pacing StdDev": round(std_dev, 2),
            "Classification": classification,
            "Behavior": behavior,
            "Malware Match (%)": round(similarity_score * 100, 1),
            "Threat Level": threat_level
        })

    return pd.DataFrame(results).sort_values(by="Malware Match (%)", ascending=False)


# --- MODULE 10: Predictive Attacker Modeling (Markov Chain) ---
def build_markov_chain(df):
    """
    Builds a transition probability matrix.
    Given command A, what is the probability of command B?
    """
    predictions = []
    if df.empty or 'event_type' not in df.columns:
        return pd.DataFrame()
        
    command_df = df[df['event_type'] == 'COMMAND']
    if command_df.empty:
        return pd.DataFrame()

    transitions = defaultdict(list)
    
    # Process sequences per IP
    grouped = command_df.groupby('ip')
    for ip, group in grouped:
        cmds = []
        for x in group['details']:
            if isinstance(x, dict) and 'command' in x:
                cmds.append(str(x['command']).split()[0])
            elif isinstance(x, str):
                cmds.append(x.split()[0])
                
        # Build pairs (A -> B)
        for i in range(len(cmds) - 1):
             transitions[cmds[i]].append(cmds[i+1])

    # Calculate probabilities
    for current_cmd, next_commands in transitions.items():
        total_transitions = len(next_commands)
        counts = Counter(next_commands)
        
        # Get the most likely next command
        most_likely, count = counts.most_common(1)[0]
        probability = (count / total_transitions) * 100
        
        predictions.append({
            "Current Command": current_cmd,
            "Most Probable Next Command": most_likely,
            "Probability": f"{probability:.1f}%",
            "Observations": total_transitions
        })
        
    # Return top 10 most confident predictions
    if predictions:
        pred_df = pd.DataFrame(predictions)
        return pred_df.sort_values(by="Observations", ascending=False).head(10)
    
    return pd.DataFrame()

