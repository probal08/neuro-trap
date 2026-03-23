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

            # Fetch recent events
            events = list(events_coll.find().sort('timestamp', -1).limit(1000))
            total_attacks = events_coll.count_documents({})

            ips = [e.get('attacker_ip') for e in events if e.get('attacker_ip')]
            top_ips = Counter(ips).most_common(10)

            creds = [f"{e.get('username', 'root')}:{e.get('password', '')}" 
                     for e in events if e.get('event_type') == 'login_attempt']
            top_creds = Counter(creds).most_common(10)

            recent_events = []
            for e in events[:20]:
                recent_events.append({
                    'timestamp': e.get('timestamp'),
                    'ip': e.get('attacker_ip', 'Unknown'),
                    'type': e.get('event_type', 'unknown'),
                    'details': e.get('command', '') or e.get('username', '')
                })
        except Exception as e:
            print(f"Error querying MongoDB: {e}")
            return

    data = {
        'last_updated': datetime.utcnow().isoformat() + "Z",
        'total_attacks': total_attacks,
        'top_ips': [{'ip': ip, 'count': c_} for ip, c_ in top_ips],
        'top_creds': [{'cred': cred, 'count': c_} for cred, c_ in top_creds],
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
