import cv2
from deepface import DeepFace
import sqlite3
import time

cap = cv2.VideoCapture(0)

print("👉 Show your expression (hold steady & press ENTER to save)")
name = input("Enter name: ").strip().lower()

stable_expression = None
last_detected = None
count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Face detection
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) > 0:
        (x, y, w, h) = faces[0]

        face = frame[y:y+h, x:x+w]

        try:
            # Convert to RGB
            rgb_face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

            # Resize for DeepFace
            resized_face = cv2.resize(rgb_face, (224,224))

            result = DeepFace.analyze(
                resized_face,
                actions=['emotion'],
                enforce_detection=False
            )

            current_expression = result[0]['dominant_emotion']

            # Stability check
            if current_expression == last_detected:
                count += 1
            else:
                count = 0

            last_detected = current_expression

            # If stable for few frames
            if count > 5:
                stable_expression = current_expression

            cv2.putText(frame, f"Detecting: {current_expression}",
                        (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0), 2)

            if stable_expression:
                cv2.putText(frame, f"Stable: {stable_expression}",
                            (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        except:
            pass

        # Draw face box
        cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0), 2)

    else:
        cv2.putText(frame, "No face detected",
                    (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

    cv2.imshow("Register Expression", frame)

    key = cv2.waitKey(1)

    # ENTER key
    if key == 13 and stable_expression:
        break

cap.release()
cv2.destroyAllWindows()

# ----------------------------
# SAVE TO DB
# ----------------------------
conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

cursor.execute("""
INSERT OR REPLACE INTO users (name, expression)
VALUES (?, ?)
""", (name, stable_expression))

conn.commit()
conn.close()

print(f"✅ {name} registered with expression: {stable_expression}")