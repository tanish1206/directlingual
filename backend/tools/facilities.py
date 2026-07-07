import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "venue.db")

def get_facility(facility_type: str, near_section: int = None) -> dict:
    """
    Finds the nearest facility of a specific type (e.g., toilet, concession, medical, prayer, elevator).
    If near_section is provided, sorts by numerical distance to that section.
    """
    if not facility_type:
        return {"error": "Facility type must be specified."}
        
    facility_type_clean = facility_type.strip().lower()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, type, level, section, is_accessible, status 
        FROM facilities 
        WHERE LOWER(type) = LOWER(?)
    """, (facility_type_clean,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return {"error": f"No facilities found of type '{facility_type}'."}
        
    facilities_list = []
    for name, f_type, level, section, is_accessible, status in rows:
        facilities_list.append({
            "name": name,
            "type": f_type,
            "level": level,
            "section": section,
            "is_accessible": bool(is_accessible),
            "status": status
        })
        
    if near_section is not None:
        try:
            target_sec = int(near_section)
            # Sort by absolute distance between section numbers
            facilities_list.sort(key=lambda f: abs(f["section"] - target_sec))
        except ValueError:
            pass # ignore invalid section conversion

    return {
        "facility_type": facility_type_clean,
        "results": facilities_list
    }
