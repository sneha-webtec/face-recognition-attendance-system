import cv2
import numpy as np
import psycopg2
import base64
import json

print("🚀 Training started...")

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
# GET ALL EMPLOYEE FACES
# ----------------------------

cursor.execute("""
SELECT e.employee_name,
       f.face_base64
FROM employee_faces f
JOIN employees e
ON f.employee_id = e.employee_id
""")

rows = cursor.fetchall()

conn.close()

# ----------------------------
# PREPARE TRAINING DATA
# ----------------------------

faces = []
labels = []

label_ids = {}
current_id = 0

for employee_name, face_base64 in rows:

    # Create label ID
    if employee_name not in label_ids:

        label_ids[employee_name] = current_id

        current_id += 1

    label = label_ids[employee_name]

    # Decode Base64
    image_data = base64.b64decode(face_base64)

    np_array = np.frombuffer(image_data, np.uint8)

    img = cv2.imdecode(np_array, cv2.IMREAD_GRAYSCALE)

    if img is None:
        continue

    faces.append(img)

    labels.append(label)

# ----------------------------
# CHECK EMPTY DATA
# ----------------------------

if len(faces) == 0:

    print("❌ No training images found")

    exit()

# ----------------------------
# TRAIN MODEL
# ----------------------------

recognizer = cv2.face.LBPHFaceRecognizer_create()

recognizer.train(
    faces,
    np.array(labels)
)

recognizer.save("model.yml")


# ----------------------------
# SAVE LABELS
# ----------------------------

with open("labels.json", "w") as f:

    json.dump(
        {v: k for k, v in label_ids.items()},
        f
    )

print("✅ Model trained successfully")
print(f"✅ Total faces trained: {len(faces)}")