import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import cv2
import numpy as np
from deepface import DeepFace
import psycopg2
from datetime import datetime
import json
import time
import winsound

from attendance_policy import check_attendance_policy


def start_attendance():

    # ----------------------------
    # CONFIG
    # ----------------------------

    MODEL_PATH = "model.yml"
    LABELS_PATH = "labels.json"

    COOLDOWN = 5

    # ----------------------------
    # LOAD MODEL
    # ----------------------------

    recognizer = cv2.face.LBPHFaceRecognizer_create()

    recognizer.read(MODEL_PATH)

    with open(LABELS_PATH, "r") as f:

        labels = json.load(f)

        labels = {
            int(k): v
            for k, v in labels.items()
        }

    # ----------------------------
    # DATABASE FUNCTIONS
    # ----------------------------

    def get_user_expression(name):

        conn = psycopg2.connect(
            host="localhost",
            database="attendance_system",
            user="postgres",
            password="admin123",
            port="5432"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT expression
            FROM employees
            WHERE employee_name=%s
            """,
            (name,)
        )

        result = cursor.fetchone()

        conn.close()

        if result:

            return result[0]

        return None

    def log_event(name, event):

        conn = psycopg2.connect(
            host="localhost",
            database="attendance_system",
            user="postgres",
            password="admin123",
            port="5432"
        )

        cursor = conn.cursor()

        time_now = datetime.now().strftime("%H:%M:%S")

        date_now = datetime.now().strftime("%Y-%m-%d")

        cursor.execute(
            """
            INSERT INTO attendance
            (name, event, date, time)
            VALUES (%s, %s, %s, %s)
            """,
            (
                name,
                event,
                date_now,
                time_now
            )
        )

        conn.commit()

        conn.close()

        print(f"✅ {name} {event}")

    def get_last_status(name):

        conn = psycopg2.connect(
            host="localhost",
            database="attendance_system",
            user="postgres",
            password="admin123",
            port="5432"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT event
            FROM attendance
            WHERE name=%s
            ORDER BY id DESC
            LIMIT 1
            """,
            (name,)
        )

        row = cursor.fetchone()

        conn.close()

        return row[0] if row else "EXIT"

    # ----------------------------
    # FACE DETECTOR
    # ----------------------------

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades +
        "haarcascade_frontalface_default.xml"
    )

    # ----------------------------
    # ALERT SOUND
    # ----------------------------

    def play_alert():

        winsound.Beep(1000, 400)

        winsound.Beep(800, 400)

    # ----------------------------
    # CAMERA
    # ----------------------------

    cap = cv2.VideoCapture(0)

    # ----------------------------
    # CAMERA CHECK
    # ----------------------------

    if not cap.isOpened():

        import tkinter as tk

        from tkinter import messagebox

        root = tk.Tk()

        root.withdraw()

        messagebox.showerror(
            "Camera Error",
            "Camera access not available.\n"
            "Please allow camera permission."
        )

        print("❌ Camera not accessible")

        return False

    print("📸 Camera started")

    start_time = time.time()

    success = False

    unknown_detected = False

    last_action_time = 0

    # ----------------------------
    # MAIN LOOP
    # ----------------------------

    while True:

        ret, frame = cap.read()

        if not ret:

            continue

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        faces = face_cascade.detectMultiScale(
            gray,
            1.3,
            5
        )

        display_text = "NO FACE"

        color = (0, 0, 255)

        if len(faces) > 0:

            (x, y, w, h) = faces[0]

            face_gray = gray[y:y+h, x:x+w]

            id_, confidence = recognizer.predict(
                face_gray
            )

            # ----------------------------
            # UNKNOWN PERSON
            # ----------------------------

            if confidence > 60:

                display_text = "UNKNOWN PERSON"

                color = (0, 0, 255)

                unknown_detected = True

            else:

                name = labels.get(
                    id_,
                    "Unknown"
                ).lower()

                if name == "unknown":

                    display_text = "UNKNOWN PERSON"

                    color = (0, 0, 255)

                else:

                    # ----------------------------
                    # COOLDOWN CHECK
                    # ----------------------------

                    if (
                        time.time() -
                        last_action_time
                        < COOLDOWN
                    ):

                        display_text = "WAIT..."

                        color = (0, 255, 255)

                    else:

                        # ----------------------------
                        # EMOTION CHECK
                        # ----------------------------

                        emotion_list = []

                        for _ in range(8):

                            ret, temp_frame = cap.read()

                            if not ret:

                                continue

                            face_color = temp_frame[
                                y:y+h,
                                x:x+w
                            ]

                            rgb_face = cv2.cvtColor(
                                face_color,
                                cv2.COLOR_BGR2RGB
                            )

                            resized_face = cv2.resize(
                                rgb_face,
                                (224, 224)
                            )

                            try:

                                result = DeepFace.analyze(
                                    resized_face,
                                    actions=['emotion'],
                                    enforce_detection=False
                                )

                                emotion_list.append(
                                    result[0]['dominant_emotion']
                                )

                            except:

                                pass

                        # ----------------------------
                        # FINAL EMOTION
                        # ----------------------------

                        if len(emotion_list) > 0:

                            emotion = max(
                                set(emotion_list),
                                key=emotion_list.count
                            )

                        else:

                            emotion = None

                        stored_expression = (
                            get_user_expression(name)
                        )

                        # ----------------------------
                        # EXPRESSION MATCH
                        # ----------------------------

                        if emotion == stored_expression:

                            success = True

                            last_state = (
                                get_last_status(name)
                            )

                            if last_state == "EXIT":

                                new_state = "ENTRY"

                            else:

                                new_state = "EXIT"

                            log_event(
                                name,
                                new_state
                            )

                            display_text = (
                                f"{name} {new_state}"
                            )

                            color = (0, 255, 0)

                            last_action_time = (
                                time.time()
                            )

                        else:

                            display_text = (
                                "INVALID EXPRESSION"
                            )

                            color = (0, 0, 255)

            # ----------------------------
            # DRAW FACE RECTANGLE
            # ----------------------------

            cv2.rectangle(
                frame,
                (x, y),
                (x+w, y+h),
                color,
                2
            )

        # ----------------------------
        # DISPLAY TEXT
        # ----------------------------

        cv2.putText(
            frame,
            display_text,
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            color,
            2
        )

        cv2.imshow("System", frame)

        # ----------------------------
        # EXIT CONDITIONS
        # ----------------------------

        if success or (
            time.time() - start_time > 5
        ):

            if unknown_detected:

                play_alert()

            cv2.waitKey(2000)

            break

        if cv2.waitKey(1) == 27:

            break

    # ----------------------------
    # CLEANUP
    # ----------------------------

    cap.release()

    cv2.destroyAllWindows()

    return True