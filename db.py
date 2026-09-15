# Import SQLite — Python's built-in database library (no pip install needed)
import sqlite3

# List of sample campus events: (title, date, location)
SAMPLE_EVENTS = [
    # Event 1: AI Workshop
    ("AI Workshop", "2026-09-15", "Main Auditorium"),
    # Event 2: Coding Competition
    ("Coding Competition", "2026-09-17", "Computer Lab"),
    # Event 3: Placement Orientation
    ("Placement Orientation", "2026-09-20", "Seminar Hall"),
    # Event 4: Hackathon
    ("Hackathon 2026", "2026-09-22", "Innovation Lab"),
    # Event 5: Robotics Expo
    ("Robotics Expo", "2026-09-25", "Main Auditorium"),
    # Event 6: Python Bootcamp
    ("Python Bootcamp", "2026-09-28", "Computer Lab"),
    # Event 7: Career Fair
    ("Career Fair", "2026-10-02", "Sports Complex"),
    # Event 8: Cultural Fest
    ("Cultural Fest", "2026-10-05", "Open Air Theatre"),
    # Event 9: Cloud Meetup
    ("Cloud Meetup", "2026-10-08", "Seminar Hall"),
    # Event 10: Data Science Talk
    ("Data Science Talk", "2026-10-12", "Block B Hall"),
    # Event 11: Startup Pitch Day
    ("Startup Pitch Day", "2026-10-15", "Incubation Centre"),
    # Event 12: Cyber Security Workshop
    ("Cyber Security Workshop", "2026-10-18", "Computer Lab"),
]

# List of sample reminders (text only)
SAMPLE_REMINDERS = [
    # Reminder 1
    "Attend AI Workshop",
    # Reminder 2
    "Submit coding assignment",
    # Reminder 3
    "Meet placement officer",
    # Reminder 4
    "Register for Hackathon 2026",
    # Reminder 5
    "Renew library books",
    # Reminder 6
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

    # If force_reseed=True, delete all old rows first
    if force_reseed:
        # Clear events table
        cursor.execute("DELETE FROM events")
        # Clear reminders table
        cursor.execute("DELETE FROM reminders")

    # Count how many event rows are already in the table
    cursor.execute("SELECT COUNT(*) FROM events")
    # If count is 0, the table is empty — insert sample events
    if cursor.fetchone()[0] == 0:
        # Insert all rows from SAMPLE_EVENTS at once
        cursor.executemany(
            "INSERT INTO events (title, date, location) VALUES (?, ?, ?)",
            SAMPLE_EVENTS,
        )

    # Count how many reminder rows are already in the table
    cursor.execute("SELECT COUNT(*) FROM reminders")
    # If count is 0, insert sample reminders
    if cursor.fetchone()[0] == 0:
        # Wrap each reminder string as a 1-item tuple for executemany
        cursor.executemany(
            "INSERT INTO reminders (text) VALUES (?)",
            [(text,) for text in SAMPLE_REMINDERS],
        )

    # Save all INSERT / CREATE / DELETE changes to disk
    conn.commit()
    # Close the connection (good habit)
    conn.close()


# This block runs only when you type: python db.py
if __name__ == "__main__":
    # Clear and reload all sample data
    init_db(force_reseed=True)

    # Open DB again to print what was inserted
    conn = get_connections()
    # Create cursor for SELECT queries
    cursor = conn.cursor()
    # Read all events sorted by date
    cursor.execute("SELECT title, date, location FROM events ORDER BY date")
    # Print header
    print("Events:")
    # Print each event row
    for row in cursor.fetchall():
        print(" ", row)
    # Read all reminders sorted by id
    cursor.execute("SELECT id, text FROM reminders ORDER BY id")
    # Print header
    print("Reminders:")
    # Print each reminder row
    for row in cursor.fetchall():
        print(" ", row)
    # Close connection after printing
    conn.close()

    # Final success message for students
    print("Database ready (events + reminders reseeded)")
