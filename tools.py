# Import json — used to build the certificate API request body
import json
# Import os — used to read environment variables like CERT_API_BASE
import os
# Import urllib error types — used when HTTP request fails
import urllib.error
# Import urllib.request — used to call the certificate API
import urllib.request
# Import Path — used to save the PDF file on disk
from pathlib import Path

# Import our DB helper so tools can open campus.db
from db import get_connections

# Dictionary of simple campus FAQ answers (used by college_faq tool)
COLLEGE_FAQ = {
    # Key "library" → library hours text
    "library": "Library hours: Mon–Sat 8:00 AM – 8:00 PM. Sunday closed.",
    # Key "wifi" → campus wifi instructions
    "wifi": "Campus Wi‑Fi: connect to 'CampusNet' and login with student ID.",
    # Key "bus" → college bus timings
    "bus": "College bus leaves main gate at 8:15 AM and 4:30 PM on weekdays.",
    # Key "hostel" → hostel office info
    "hostel": "Hostel office is open 9:00 AM – 5:00 PM. Contact warden for room issues.",
    # Key "placement" → placement cell location
    "placement": "Placement cell is in Block B, 2nd floor. Walk-ins Mon–Fri 10 AM – 4 PM.",
    # Key "canteen" → canteen hours / place
    "canteen": "Canteen is open 8:00 AM – 7:00 PM near the sports complex.",
}


def search_events(query):
    """Tool: search events by keyword in title or location."""
    # Open database connection
    conn = get_connections()
    # Create cursor to run SQL
    cursor = conn.cursor()

    # Run SELECT with LIKE search ( ? = safe placeholders )
    cursor.execute(
        """
        SELECT title, date, location
        FROM events
        WHERE title LIKE ? COLLATE NOCASE
           OR location LIKE ? COLLATE NOCASE
        ORDER BY date
        """,
        # %query% means: match text containing the keyword
        (f"%{query}%", f"%{query}%"),
    )

    # Fetch all matching rows as a list of tuples
    rows = cursor.fetchall()
    # Close DB connection
    conn.close()

    # If nothing matched, return a clear message
    if not rows:
        return "No events found."

    # Build a readable string list for the agent
    lines = []
    # Loop each row: unpack title, date, location
    for title, date, location in rows:
        # Format one event per line
        lines.append(f"{title} | {date} | {location}")
    # Join all lines with newlines and return
    return "\n".join(lines)


def create_reminder(text):
    """Tool: save a reminder in the database."""
    # Open database connection
    conn = get_connections()
    # Create cursor to run SQL
    cursor = conn.cursor()

    # Create reminders table if missing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT
        )
    """)

    # Insert the reminder text (trailing comma makes a 1-item tuple)
    cursor.execute("INSERT INTO reminders (text) VALUES (?)", (text,))
    # Save the insert
    conn.commit()
    # Close connection
    conn.close()
    # Return confirmation for the agent / user
    return f"Reminder saved: {text}"


def list_reminders():
    """Tool: list all saved reminders."""
    # Open database connection
    conn = get_connections()
    # Create cursor to run SQL
    cursor = conn.cursor()

    # Make sure reminders table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT
        )
    """)

    # Read all reminders ordered by id
    cursor.execute("SELECT id, text FROM reminders ORDER BY id")
    # Get all rows
    rows = cursor.fetchall()
    # Close connection
    conn.close()

    # Empty table → friendly message
    if not rows:
        return "No reminders saved yet."

    # Format as "1. text", "2. text", ...
    lines = [f"{rid}. {text}" for rid, text in rows]
    # Return as one multi-line string
    return "\n".join(lines)


def add_event(title, date, location):
    """Tool: add a new college event to the database."""
    # Open database connection
    conn = get_connections()
    # Create cursor to run SQL
    cursor = conn.cursor()

    # Ensure events table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            date TEXT,
            location TEXT
        )
    """)

    # Insert the new event with safe placeholders
    cursor.execute(
        "INSERT INTO events (title, date, location) VALUES (?, ?, ?)",
        (title, date, location),
    )
    # Save the insert
    conn.commit()
    # Close connection
    conn.close()
    # Return confirmation string
    return f"Event added: {title} on {date} at {location}"


def college_faq(topic):
    """Tool: answer common campus FAQ questions."""
    # Normalize topic: trim spaces + lowercase for matching
    key = topic.strip().lower()

    # Exact match: topic is exactly "library", "wifi", etc.
    if key in COLLEGE_FAQ:
        # Return the FAQ answer text
        return COLLEGE_FAQ[key]

    # Partial match: "library hours" still finds "library"
    for faq_key, answer in COLLEGE_FAQ.items():
        # If either string contains the other, treat as match
        if faq_key in key or key in faq_key:
            # Return matched FAQ answer
            return answer

    # Build a comma-separated list of known topics
    topics = ", ".join(COLLEGE_FAQ.keys())
    # Tell user which topics are available
    return f"No FAQ found for '{topic}'. Try one of: {topics}"


def generate_certificate(name):
    """
    Bonus tool: call pdf-app API to generate a certificate PDF.
    Also returns LinkedIn preview + share URLs.
    """
    # Import dotenv here so .env is loaded when this tool runs
    from dotenv import load_dotenv

    # Load variables from .env into the environment
    load_dotenv()
    # Read certificate API base URL (local or production)
    cert_api_base = os.getenv("CERT_API_BASE", "https://certificate.aigosys.com")

    # Remove extra spaces from the student name
    cleaned = name.strip()
    # Name is required — stop early if empty
    if not cleaned:
        return "Name is required to generate a certificate."

    # Build the generate endpoint URL
    url = f"{cert_api_base.rstrip('/')}/api/generate"
    # Convert {"name": "..."} into JSON bytes for POST body
    payload = json.dumps({"name": cleaned}).encode("utf-8")
    # Create an HTTP POST request object
    req = urllib.request.Request(
        # Target URL
        url,
        # JSON body bytes
        data=payload,
        # HTTP headers
        headers={
            # Tell server we are sending JSON
            "Content-Type": "application/json",
            # Browser-like User-Agent (helps avoid some Cloudflare blocks)
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            # We expect a PDF back
            "Accept": "application/pdf,*/*",
        },
        # HTTP method
        method="POST",
    )

    # Try calling the certificate API
    try:
        # Send request and open the response (timeout 60 seconds)
        with urllib.request.urlopen(req, timeout=60) as resp:
            # Read raw PDF bytes from the response body
            pdf_bytes = resp.read()
    # HTTP error like 403 / 404 / 500
    except urllib.error.HTTPError as e:
        # Read error body as text (best effort)
        body = e.read().decode("utf-8", errors="ignore")
        # Optional hint for Cloudflare 1010 blocks
        hint = ""
        # Detect Cloudflare ban / forbidden
        if e.code == 403 or "1010" in body:
            # Suggest using local pdf-app instead
            hint = (
                "\nCloudflare blocked this request (1010). "
                "For class/demo use local pdf-app and set in .env:\n"
                "CERT_API_BASE=http://127.0.0.1:8001"
            )
        # Return short error + hint to the agent
        return f"Certificate API error {e.code}: {body[:200]}{hint}"
    # Network / DNS / connection errors
    except urllib.error.URLError as e:
        # Tell student the API could not be reached
        return (
            f"Could not reach certificate API ({cert_api_base}): {e.reason}. "
            "Start local pdf-app or check CERT_API_BASE in .env."
        )

    # Folder where we save generated PDFs
    out_dir = Path("certificates")
    # Create folder if it does not exist
    out_dir.mkdir(exist_ok=True)
    # Make a filesystem-safe filename from the student name
    safe = "".join("_" if c in '\\/:*?"<>|' else c for c in cleaned).strip(" ._") or "certificate"
    # Full path like certificates/Shemeer.pdf
    pdf_path = out_dir / f"{safe}.pdf"
    # Write PDF bytes to disk
    pdf_path.write_bytes(pdf_bytes)

    # Import quote to encode spaces in URLs
    from urllib.parse import quote

    # URL-encode the name (Shemeer Kumar → Shemeer%20Kumar)
    encoded = quote(cleaned)
    # Public PNG preview URL (LinkedIn image)
    preview_url = f"{cert_api_base.rstrip('/')}/api/preview.png?name={encoded}"
    # Public share page URL (LinkedIn link share)
    share_url = f"{cert_api_base.rstrip('/')}/api/share?name={encoded}"

    # Return a clear multi-line success message for the agent
    return (
        f"Certificate generated for {cleaned}.\n"
        f"Saved PDF: {pdf_path}\n"
        f"Preview PNG: {preview_url}\n"
        f"Share / LinkedIn: {share_url}"
    )


# Runs only when you type: python tools.py
if __name__ == "__main__":
    # Quick test: search
    print("--- search ---")
    # Call search_events with keyword AI
    print(search_events("AI"))
    # Quick test: create reminder
    print("--- reminder ---")
    # Save a sample reminder
    print(create_reminder("Attend AI Workshop"))
    # Quick test: list reminders
    print("--- list_reminders ---")
    # Show all reminders
    print(list_reminders())
    # Quick test: add event
    print("--- add_event ---")
    # Insert a sample event
    print(add_event("Cloud Meetup", "2026-10-08", "Seminar Hall"))
    # Quick test: FAQ
    print("--- faq ---")
    # Ask library FAQ
    print(college_faq("library"))
    # Quick test: certificate (needs API running)
    print("--- certificate (needs network + pdf-app) ---")
    # Try generating a demo certificate
    print(generate_certificate("Demo Student"))
