import os
import sqlite3

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "venue.db")

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        status TEXT NOT NULL,          -- 'Open', 'Closed'
        wait_time_minutes INTEGER NOT NULL,
        location_description TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL,            -- 'toilet', 'concession', 'medical', 'prayer', 'elevator'
        level TEXT NOT NULL,           -- 'Concourse 1', 'Concourse 2', 'Upper Deck'
        section INTEGER NOT NULL,      -- nearest section number
        is_accessible INTEGER NOT NULL, -- 1 for True, 0 for False (wheelchair/step-free friendly)
        status TEXT NOT NULL           -- 'Open', 'Closed', 'Busy'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_node TEXT NOT NULL,
        end_node TEXT NOT NULL,
        path_instructions TEXT NOT NULL,
        step_free_instructions TEXT NOT NULL,
        distance_meters INTEGER NOT NULL,
        UNIQUE(start_node, end_node)
    )
    """)

    # Seed data
    # Gates
    gates_data = [
        ("Gate A", "Open", 10, "North entrance, closest to Section 101 and Section 140. Main public transport hub access."),
        ("Gate B", "Open", 25, "East entrance, closest to Section 110. Near general parking Lot B."),
        ("Gate C", "Open", 5, "South entrance, closest to Section 120. Nearest to the main rideshare drop-off point."),
        ("Gate D", "Closed", 0, "West entrance, closest to Section 130. Closed due to maintenance on perimeter fencing.")
    ]
    cursor.executemany("""
    INSERT OR REPLACE INTO gates (name, status, wait_time_minutes, location_description)
    VALUES (?, ?, ?, ?)
    """, gates_data)

    # Facilities
    facilities_data = [
        # Toilets
        ("Restroom 101", "toilet", "Concourse 1", 101, 1, "Open"),
        ("Restroom 112 (Accessible)", "toilet", "Concourse 1", 112, 1, "Open"),
        ("Restroom 120", "toilet", "Concourse 1", 120, 0, "Busy"),
        ("Restroom 122 (Accessible)", "toilet", "Concourse 1", 122, 1, "Open"),
        ("Restroom 204", "toilet", "Concourse 2", 204, 1, "Open"),
        # Concessions
        ("World Cup Burgers 105", "concession", "Concourse 1", 105, 1, "Open"),
        ("Taco Fiesta 115", "concession", "Concourse 1", 115, 1, "Open"),
        ("Global Hydration 128", "concession", "Concourse 1", 128, 0, "Open"),
        # Medical
        ("First Aid Station North", "medical", "Concourse 1", 102, 1, "Open"),
        ("First Aid Station South", "medical", "Concourse 1", 124, 1, "Open"),
        # Elevators
        ("Elevator East Hub", "elevator", "Concourse 1", 110, 1, "Open"),
        ("Elevator West Hub", "elevator", "Concourse 1", 130, 1, "Open"),
        # Prayer Rooms
        ("Multi-Faith Prayer Room", "prayer", "Concourse 2", 215, 1, "Open")
    ]
    cursor.executemany("""
    INSERT OR REPLACE INTO facilities (name, type, level, section, is_accessible, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, facilities_data)

    # Routes
    # We define routes between gates and main sections/facilities
    routes_data = [
        ("Gate A", "Gate C", 
         "Walk straight past Section 101, follow the main concourse path clockwise past Section 110, take a slight right bend at Section 115 to arrive at South Concourse and Gate C.",
         "Walk straight past Section 101, follow the step-free main concourse path clockwise past Section 110 (all level ground), continue past Section 115 to Gate C.",
         400),
        ("Gate A", "Section 112",
         "Enter Gate A, turn left and walk along the concourse past Section 140, continue to Section 130, and walk down the stairs to the lower rows of Section 112.",
         "Enter Gate A, turn right, walk along the flat concourse past Section 105, and use the ADA ramp at Section 110 to access Section 112 seating area.",
         180),
        ("Gate A", "Section 215",
         "Enter Gate A, proceed to the central corridor, take the escalator on your left to Level 2 (Concourse 2), and follow signs to Section 215.",
         "Enter Gate A, proceed to the East Elevator Hub near Section 110, take Elevator East to Level 2, and follow the wide level concourse straight to Section 215.",
         250),
        ("Gate C", "Section 112",
         "Enter Gate C, turn right and walk along the concourse past Section 118, continue straight to Section 112.",
         "Enter Gate C, turn right, follow the main level concourse past Section 118, use the flat accessible entryway directly into Section 112.",
         100),
        ("Gate C", "Multi-Faith Prayer Room",
         "Enter Gate C, walk to the West corridor, take the stairs near Section 130 up to Concourse 2, and turn right to reach Section 215 / Prayer Room.",
         "Enter Gate C, walk to the Elevator West Hub near Section 130, take the elevator to Level 2, exit and turn right on the level concourse to Section 215 / Prayer Room.",
         220)
    ]
    cursor.executemany("""
    INSERT OR REPLACE INTO routes (start_node, end_node, path_instructions, step_free_instructions, distance_meters)
    VALUES (?, ?, ?, ?, ?)
    """, routes_data)

    # Add bidirectional counterpart automatically for ease of routing
    cursor.execute("SELECT start_node, end_node, path_instructions, step_free_instructions, distance_meters FROM routes")
    existing_routes = cursor.fetchall()
    for start, end, path, step_free, dist in existing_routes:
        try:
            cursor.execute("""
            INSERT INTO routes (start_node, end_node, path_instructions, step_free_instructions, distance_meters)
            VALUES (?, ?, ?, ?, ?)
            """, (end, start, f"Reverse path: {path}", f"Reverse step-free path: {step_free}", dist))
        except sqlite3.IntegrityError:
            pass # Already exists

    conn.commit()
    conn.close()
    print("Database initialized and seeded successfully.")

if __name__ == "__main__":
    init_db()
