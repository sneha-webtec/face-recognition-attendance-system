import cv2
import base64
import psycopg2

# ----------------------------
# POSTGRESQL CONNECTION
# ----------------------------

conn = psycopg2.connect(
    host="localhost",
    database="attendance_system",
    user="postgres",
    password="admin123",
    port="5432"
)

cursor = conn.cursor()

# ----------------------------
# IMAGE PATH
# ----------------------------

image_path = "dataset/sneha/1.jpg"

# ----------------------------
# READ IMAGE
# ----------------------------

img = cv2.imread(image_path)

# ----------------------------
# CONVERT IMAGE TO JPG BUFFER
# ----------------------------

_, buffer = cv2.imencode(".jpg", img)

# ----------------------------
# CONVERT BUFFER TO BASE64
# ----------------------------

encoded_string = base64.b64encode(buffer).decode()

# ----------------------------
# STORE IN POSTGRESQL
# ----------------------------

cursor.execute(
    """
    INSERT INTO employee_faces
    (employee_name, face_base64)
    VALUES (%s, %s)
    """,
    ("sneha", encoded_string)
)

conn.commit()

print("✅ Face stored successfully")

conn.close()