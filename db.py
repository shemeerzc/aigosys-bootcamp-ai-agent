import sqlite3

def get_connections():
    conn = sqlite3.connect("campus.db")
    return conn

def init_db():
    conn = get_connections()
    cursor = conn.cursor()
    
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            date TEXT,
            location TEXT
        )""")
    # insert a few sample rows if empty
    cursor.execute("SELECT COUNT(*) FROM events")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO events (title, date, location) VALUES (?, ?, ?)",
            ("AI Workshop", "2026-09-15", "Auditorium"),
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database ready")
