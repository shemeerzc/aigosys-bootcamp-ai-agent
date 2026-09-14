# Import SQLite — Python's built-in database library (no pip install needed)
import sqlite3

# Sample campus events for demos / workshops
SAMPLE_EVENTS = [
    ("AI Workshop", "2026-09-15", "Main Auditorium"),
    ("Coding Competition", "2026-09-17", "Computer Lab"),
    ("Placement Orientation", "2026-09-20", "Seminar Hall"),
    ("Hackathon 2026", "2026-09-22", "Innovation Lab"),
    ("Robotics Expo", "2026-09-25", "Main Auditorium"),
    ("Python Bootcamp", "2026-09-28", "Computer Lab"),
    ("Career Fair", "2026-10-02", "Sports Complex"),
    ("Cultural Fest", "2026-10-05", "Open Air Theatre"),
    ("Cloud Meetup", "2026-10-08", "Seminar Hall"),
    ("Data Science Talk", "2026-10-12", "Block B Hall"),
    ("Startup Pitch Day", "2026-10-15", "Incubation Centre"),
    ("Cyber Security Workshop", "2026-10-18", "Computer Lab"),
]

# Sample reminders for demos
SAMPLE_REMINDERS = [
    "Attend AI Workshop",
    "Submit coding assignment",
    "Meet placement officer",
    "Register for Hackathon 2026",
    "Renew library books",
    "Pay hostel fee before month end",
]


def get_connections():
    # Open (or create) the campus.db file in this project folder
    conn = sqlite3.connect("campus.db")
    # Return the connection object so other functions can use it
    return conn


def init_db(force_reseed=False):
    # Get a live connection to the database
    conn = get_connections()
    # Create a cursor — this object is used to run SQL commands
    cursor = conn.cursor()

    # Create the events table if it does not already exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            date TEXT,
            location TEXT
        )""")

    # Create the reminders table if it does not already exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT
        )""")

    # Optional: clear old rows so we can load fresh sample data
    if force_reseed:
        cursor.execute("DELETE FROM events")
        cursor.execute("DELETE FROM reminders")

    # Count how many event rows are already in the table
    cursor.execute("SELECT COUNT(*) FROM events")
    # If count is 0, insert all sample events
    if cursor.fetchone()[0] == 0:
        # Insert many campus events ( ? placeholders = safe values )
        cursor.executemany(
            "INSERT INTO events (title, date, location) VALUES (?, ?, ?)",
            SAMPLE_EVENTS,
        )

    # Count how many reminder rows are already in the table
    cursor.execute("SELECT COUNT(*) FROM reminders")
    # If count is 0, insert all sample reminders
    if cursor.fetchone()[0] == 0:
        # Insert many reminders
        cursor.executemany(
            "INSERT INTO reminders (text) VALUES (?)",
            [(text,) for text in SAMPLE_REMINDERS],
        )

    # Save all INSERT / CREATE changes to disk
    conn.commit()
    # Close the connection (good habit)
    conn.close()


# This block runs only when you type: python db.py
if __name__ == "__main__":
    # force_reseed=True → clear old data and insert fresh samples
    init_db(force_reseed=True)

    # Show what was inserted (for teaching / verification)
    conn = get_connections()
    cursor = conn.cursor()
    cursor.execute("SELECT title, date, location FROM events ORDER BY date")
    print("Events:")
    for row in cursor.fetchall():
        print(" ", row)
    cursor.execute("SELECT id, text FROM reminders ORDER BY id")
    print("Reminders:")
    for row in cursor.fetchall():
        print(" ", row)
    conn.close()

    # Tell the student the DB is ready
    print("Database ready (events + reminders reseeded)")
