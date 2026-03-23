"""
MongoDB Client for Neuro-Trap
Handles the connection to MongoDB Atlas.
"""
import os
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError

# MongoDB Atlas Connection String
MONGO_URI = os.environ.get(
    "MONGODB_URI", 
    "mongodb+srv://placeholder:placeholder@neurotrap.tbtmk51.mongodb.net/?appName=neurotrap"
)

DB_NAME = "neurotrap"

_client = None
_db = None

def get_client():
    """Returns the MongoClient instance, initializing it if necessary."""
    global _client
    if _client is None:
        try:
            # certifi.where() fixes common SSL cert issues on Windows
            _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
            # Force a connection test
            _client.admin.command('ping')
        except (ConnectionFailure, ConfigurationError, Exception) as e:
            print(f"[!] MongoDB Connection Error: {e}")
            _client = None
    return _client

def get_db():
    """Returns the neurotrap database instance, or None if connection fails."""
    global _db
    if _db is None:
        client = get_client()
        if client:
            _db = client[DB_NAME]
    return _db

def get_events_col():
    """Returns the events collection, or None if connection fails."""
    db = get_db()
    if db is not None:
        return db.events
    return None

def get_profiles_col():
    """Returns the attacker_profiles collection, or None if connection fails."""
    db = get_db()
    if db is not None:
        return db.attacker_profiles
    return None

def test_connection():
    """Test function to quickly verify the DB connection."""
    client = get_client()
    if client:
        print("✅ Successfully connected to MongoDB Atlas!")
        db = get_db()
        print(f"✅ Selected database: {db.name}")
        return True
    else:
        print("❌ Failed to connect to MongoDB Atlas.")
        return False

if __name__ == "__main__":
    test_connection()
