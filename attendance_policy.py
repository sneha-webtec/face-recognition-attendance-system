import sqlite3
from datetime import datetime
import smtplib
from email.mime.text import MIMEText


# ----------------------------
# OFFICE RULES
# ----------------------------

OFFICE_ENTRY_TIME = "09:00:00"
OFFICE_EXIT_TIME = "18:00:00"

REQUIRED_HOURS = 0.02
GRACE_MINUTES = 15

# ----------------------------
# EMAIL CONFIG
# ----------------------------

SENDER_EMAIL = "smartattendancep@gmail.com"
SENDER_PASSWORD = "otppxnzlesppotom"

MANAGER_EMAIL = "sneharampur5@gmail.com"

# ----------------------------
# SEND EMAIL
# ----------------------------

def send_email(subject, body):

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = MANAGER_EMAIL

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)

        server.starttls()

        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        server.sendmail(
            SENDER_EMAIL,
            MANAGER_EMAIL,
            msg.as_string()
        )

        server.quit()

        print("📩 Alert sent to manager")

    except Exception as e:
        print("MAIL ERROR:", e)

# ----------------------------
# POLICY CHECK
# ----------------------------

def check_attendance_policy(name):

    conn = sqlite3.connect("attendance.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # Today's records
    cursor.execute("""
        SELECT event, time
        FROM attendance
        WHERE name=? AND date=DATE('now')
        ORDER BY id ASC
    """, (name,))

    records = cursor.fetchall()

    conn.close()

    if len(records) < 2:
        return

    # ----------------------------
    # GET FIRST ENTRY
    # ----------------------------

    first_entry = None
    last_exit = None

    total_minutes = 0
    entry_time = None

    for row in records:

        event = row["event"]
        time_str = row["time"]

        current_time = datetime.strptime(
            time_str,
            "%H:%M:%S"
        )

        if event == "ENTRY":

            if first_entry is None:
                first_entry = current_time

            entry_time = current_time

        elif event == "EXIT":

            last_exit = current_time

            if entry_time:

                diff = last_exit - entry_time

                total_minutes += diff.seconds // 60

                entry_time = None

    # ----------------------------
    # TOTAL WORK HOURS
    # ----------------------------

    total_hours = total_minutes / 60

    # ----------------------------
    # RULE 1 - LATE LOGIN
    # ----------------------------

    office_entry = datetime.strptime(
        OFFICE_ENTRY_TIME,
        "%H:%M:%S"
    )

    late_limit = office_entry.hour * 60 + office_entry.minute + GRACE_MINUTES

    employee_minutes = (
        first_entry.hour * 60 +
        first_entry.minute
    )

    if employee_minutes > late_limit:

        send_email(
            "Late Login Alert",
            f"{name.upper()} logged in late at {first_entry.strftime('%H:%M:%S')}"
        )

    # ----------------------------
    # RULE 2 - EARLY EXIT
    # ----------------------------

    office_exit = datetime.strptime(
        OFFICE_EXIT_TIME,
        "%H:%M:%S"
    )

    employee_exit_minutes = (
        last_exit.hour * 60 +
        last_exit.minute
    )

    office_exit_minutes = (
        office_exit.hour * 60 +
        office_exit.minute
    )

    if employee_exit_minutes < office_exit_minutes:

        send_email(
            "Early Exit Alert",
            f"{name.upper()} exited early at {last_exit.strftime('%H:%M:%S')}"
        )

    # ----------------------------
    # RULE 3 - UNDERWORKED
    # ----------------------------

    if total_hours < REQUIRED_HOURS:
        hours = total_minutes // 60
        minutes = total_minutes % 60
        send_email(
            "Underworked Alert",
            f"{name.upper()} worked only  {hours}h {minutes}m today"
        )

    # ----------------------------
    # RULE 4 - OVERTIME
    # ----------------------------

    elif total_hours > REQUIRED_HOURS:
        hours = total_minutes // 60
        minutes = total_minutes % 60
        send_email(
            "Overtime Alert",
            f"{name.upper()} worked overtime ({hours}h {minutes}m)"
        )



if __name__ == "__main__":

    conn = sqlite3.connect("attendance.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT name
        FROM attendance
        WHERE name != 'unknown'
        """)

    employees = cursor.fetchall()

    conn.close()
            
    print("Checking attendance policies...")
    for employee in employees:

            name = employee["name"]

            print(f"Checking policy for {name}")

            check_attendance_policy(name)