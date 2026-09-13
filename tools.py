import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from db import get_connections

# Simple FAQ for campus questions (tool: college_faq)
COLLEGE_FAQ = {
    "library": "Library hours: Mon–Sat 8:00 AM – 8:00 PM. Sunday closed.",
    "wifi": "Campus Wi‑Fi: connect to 'CampusNet' and login with student ID.",
    "bus": "College bus leaves main gate at 8:15 AM and 4:30 PM on weekdays.",
    "hostel": "Hostel office is open 9:00 AM – 5:00 PM. Contact warden for room issues.",
    "placement": "Placement cell is in Block B, 2nd floor. Walk-ins Mon–Fri 10 AM – 4 PM.",
    "canteen": "Canteen is open 8:00 AM – 7:00 PM near the sports complex.",
}


def search_events(query):
    """Search events by keyword."""
    conn = get_connections()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT title, date, location
        FROM events
        WHERE title LIKE ? COLLATE NOCASE
           OR location LIKE ? COLLATE NOCASE
        ORDER BY date
        """,
        (f"%{query}%", f"%{query}%"),
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No events found."

    lines = []
    for title, date, location in rows:
        lines.append(f"{title} | {date} | {location}")
    return "\n".join(lines)


def create_reminder(text):
    """Save a reminder in the database."""
    conn = get_connections()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT
        )
    """)

    cursor.execute("INSERT INTO reminders (text) VALUES (?)", (text,))
    conn.commit()
    conn.close()
    return f"Reminder saved: {text}"


def list_reminders():
    """List all saved reminders."""
    conn = get_connections()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT
        )
    """)

    cursor.execute("SELECT id, text FROM reminders ORDER BY id")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No reminders saved yet."

    lines = [f"{rid}. {text}" for rid, text in rows]
    return "\n".join(lines)


def add_event(title, date, location):
    """Add a new college event to the database."""
    conn = get_connections()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            date TEXT,
            location TEXT
        )
    """)

    cursor.execute(
        "INSERT INTO events (title, date, location) VALUES (?, ?, ?)",
        (title, date, location),
    )
    conn.commit()
    conn.close()
    return f"Event added: {title} on {date} at {location}"


def college_faq(topic):
    """Answer common campus FAQ questions."""
    key = topic.strip().lower()

    # exact key
    if key in COLLEGE_FAQ:
        return COLLEGE_FAQ[key]

    # partial match (e.g. "library hours" → library)
    for faq_key, answer in COLLEGE_FAQ.items():
        if faq_key in key or key in faq_key:
            return answer

    topics = ", ".join(COLLEGE_FAQ.keys())
    return f"No FAQ found for '{topic}'. Try one of: {topics}"


def generate_certificate(name):
    """
    Bonus tool: call pdf-app API to generate a certificate PDF.
    Also returns LinkedIn preview + share URLs.
    """
    from dotenv import load_dotenv

    load_dotenv()
    cert_api_base = os.getenv("CERT_API_BASE", "https://certificate.aigosys.com")

    cleaned = name.strip()
    if not cleaned:
        return "Name is required to generate a certificate."

    url = f"{cert_api_base.rstrip('/')}/api/generate"
    payload = json.dumps({"name": cleaned}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            # Cloudflare often blocks bare Python urllib (error 1010)
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/pdf,*/*",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            pdf_bytes = resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        hint = ""
        if e.code == 403 or "1010" in body:
            hint = (
                "\nCloudflare blocked this request (1010). "
                "For class/demo use local pdf-app and set in .env:\n"
                "CERT_API_BASE=http://127.0.0.1:8001"
            )
        return f"Certificate API error {e.code}: {body[:200]}{hint}"
    except urllib.error.URLError as e:
        return (
            f"Could not reach certificate API ({cert_api_base}): {e.reason}. "
            "Start local pdf-app or check CERT_API_BASE in .env."
        )

    out_dir = Path("certificates")
    out_dir.mkdir(exist_ok=True)
    safe = "".join("_" if c in '\\/:*?"<>|' else c for c in cleaned).strip(" ._") or "certificate"
    pdf_path = out_dir / f"{safe}.pdf"
    pdf_path.write_bytes(pdf_bytes)

    from urllib.parse import quote

    encoded = quote(cleaned)
    preview_url = f"{cert_api_base.rstrip('/')}/api/preview.png?name={encoded}"
    share_url = f"{cert_api_base.rstrip('/')}/api/share?name={encoded}"

    return (
        f"Certificate generated for {cleaned}.\n"
        f"Saved PDF: {pdf_path}\n"
        f"Preview PNG: {preview_url}\n"
        f"Share / LinkedIn: {share_url}"
    )


if __name__ == "__main__":
    print("--- search ---")
    print(search_events("AI"))
    print("--- reminder ---")
    print(create_reminder("Attend AI Workshop"))
    print("--- list_reminders ---")
    print(list_reminders())
    print("--- add_event ---")
    print(add_event("Cloud Meetup", "2026-10-08", "Seminar Hall"))
    print("--- faq ---")
    print(college_faq("library"))
    print("--- certificate (needs network + pdf-app) ---")
    print(generate_certificate("Demo Student"))
