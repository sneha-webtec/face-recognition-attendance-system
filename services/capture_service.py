import cv2
import time
import psycopg2
import os
import base64
import tkinter as tk
from tkinter import messagebox
import sys
import json

# ----------------------------
# POSTGRESQL CONNECTION
# ----------------------------
def register_employee(person_name):
    conn = psycopg2.connect(
        host="localhost",
        database="attendance_system",
        user="postgres",
        password="admin123",
        port="5432"
    )

    cursor = conn.cursor()

# ----------------------------
# LOAD FACE RECOGNIZER
# ----------------------------

    recognizer = None
    labels = {}

    if os.path.exists("model.yml") and os.path.exists("labels.json"):

        recognizer = cv2.face.LBPHFaceRecognizer_create()

        recognizer.read("model.yml")

        with open("labels.json", "r") as f:

            labels = json.load(f)

        labels = {int(k): v for k, v in labels.items()}

        print("✅ Existing model loaded")

    else:

        print("⚠ No trained model found")
        print("⚠ Duplicate face checking disabled")

# ----------------------------
# CONFIG
# ----------------------------

# ----------------------------
# CHECK EXISTING EMPLOYEE NAME
# ----------------------------

    cursor.execute("""
    SELECT employee_id
    FROM employees
    WHERE employee_name = %s
    """, (person_name,))

    result = cursor.fetchone()

    if result is not None:

        root = tk.Tk()

        root.withdraw()

        messagebox.showwarning(
            "Employee Exists",
            f"{person_name.upper()} already exists in database."
        )

        print("⚠ Employee already exists")

        conn.close()

        sys.exit()

# ----------------------------
# FACE DETECTOR
# ----------------------------

    face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    'haarcascade_frontalface_default.xml'
)

# ----------------------------
# CAMERA
# ----------------------------

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():

        root = tk.Tk()

        root.withdraw()

        messagebox.showerror(
            "Camera Error",
            "Camera access not available.\n"
            "Please allow camera permission."
        )

        print("❌ Camera not accessible")

        conn.close()

        sys.exit()

        print("📸 Camera started")

    cv2.namedWindow("Capture Faces", cv2.WINDOW_NORMAL)

    cv2.resizeWindow("Capture Faces", 800, 600)

    print("📸 Look at camera and move slightly")

# ----------------------------
# PHASE 1:
# DUPLICATE FACE CHECK
# ----------------------------

    duplicate_detected = False

    duplicate_person = None

    frames_checked = 0

    MAX_CHECK_FRAMES = 10

    CONFIDENCE_THRESHOLD = 65

    print("🔍 Checking for duplicate face...")

    while frames_checked < MAX_CHECK_FRAMES:

        ret, frame = cap.read()

        if not ret:
            break

        display_frame = frame.copy()

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5
        )

        for (x, y, w, h) in faces:

            face = gray[y:y+h, x:x+w]

            face = cv2.resize(face, (200, 200))

            face = cv2.equalizeHist(face)

        # ----------------------------
        # FACE RECOGNITION
        # ----------------------------

        if recognizer is not None:

            try:

                label, confidence = recognizer.predict(face)

                print(
                    f"DEBUG -> "
                    f"label: {label}, "
                    f"confidence: {confidence}"
                )

                # LOWER = more similar

                if confidence < CONFIDENCE_THRESHOLD:

                    existing_person = labels.get(label)

                    if (
                        existing_person
                        and existing_person != person_name
                    ):

                        duplicate_detected = True

                        duplicate_person = existing_person

                        break

            except Exception as e:

                print("Recognition error:", e)

        frames_checked += 1

        # ----------------------------
        # DRAW RECTANGLE
        # ----------------------------

        cv2.rectangle(
            display_frame,
            (x, y),
            (x+w, y+h),
            (0, 255, 255),
            2
        )

        cv2.putText(
            display_frame,
            f"Checking... "
            f"{frames_checked}/{MAX_CHECK_FRAMES}",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        break

        if duplicate_detected:
            break

    cv2.imshow("Capture Faces", display_frame)

    key = cv2.waitKey(1)

    if key == 27:

        print("❌ Registration cancelled")

        cap.release()

        cv2.destroyAllWindows()

        conn.close()

        sys.exit()

# ----------------------------
# DUPLICATE FACE FOUND
# ----------------------------

    if duplicate_detected:

        cap.release()

        cv2.destroyAllWindows()

        conn.close()

        root = tk.Tk()

        root.withdraw()

        messagebox.showerror(
            "Duplicate Face",
            f"This face already belongs to "
            f"{duplicate_person.upper()}"
        )

        print(
            f"❌ Duplicate face detected: "
            f"{duplicate_person}"
        )

        sys.exit()

        print("✅ Face check passed")

# ----------------------------
# PHASE 2:
# INSERT EMPLOYEE
# ----------------------------

    cursor.execute("""
    INSERT INTO employees
    (employee_name)
    VALUES (%s)
    RETURNING employee_id
    """, (person_name,))

    employee_id = cursor.fetchone()[0]

    print(f"✅ New Employee ID: {employee_id}")

# ----------------------------
# CAPTURE SETTINGS
# ----------------------------

    MAX_IMAGES = 50

    CAPTURE_DELAY = 0.3

# ----------------------------
# PHASE 3:
# CAPTURE IMAGES
# ----------------------------

    count = 0

    last_capture_time = time.time()

    while count < MAX_IMAGES:

        ret, frame = cap.read()

        if not ret:
            break

    display_frame = frame.copy()

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5
    )

    for (x, y, w, h) in faces:

        current_time = time.time()

        if (
            current_time - last_capture_time
            > CAPTURE_DELAY
        ):

            # ----------------------------
            # FACE EXTRACTION
            # ----------------------------

            face = gray[y:y+h, x:x+w]

            face = cv2.resize(face, (200, 200))

            face = cv2.equalizeHist(face)

            # ----------------------------
            # CONVERT TO BASE64
            # ----------------------------

            _, buffer = cv2.imencode(".jpg", face)

            encoded_string = base64.b64encode(
                buffer
            ).decode()

            # ----------------------------
            # STORE IN POSTGRESQL
            # ----------------------------

            cursor.execute(
                """
                INSERT INTO employee_faces
                (employee_id, face_base64)
                VALUES (%s, %s)
                """,
                (
                    employee_id,
                    encoded_string
                )
            )

            count += 1

            print(
                f"✅ Stored image "
                f"{count}/{MAX_IMAGES}"
            )

            last_capture_time = current_time

        # ----------------------------
        # DRAW RECTANGLE
        # ----------------------------

        cv2.rectangle(
            display_frame,
            (x, y),
            (x+w, y+h),
            (0, 255, 0),
            2
        )

        cv2.putText(
            display_frame,
            f"{count}/{MAX_IMAGES}",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        break

    cv2.imshow(
        "Capture Faces",
        display_frame
    )

    key = cv2.waitKey(1)

    if key == 27:

        print("❌ Registration cancelled")

        conn.rollback()

        cap.release()

        cv2.destroyAllWindows()

        conn.close()

        sys.exit()

# ----------------------------
# FINAL COMMIT
# ----------------------------

    conn.commit()

    cap.release()

    cv2.destroyAllWindows()

    conn.close()

    print(
        f"✅ Employee "
        f"{person_name} "
        f"registered successfully"
    )

    return True