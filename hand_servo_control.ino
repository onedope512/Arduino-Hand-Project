/*
  Drives 5 servos (one per finger) on pins 3, 4, 5, 9, 10.
  Finger order (index 0-4) is assumed to be: thumb, index, middle, ring,
  pinky, wired to pins 3, 4, 5, 9, 10 respectively. If your physical wiring
  assigns fingers to pins differently, reorder SERVO_PINS and ASL_ANGLES
  to match.

  Serial command protocol (single ASCII char):
    'i'        -> increment all 5 servos by 10 degrees (clamped to 0-180)
    'r'        -> reset all 5 servos to the neutral 90 degree pose
    'A' - 'Z'  -> move directly to the ASL fingerspelling handshape for
                  that letter (0 = fully curled, 180 = fully extended)

  Note on ASL accuracy: this hand only has one open/close axis per finger,
  no thumb opposition, and no wrist rotation, so several letters are only
  rough approximations of the real handshape:
    - J and Z involve tracing a motion path and can't be represented as a
      static pose; they fall back to the closest static letter (I and D).
    - Letter pairs that differ mainly by finger crossing or spread instead
      of curl (e.g. U vs V, R, M vs N vs T) will look identical here.

  Setup:
    1. Upload this sketch to the Arduino.
    2. Wire 5 servos' signal wires to pins 3, 4, 5, 9, 10 (and power/ground
       from an external supply if your servos draw more current than the
       Arduino 5V pin can provide).
    3. Run gesture_hand_control.py or speech_to_asl.py on your computer.
*/

#include <Servo.h>

const int NUM_SERVOS = 5;
const int SERVO_PINS[NUM_SERVOS] = {3, 4, 5, 9, 10};
const int START_ANGLE = 90;
const int STEP_DEGREES = 10;

// Approximate ASL fingerspelling handshapes, in degrees, ordered
// {thumb, index, middle, ring, pinky}. 0 = curled, 180 = extended.
const int ASL_ANGLES[26][NUM_SERVOS] = {
  /* A */ {90, 0, 0, 0, 0},
  /* B */ {0, 180, 180, 180, 180},
  /* C */ {90, 90, 90, 90, 90},
  /* D */ {0, 180, 0, 0, 0},
  /* E */ {0, 0, 0, 0, 0},
  /* F */ {90, 90, 180, 180, 180},
  /* G */ {90, 180, 0, 0, 0},
  /* H */ {0, 180, 180, 0, 0},
  /* I */ {0, 0, 0, 0, 180},
  /* J */ {0, 0, 0, 0, 180},   // static fallback for I; real J adds motion
  /* K */ {90, 180, 180, 0, 0},
  /* L */ {180, 180, 0, 0, 0},
  /* M */ {0, 0, 0, 0, 0},
  /* N */ {0, 0, 0, 0, 0},
  /* O */ {90, 90, 90, 90, 90},
  /* P */ {90, 180, 180, 0, 0},
  /* Q */ {90, 180, 0, 0, 0},
  /* R */ {0, 180, 180, 0, 0},
  /* S */ {0, 0, 0, 0, 0},
  /* T */ {90, 0, 0, 0, 0},
  /* U */ {0, 180, 180, 0, 0},
  /* V */ {0, 180, 180, 0, 0},
  /* W */ {0, 180, 180, 180, 0},
  /* X */ {0, 90, 0, 0, 0},
  /* Y */ {180, 0, 0, 0, 180},
  /* Z */ {0, 180, 0, 0, 0},   // static fallback for D; real Z adds motion
};

Servo servos[NUM_SERVOS];
int angles[NUM_SERVOS];

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(SERVO_PINS[i]);
    angles[i] = START_ANGLE;
    servos[i].write(angles[i]);
  }
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();

    if (command == 'i') {
      for (int i = 0; i < NUM_SERVOS; i++) {
        angles[i] = min(angles[i] + STEP_DEGREES, 180);
        servos[i].write(angles[i]);
      }
      Serial.println("Incremented all 5 servos by 10 degrees");
    } else if (command == 'r') {
      for (int i = 0; i < NUM_SERVOS; i++) {
        angles[i] = START_ANGLE;
        servos[i].write(angles[i]);
      }
      Serial.println("Reset all 5 servos to 90 degrees");
    } else if (command >= 'A' && command <= 'Z') {
      int letterIndex = command - 'A';
      for (int i = 0; i < NUM_SERVOS; i++) {
        angles[i] = ASL_ANGLES[letterIndex][i];
        servos[i].write(angles[i]);
      }
      Serial.print("Formed ASL letter ");
      Serial.println(command);
    }
  }
}
