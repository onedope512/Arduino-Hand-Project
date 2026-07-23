/*
  Drives 5 servos (one per finger) on pins 3, 4, 5, 9, 10.
  Receives single-char commands over serial from gesture_hand_control.py:
    'i' -> increment all 5 servos by 10 degrees (clamped to 0-180)
    'r' -> reset all 5 servos back to 90 degrees

  Setup:
    1. Upload this sketch to the Arduino.
    2. Wire 5 servos' signal wires to pins 3, 4, 5, 9, 10 (and power/ground
       from an external supply if your servos draw more current than the
       Arduino 5V pin can provide).
    3. Run gesture_hand_control.py on your computer.
*/

#include <Servo.h>

const int NUM_SERVOS = 5;
const int SERVO_PINS[NUM_SERVOS] = {3, 4, 5, 9, 10};
const int START_ANGLE = 90;
const int STEP_DEGREES = 10;

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
    }
  }
}
