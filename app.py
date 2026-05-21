from flask import Flask, render_template
import psycopg2
import psycopg2.extras
from datetime import datetime
from flask import Flask, render_template, request

from services.capture_service import register_employee
from services.train_service import train_model
from services.attendance_service import start_attendance

app = Flask(__name__)

# ----------------------------
# POSTGRESQL CONNECTION
# ----------------------------

def get_db_connection():

    conn = psycopg2.connect(
        host="localhost",
        database="attendance_system",
        user="postgres",
        password="admin123",
        port="5432"
    )

    return conn


# ----------------------------
# DASHBOARD
# ----------------------------

@app.route("/")

def dashboard():

    conn = get_db_connection()

    cursor = conn.cursor(
        cursor_factory=psycopg2.extras.RealDictCursor
    )


    # ----------------------------
    # TOTAL REGISTERED USERS
    # ----------------------------

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM employees
    """)

    total_users = cursor.fetchone()["total"]

    # ----------------------------
    # UNKNOWN ATTEMPTS
    # ----------------------------

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM attendance
        WHERE name='unknown'
    """)

    unknown_attempts = cursor.fetchone()["total"]

    # ----------------------------
    # RECENT LOGS
    # ----------------------------

    cursor.execute("""
        SELECT name, event, time
        FROM attendance
        ORDER BY id DESC
        LIMIT 10
    """)

    recent_logs = cursor.fetchall()

    # ----------------------------
    # GET ALL EMPLOYEES
    # ----------------------------

    cursor.execute("""
        SELECT employee_name
        FROM employees
    """)

    people = cursor.fetchall()

    employee_data = []

    inside_count = 0

    outside_count = 0

    # ----------------------------
    # PROCESS EACH EMPLOYEE
    # ----------------------------

    for person in people:

        name = person["employee_name"]

        # ----------------------------
        # CURRENT STATUS
        # ----------------------------

        cursor.execute("""
            SELECT event, time
            FROM attendance
            WHERE name=%s
            AND date=CURRENT_DATE
            ORDER BY id DESC
            LIMIT 1
        """, (name,))

        status_row = cursor.fetchone()

        status = "Outside"

        if status_row:

            if status_row["event"] == "ENTRY":

                status = "Inside"

                inside_count += 1

            else:

                status = "Outside"

                outside_count += 1

        else:

            outside_count += 1

        # ----------------------------
        # TODAY LOGS
        # ----------------------------

        cursor.execute("""
            SELECT event, time
            FROM attendance
            WHERE name=%s
            AND date=CURRENT_DATE
            ORDER BY time DESC
            LIMIT 5
        """, (name,))

        logs = cursor.fetchall()

        # ----------------------------
        # ALL TODAY RECORDS
        # ----------------------------

        cursor.execute("""
            SELECT event, time
            FROM attendance
            WHERE name=%s
            AND date=CURRENT_DATE
            ORDER BY id ASC
        """, (name,))

        records = cursor.fetchall()

        # ----------------------------
        # ATTENDANCE CALCULATION
        # ----------------------------

        first_entry = "-"
        last_exit = "-"
        latest_event = None

        total_minutes = 0
        entry_time = None

        for record in records:

            event = record["event"]
            time_value = record["time"]

            latest_event = event

            # ----------------------------
            # FIRST ENTRY OF DAY
            # ----------------------------

            if event == "ENTRY":

                if first_entry == "-":
                    first_entry = time_value

                entry_time = datetime.strptime(
                    str(time_value),
                    "%H:%M:%S"
                )

            # ----------------------------
            # LAST EXIT OF DAY
            # ----------------------------

            elif event == "EXIT":

                last_exit = time_value

                if entry_time:

                    exit_time = datetime.strptime(
                        str(time_value),
                        "%H:%M:%S"
                    )

                    diff = exit_time - entry_time

                    total_minutes += diff.seconds // 60

                    entry_time = None

        # ----------------------------
        # IF STILL INSIDE
        # ----------------------------

        if latest_event == "ENTRY":

            last_exit = "-"

        # ----------------------------
        # WORKING HOURS
        # ----------------------------

        hours = total_minutes // 60

        minutes = total_minutes % 60

        working_hours = f"{hours}h {minutes}m"

        # ----------------------------
        # FINAL EMPLOYEE DATA
        # ----------------------------

        employee_data.append({

            "name": name,

            "entry": first_entry,

            "exit": last_exit,

            "status": status,

            "logs": logs,

            "working_hours": working_hours

        })

    conn.close()

    # ----------------------------
    # RENDER HTML
    # ----------------------------

    return render_template(

        "dashboard.html",

        total_users=total_users,

        inside_count=inside_count,

        outside_count=outside_count,

        unknown_attempts=unknown_attempts,

        employee_data=employee_data,

        recent_logs=recent_logs
    )

@app.route("/register", methods=["GET", "POST"])

def register():

    if request.method == "POST":

        name = request.form["name"]

        register_employee(name)

        return "Employee Registered Successfully"

    return render_template("register.html")

@app.route("/train")

def train():

    train_model()

    return "Model Trained Successfully"

@app.route("/attendance")

def attendance():

    start_attendance()

    return "Attendance Started"
# ----------------------------
# RUN FLASK
# ----------------------------

if __name__ == "__main__":

    app.run(debug=True)