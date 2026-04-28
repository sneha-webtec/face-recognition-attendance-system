import cv2
import os
import time

# ----------------------------
# CONFIG
# ----------------------------
person_name = input("Enter name: ").strip().lower()
dataset_path = "dataset"
save_path = os.path.join(dataset_path, person_name)

os.makedirs(save_path, exist_ok=True)

MAX_IMAGES = 80
CAPTURE_DELAY = 0.3  # seconds

# ----------------------------
# FACE DETECTOR
# ----------------------------
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

cv2.namedWindow("Capture Faces", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Capture Faces", 800, 600)

print("📸 Look at camera and move slightly (left/right/up/down)")

count = 0
last_capture_time = time.time()

while count < MAX_IMAGES:

    ret, frame = cap.read()
    if not ret:
        break

    display_frame = frame.copy()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:

        current_time = time.time()

        # capture every few milliseconds
        if current_time - last_capture_time > CAPTURE_DELAY:

            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (200, 200))

            # lighting normalization
            face = cv2.equalizeHist(face)

            file_name = os.path.join(save_path, f"{count}.jpg")
            cv2.imwrite(file_name, face)

            count += 1
            last_capture_time = current_time

        # draw box
        cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0,255,0), 2)
        cv2.putText(display_frame, f"{count}/{MAX_IMAGES}",
                    (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0,255,0), 2)

        break

    cv2.imshow("Capture Faces", display_frame)

    key = cv2.waitKey(1)
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()

print("✅ Dataset captured successfully!")