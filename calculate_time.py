import sqlite3

conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

# Get all data
cursor.execute("SELECT name, event, time FROM attendance ORDER BY id ASC")
rows = cursor.fetchall()

data = {}

# ----------------------------
# PROCESS DATA
# ----------------------------
for name, event, time in rows:

    if name not in data:
        data[name] = []

    data[name].append((event, time))

# ----------------------------
# CALCULATE WORK TIME
# ----------------------------
print("\n📊 Attendance Summary:\n")

for name in data:

    logs = data[name]
    last_entry = None
    total_minutes = 0

    for event, time in logs:

        if event == "ENTRY":
            last_entry = time

        elif event == "EXIT" and last_entry:

            # convert to seconds
            h1, m1, s1 = map(int, last_entry.split(":"))
            h2, m2, s2 = map(int, time.split(":"))

            t1 = h1*3600 + m1*60 + s1
            t2 = h2*3600 + m2*60 + s2

            total_minutes += (t2 - t1) // 60

            last_entry = None

    print(f"{name} → {total_minutes} minutes")

conn.close()