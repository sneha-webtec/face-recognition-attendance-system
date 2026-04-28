import sqlite3

conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    name TEXT PRIMARY KEY,
    expression TEXT
)
""")
# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    event TEXT,
    time TEXT
)
""")

conn.commit()
conn.close()

print("✅ Database ready")

