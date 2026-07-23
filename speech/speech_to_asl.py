"""
Listens to your microphone, transcribes speech to text with the
SpeechRecognition library, and sends each letter of each recognized word
over serial to an Arduino (running hand_servo_control.ino), which forms
the ASL fingerspelling handshape for that letter on a 5-servo robotic hand.

Hardware limits (see hand_servo_control.ino for details): the hand only
opens/curls each finger on one axis, with no thumb opposition or wrist
rotation, so this can only approximate real ASL fingerspelling. J and Z
(which involve tracing a motion) fall back to their closest static letter,
and a few letter pairs that differ mainly by finger crossing or spread
(e.g. U/V, R, M/N/T) will look identical on this hand.

Setup:
    pip install SpeechRecognition pyaudio pyserial

    On Windows, if `pip install pyaudio` fails to build, use a prebuilt
    wheel instead:
        pip install pipwin
        pipwin install pyaudio

Before running:
    1. Upload hand_servo_control.ino to the Arduino.
    2. Set PORT below to your Arduino's serial port:
         Windows: something like "COM3"  (check Device Manager > Ports)
         Mac:     something like "/dev/cu.usbmodem14101" (run `ls /dev/cu.*`)
         Linux:   something like "/dev/ttyACM0" or "/dev/ttyUSB0"
    3. Close the Arduino IDE Serial Monitor if it's open (only one program
       can use the serial port at a time).

Run:
    python speech_to_asl.py

Speak a word or short phrase -> the script transcribes it and fingerspells
each word on the robotic hand, one letter at a time. Press Ctrl+C to quit.

Note: recognize_google() uses SpeechRecognition's default free web API,
which sends short audio clips to Google over the internet for
transcription. It requires no API key but does require an internet
connection. Swap in an offline engine (e.g. the `vosk` package) if you'd
rather not send audio off the machine.
"""

import string
import time

import serial
import speech_recognition as sr

PORT = "COM3"  # <-- change this to your Arduino's port
BAUD_RATE = 9600
SECONDS_PER_LETTER = 1.2  # time to hold each handshape before the next letter
SECONDS_BETWEEN_WORDS = 1.5  # pause with hand reset to neutral between words

ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # wait for the Arduino to reset after opening the serial connection

recognizer = sr.Recognizer()
microphone = sr.Microphone()

with microphone as source:
    print("Calibrating for ambient noise...")
    recognizer.adjust_for_ambient_noise(source, duration=1)


def fingerspell(word: str) -> None:
    for letter in word.upper():
        if letter not in string.ascii_uppercase:
            continue
        ser.write(letter.encode())
        print(f"  -> forming letter '{letter}'")
        time.sleep(SECONDS_PER_LETTER)

    ser.write(b"r")  # relax hand to neutral before the next word
    time.sleep(SECONDS_BETWEEN_WORDS)


print("Listening for speech (Ctrl+C to quit)...")
try:
    while True:
        with microphone as source:
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            continue
        except sr.RequestError as exc:
            print(f"Speech recognition service error: {exc}")
            continue

        print(f"Heard: {text}")
        for word in text.split():
            fingerspell(word)
except KeyboardInterrupt:
    print("Exiting.")
finally:
    ser.close()
