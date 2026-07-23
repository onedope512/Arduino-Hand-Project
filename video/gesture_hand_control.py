"""
Records video from your webcam, runs MediaPipe's Gesture Recognizer on each
frame, and sends a serial command to an Arduino whenever a hand gesture is
detected. The Arduino (running hand_servo_control.ino) moves all 5 servos
(one per finger, on pins 3, 4, 5, 9, 10) by +10 degrees each time a gesture
fires. This is a placeholder mapping: for now every recognized gesture just
nudges every servo the same amount, rather than driving each finger
independently.

Setup:
    pip install opencv-python mediapipe pyserial

    Download the gesture recognizer model file and place it next to this
    script as "gesture_recognizer.task":
        https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task

Before running:
    1. Upload hand_servo_control.ino to the Arduino.
    2. Set PORT below to your Arduino's serial port:
         Windows: something like "COM3"  (check Device Manager > Ports)
         Mac:     something like "/dev/cu.usbmodem14101" (run `ls /dev/cu.*`)
         Linux:   something like "/dev/ttyACM0" or "/dev/ttyUSB0"
    3. Close the Arduino IDE Serial Monitor if it's open (only one program
       can use the serial port at a time).

Run:
    python gesture_hand_control.py

Show a hand gesture (thumbs up, open palm, fist, etc.) to the webcam ->
all 5 servos move +10 degrees. Press Esc to quit.
"""

import time

import cv2
import mediapipe as mp
import serial
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

PORT = "COM3"  # <-- change this to your Arduino's port
BAUD_RATE = 9600
MODEL_PATH = "gesture_recognizer.task"
GESTURE_COOLDOWN_SECONDS = 1.0  # minimum time between servo moves

ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # wait for the Arduino to reset after opening the serial connection

base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.GestureRecognizerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
)
recognizer = vision.GestureRecognizer.create_from_options(options)

mp_hands_connections = mp.solutions.hands.HAND_CONNECTIONS

cap = cv2.VideoCapture(0)
last_move_time = 0.0

try:
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int(time.time() * 1000)
        result = recognizer.recognize_for_video(mp_image, timestamp_ms)

        gesture_name = "None"
        if result.gestures:
            gesture_name = result.gestures[0][0].category_name

            if gesture_name != "None" and (time.time() - last_move_time) > GESTURE_COOLDOWN_SECONDS:
                ser.write(b"i")
                last_move_time = time.time()
                print(f"Gesture '{gesture_name}' detected -> all 5 servos +10 degrees")

        if result.hand_landmarks:
            h, w, _ = frame.shape
            for hand_landmarks in result.hand_landmarks:
                points = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]
                for start, end in mp_hands_connections:
                    cv2.line(frame, points[start], points[end], (0, 255, 0), 2)
                for point in points:
                    cv2.circle(frame, point, 3, (0, 0, 255), -1)

        cv2.putText(
            frame, f"Gesture: {gesture_name}", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2,
        )
        cv2.imshow("Gesture -> Servo Control", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # Esc
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    recognizer.close()
    ser.close()
