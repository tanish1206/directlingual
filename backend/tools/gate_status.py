import sqlite3
import os
import time

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "venue.db")

# Cache format: { gate_name: (expiry_timestamp, result_dict) }
_gate_cache = {}
CACHE_TTL_SECONDS = 30

def get_gate_status(gate_name: str) -> dict:
    """
    Fetches the status and current wait times for a specified gate.
    Uses a local thread-safe/in-memory cache with 30s TTL.
    """
    if not gate_name:
        return {"error": "Gate name must be specified."}

    gate_name_clean = gate_name.strip()
    now = time.time()
    
    # Check cache
    cache_key = gate_name_clean.lower()
    if cache_key in _gate_cache:
        expiry, cached_res = _gate_cache[cache_key]
        if now < expiry:
            return {**cached_res, "cached": True}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, status, wait_time_minutes, location_description 
        FROM gates 
        WHERE LOWER(name) = LOWER(?)
    """, (gate_name_clean,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        res = {
            "name": row[0],
            "status": row[1],
            "wait_time_minutes": row[2],
            "location_description": row[3],
            "cached": False
        }
        # Update cache
        _gate_cache[cache_key] = (now + CACHE_TTL_SECONDS, res)
        return res
        
    # Check with prefix/fuzzy match
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, status, wait_time_minutes, location_description FROM gates")
    all_gates = cursor.fetchall()
    conn.close()
    
    for name, status, wait, desc in all_gates:
        if gate_name_clean.lower() in name.lower() or name.lower() in gate_name_clean.lower():
            res = {
                "name": name,
                "status": status,
                "wait_time_minutes": wait,
                "location_description": desc,
                "cached": False
            }
            _gate_cache[name.lower()] = (now + CACHE_TTL_SECONDS, res)
            return res
            
    return {"error": f"Gate '{gate_name}' not found."}
