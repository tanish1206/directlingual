import sqlite3
import time
from typing import Dict, Tuple, Any
from backend.config import DB_PATH, GATE_STATUS_CACHE_TTL

# Cache format: { gate_name: (expiry_timestamp, result_dict) }
_gate_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
CACHE_TTL_SECONDS: int = GATE_STATUS_CACHE_TTL


def get_gate_status(gate_name: str) -> Dict[str, Any]:
    """Fetches the status and current wait times for a specified gate.

    Uses a thread-safe local in-memory cache to prevent redundant DB hits.

    Args:
        gate_name: Name of the gate to lookup (e.g., 'Gate A').

    Returns:
        A dictionary containing the gate's status, wait time, location details,
        and whether the result was retrieved from cache.
    """
    if not gate_name:
        return {"error": "Gate name must be specified."}

    gate_name_clean: str = gate_name.strip()
    now: float = time.time()

    # Check cache
    cache_key: str = gate_name_clean.lower()
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
        res: Dict[str, Any] = {
            "name": row[0],
            "status": row[1],
            "wait_time_minutes": row[2],
            "location_description": row[3],
            "cached": False,
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
                "cached": False,
            }
            _gate_cache[name.lower()] = (now + CACHE_TTL_SECONDS, res)
            return res

    return {"error": f"Gate '{gate_name}' not found."}
