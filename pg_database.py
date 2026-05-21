import psycopg2

try:

    conn = psycopg2.connect(
        host="localhost",
        database="attendance_system",
        user="postgres",
        password="admin123",
        port="5432"
    )

    cursor = conn.cursor()

    print("✅ PostgreSQL Connected Successfully")

except Exception as e:

    print("❌ Connection Error")
    print(e)