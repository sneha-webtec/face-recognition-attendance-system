import cv2
import os
import json
import numpy as np
DATASET_PATH = "dataset"

recognizer = cv2.face.LBPHFaceRecognizer_create()
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

faces = []
labels = []

label_map = {}
current_id = 0

print("🚀 Training started...")

for person_name in os.listdir(DATASET_PATH):

    person_path = os.path.join(DATASET_PATH, person_name)

    if not os.path.isdir(person_path):
        continue

    print(f"📁 Processing: {person_name}")

    # 🔥 FIX: Assign ID if not already present
    if person_name not in label_map:
        label_map[person_name] = current_id
        current_id += 1

    for image_name in os.listdir(person_path):

        image_path = os.path.join(person_path, image_name)

        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            continue

        detected = face_cascade.detectMultiScale(img, 1.3, 5)

        for (x, y, w, h) in detected:
            face = img[y:y+h, x:x+w]

            faces.append(face)
            labels.append(label_map[person_name])

# ----------------------------
# TRAIN MODEL
# ----------------------------
recognizer.train(faces, np.array(labels))

# SAVE MODEL
recognizer.save("model.yml")

# SAVE LABELS (IMPORTANT FORMAT)
labels_output = {str(v): k for k, v in label_map.items()}

with open("labels.json", "w") as f:
    json.dump(labels_output, f)

print("✅ Training completed!")
print("Label Map:", labels_output)