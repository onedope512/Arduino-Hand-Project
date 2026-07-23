# 5-DOF Robotic Hand

A robotic hand with 5 servos (one per finger) that can be driven two ways:

1. **Gesture control** — a webcam watches your hand, MediaPipe's Gesture Recognizer classifies the gesture, and the robotic hand nudges all 5 fingers in response.
2. **Speech-to-ASL fingerspelling** — a microphone listens to speech, transcribes it to text, and the robotic hand spells each word out letter-by-letter using an approximation of the ASL manual alphabet.

Both modes drive the same hardware and share the same Arduino sketch.

---

## Hardware

- Arduino Uno (or any Arduino with 5 PWM-capable pins)
- 5 hobby servos, one per finger, signal wires on pins **3, 4, 5, 9, 10**
- Finger assignment is assumed to be **thumb → pin 3, index → pin 4, middle → pin 5, ring → pin 9, pinky → pin 10**. If your hand is wired differently, reorder `SERVO_PINS` and the `ASL_ANGLES` table in the `.ino` file to match.
- An external 5V/6V power supply for the servos is strongly recommended — 5 servos moving together can exceed what the Arduino's onboard 5V regulator can safely supply. Share ground between the external supply and the Arduino.
- A webcam (for gesture mode) and a microphone (for speech mode).

---

## Files

| File | Role |
|---|---|
| [`hand_servo_control.ino`](hand_servo_control.ino) | Arduino sketch. Owns all 5 servos and the serial command protocol. Upload this once; both Python scripts talk to it. |
| [`gesture_hand_control.py`](gesture_hand_control.py) | Webcam → MediaPipe Gesture Recognizer → serial. Every recognized gesture bumps all 5 servos +10°. |
| [`speech_to_asl.py`](speech_to_asl.py) | Microphone → speech-to-text → serial. Fingerspells each recognized word on the hand. |
| [`servo_control.py`](servo_control.py) | Earlier, simpler test script — keyboard `g`/`h` keys move a single servo on pin 9. Not part of the gesture/speech pipeline; useful for sanity-checking wiring on one servo before running the full hand. |

Only one Python script should have the serial port open at a time (the Arduino IDE Serial Monitor must also be closed) — serial ports don't support multiple simultaneous clients.

---

## Serial Protocol

Both Python scripts talk to the Arduino over USB serial (9600 baud) using single ASCII-character commands:

| Command | Effect |
|---|---|
| `i` | Increment all 5 servos by 10° (clamped to 0–180°) |
| `r` | Reset all 5 servos to the neutral 90° pose |
| `A`–`Z` | Move directly to the ASL fingerspelling handshape for that letter |

The Arduino holds the current angle of each servo in memory and writes the new position immediately on each command — there's no interpolation/easing, so servos snap to the new pose.

---

## Setup

### 1. Arduino

Upload [`hand_servo_control.ino`](hand_servo_control.ino) via the Arduino IDE. It attaches all 5 servos on `setup()` and centers them at 90°.

### 2. Python environment

```bash
pip install opencv-python mediapipe pyserial SpeechRecognition pyaudio
```

On Windows, if `pyaudio` fails to build from source:

```bash
pip install pipwin
pipwin install pyaudio
```

### 3. Gesture Recognizer model (for `gesture_hand_control.py`)

Download `gesture_recognizer.task` and place it in this folder:
```
https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task
```

### 4. Serial port

In both `gesture_hand_control.py` and `speech_to_asl.py`, set `PORT` to your Arduino's port:
- Windows: `COM3` (check Device Manager → Ports)
- Mac: `/dev/cu.usbmodem14101` (run `ls /dev/cu.*`)
- Linux: `/dev/ttyACM0` or `/dev/ttyUSB0`

---

## Running

**Gesture mode:**
```bash
python gesture_hand_control.py
```
Shows a live camera window with the hand skeleton overlay and the recognized gesture name. Any recognized gesture (thumbs up, open palm, fist, victory, etc.) sends `i`, moving all 5 servos +10° — there's a 1-second cooldown so a held gesture doesn't spam the servos. Press **Esc** to quit.

**Speech-to-ASL mode:**
```bash
python speech_to_asl.py
```
Calibrates briefly for ambient noise, then listens continuously. Each recognized phrase is split into words; each word is fingerspelled letter-by-letter (servo holds each handshape ~1.2s), then the hand resets to neutral before the next word. Press **Ctrl+C** to quit.

`speech_to_asl.py` uses `SpeechRecognition`'s default `recognize_google()` engine, which sends short audio clips to Google's free web API for transcription — no API key needed, but it requires an internet connection and sends audio off the machine. Swap in an offline engine (e.g. the `vosk` package) if that's not acceptable for your use case.

---

## How Gesture Mode Works

1. `cv2.VideoCapture` grabs frames from the webcam.
2. Each frame is converted to an `mp.Image` and passed to `GestureRecognizer.recognize_for_video()`, running MediaPipe's bundled gesture classification model (built on top of its hand-landmark detector).
3. The top-ranked gesture category (`Thumb_Up`, `Open_Palm`, `Closed_Fist`, `Victory`, etc.) is read from the result.
4. If a gesture other than `"None"` is seen and the cooldown has elapsed, the script writes `b"i"` to serial.
5. Hand landmarks are drawn on the frame for visual feedback, along with the current gesture name.

This is intentionally a placeholder mapping: **every** gesture currently does the same thing (nudge all 5 servos identically) rather than driving each finger independently. A natural next step is mapping specific gestures, or individual landmark angles, to individual servos.

---

## How Speech-to-ASL Mode Works

1. `sr.Microphone()` + `Recognizer.listen()` captures a phrase of speech bounded by silence.
2. `recognize_google()` transcribes it to text.
3. The text is split into words; each word is upper-cased and iterated letter by letter (non-letter characters are skipped).
4. Each letter is sent as its own ASCII character over serial. The Arduino looks it up in its `ASL_ANGLES` table and moves all 5 servos directly to that letter's handshape (not an increment — an absolute pose).
5. After each word, `r` is sent to relax the hand to neutral before the next word.

### ASL Accuracy — Known Limitations

This hand has **one open/curl axis per finger** and no thumb opposition or wrist rotation, so it can only approximate real ASL fingerspelling:

- **J and Z** involve tracing a motion path in real ASL. Since the hand can only hold static poses, they fall back to their closest static letter (I and D respectively) — the motion itself isn't reproduced.
- **U vs V**, **R**, and **M vs N vs T** differ in real ASL mainly by finger crossing or spread, not curl amount — these will look identical or near-identical on this hardware.
- This is fingerspelling only, not full ASL. Real ASL has its own grammar, facial/non-manual markers, and whole-word signs that a static 5-servo hand cannot represent — this project spells words out letter-by-letter, which is a valid (if slow) part of ASL, but is not equivalent to fluent signing.

---

## Extending Further

- **Real finger-by-finger gesture mapping**: instead of `GestureRecognizer`'s whole-hand classification, use MediaPipe's raw hand landmarks and compute per-finger curl angles directly, then map each finger's real-world bend to its corresponding servo — this would make gesture mode actually mirror the user's hand instead of just nudging everything uniformly.
- **Smoothing/interpolation**: the Arduino currently snaps servos straight to the target angle; adding a small step-and-delay loop in `loop()` would let the hand ease between poses instead of jerking.
- **Offline speech recognition**: swap `recognize_google()` for the `vosk` package to transcribe without sending audio to an external service.
- **Two-way calibration**: expose a serial command to set custom neutral/min/max angles per servo, since real servo horns and finger linkages rarely land exactly on 0°/90°/180°.
