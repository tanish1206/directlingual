import sqlite3
from typing import Dict, Any
from backend.config import DB_PATH


def get_route(start: str, end: str) -> Dict[str, Any]:
    """Retrieves route directions between two nodes in the venue.

    Supports standard path instructions and step-free/wheelchair-accessible paths.

    Args:
        start: Name of the starting location (e.g., 'Gate A').
        end: Name of the destination location (e.g., 'Section 215').

    Returns:
        A dictionary containing the start node, end node, standard route,
        step-free route, and distance in meters, or an error message.
    """
    if not start or not end:
        return {"error": "Both start and end points must be specified."}
        
    start_clean: str = start.strip()
    end_clean: str = end.strip()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Try exact match first
    cursor.execute("""
        SELECT start_node, end_node, path_instructions, step_free_instructions, distance_meters 
        FROM routes 
        WHERE LOWER(start_node) = LOWER(?) AND LOWER(end_node) = LOWER(?)
    """, (start_clean, end_clean))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "start": row[0],
            "end": row[1],
            "standard_route": row[2],
            "step_free_route": row[3],
            "distance_meters": row[4],
        }
    
    # Fallback to fuzzy starts/ends (e.g. "Gate A" instead of "gate a")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT start_node, end_node, path_instructions, step_free_instructions, distance_meters 
        FROM routes
    """)
    all_routes = cursor.fetchall()
    conn.close()
    
    for r_start, r_end, path, step_free, dist in all_routes:
        start_match: bool = (start_clean.lower() in r_start.lower() or r_start.lower() in start_clean.lower())
        end_match: bool = (end_clean.lower() in r_end.lower() or r_end.lower() in end_clean.lower())
        if start_match and end_match:
            return {
                "start": r_start,
                "end": r_end,
                "standard_route": path,
                "step_free_route": step_free,
                "distance_meters": dist,
            }
            
    return {
        "error": f"No route found between '{start}' and '{end}'. Please ask staff or check the physical maps."
    }
