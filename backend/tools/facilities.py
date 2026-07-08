import sqlite3
from typing import Dict, List, Any, Optional
from backend.config import DB_PATH


def get_facility(facility_type: str, near_section: Optional[int] = None) -> Dict[str, Any]:
    """Finds the nearest facility of a specific type.

    Finds facilities of the specified type (e.g., toilet, concession, medical,
    prayer, elevator). If near_section is provided, the results are sorted
    numerically by proximity to that section number.

    Args:
        facility_type: Type of facility to find.
        near_section: Optional stadium section number the user is near.

    Returns:
        A dictionary containing the facility type and a list of matching
        facilities, or an error message if none are found.
    """
    if not facility_type:
        return {"error": "Facility type must be specified."}

    facility_type_clean: str = facility_type.strip().lower()

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

    facilities_list: List[Dict[str, Any]] = []
    for name, f_type, level, section, is_accessible, status in rows:
        facilities_list.append({
            "name": name,
            "type": f_type,
            "level": level,
            "section": section,
            "is_accessible": bool(is_accessible),
            "status": status,
        })

    if near_section is not None:
        try:
            target_sec: int = int(near_section)
            # Sort by absolute distance between section numbers
            facilities_list.sort(key=lambda f: abs(f["section"] - target_sec))
        except ValueError:
            pass  # ignore invalid section conversion

    return {
        "facility_type": facility_type_clean,
        "results": facilities_list,
    }
