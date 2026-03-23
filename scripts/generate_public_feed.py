"""
Neuro-Trap Data Generator for Public Threat Intel Feed
This script runs automatically inside GitHub Actions every hour.
It fetches the latest attacks from MongoDB and compiles them into a clean JSON for the static site.
"""
import os
import json
from collections import Counter
from datetime import datetime
from pymongo import MongoClient

def generate_feed():
    uri = os.environ.get('MONGODB_URI')
    if not uri:
        print("WARNING: MONGODB_URI not set. Using dummy data for testing.")
        # Generate dummy data if testing locally without the URI
        total_attacks = 14529
        top_ips = [("192.168.1.100", 500), ("8.8.8.8", 340)]
        top_creds = [("root:admin", 120), ("admin:12345", 90)]
        recent_events = [
            {"timestamp": datetime.utcnow().isoformat() + "Z", "ip": "1.2.3.4", "type": "login_attempt", "details": "root"}
        ]
    else:
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            db = client['neurotrap']
            events_coll = db['events']
            profiles_coll = db['attacker_profiles']

            # Fetch events
            events = list(events_coll.find().sort('timestamp', -1).limit(2000))
            total_attacks = events_coll.count_documents({})

            ips = [e.get('attacker_ip') for e in events if e.get('attacker_ip')]
            top_ips = Counter(ips).most_common(10)

            creds = [f"{e.get('username', 'root')}:{e.get('password', '')}" 
                     for e in events if e.get('event_type') == 'login_attempt']
            top_creds = Counter(creds).most_common(10)

            # --- Timeseries Data (Attacks per hour) ---
            from collections import defaultdict
            timeseries = defaultdict(int)
            for e in events:
                ts = e.get('timestamp')
                if ts:
                    try:
                        # Extract YYYY-MM-DD HH
                        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        hour_str = dt.strftime("%Y-%m-%d %H:00")
                        timeseries[hour_str] += 1
                    except:
                        pass
            
            # Sort by time, take last 24
            sorted_times = sorted(timeseries.keys())[-24:]
            attacks_over_time = [{'time': t, 'count': timeseries[t]} for t in sorted_times]

            # --- Threat Levels & Geo (From Profiles) ---
            profiles = list(profiles_coll.find().limit(1000))
            threats = [p.get('threat_level', 'LOW') for p in profiles]
            threat_distribution = Counter(threats)

            countries = []
            for p in profiles:
                geo = p.get('geo_location', {})
                if isinstance(geo, dict):
                    c = geo.get('country', 'Unknown')
                    if c != 'Unknown' and c != 'Local Network':
                        countries.append(c)
            top_countries = Counter(countries).most_common(5)

            recent_events = []
            for e in events[:20]:
                recent_events.append({
                    'timestamp': e.get('timestamp'),
                    'ip': e.get('attacker_ip', 'Unknown'),
                    'type': e.get('event_type', 'unknown'),
                    'details': e.get('command', '') or e.get('username', '')
                })
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error querying MongoDB: {e}")
            return

    data = {
        'last_updated': datetime.utcnow().isoformat() + "Z",
        'total_attacks': total_attacks,
        'top_ips': [{'ip': ip, 'count': c_} for ip, c_ in top_ips],
        'top_creds': [{'cred': cred, 'count': c_} for cred, c_ in top_creds],
        'attacks_over_time': attacks_over_time,
        'threat_distribution': dict(threat_distribution),
        'top_countries': [{'country': c, 'count': cnt} for c, cnt in top_countries],
        'recent_events': recent_events
    }

    # Ensure output dir exists
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public_web')
    os.makedirs(out_dir, exist_ok=True)
    
    out_file = os.path.join(out_dir, 'data.json')
    with open(out_file, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"Successfully generated {out_file} with {total_attacks} total attacks.")

if __name__ == '__main__':
    generate_feed()
