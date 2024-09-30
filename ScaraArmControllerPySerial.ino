#include <AccelStepper.h>

// Define stepper motor connections and motor interface type
#define motorInterfaceType 1 // 1 for 2 wire stepper (step and direction)

// Pins for stepper motors
#define stepPin1 3
#define dirPin1 2

#define stepPin2 4
#define dirPin2 5

#define stepPin3 7
#define dirPin3 6

#define stepPin4 8
#define dirPin4 9

// Initialize stepper motors
AccelStepper stepper1(motorInterfaceType, stepPin1, dirPin1); // Base Rotation
AccelStepper stepper2(motorInterfaceType, stepPin2, dirPin2); // Arm Joint 1
AccelStepper stepper3(motorInterfaceType, stepPin3, dirPin3); // Arm Joint 2
AccelStepper stepper4(motorInterfaceType, stepPin4, dirPin4); // Gripper

// Variables to store the current angles
float currentAngle1 = 0; // Base
float currentAngle2 = 0; // Arm Joint 1
float currentAngle3 = 0; // Arm Joint 2
float currentAngle4 = 0; // Gripper
float theta1, theta2, gripper_theta;

void setup() {
  // Set maximum speed and acceleration for each stepper motor
  stepper1.setMaxSpeed(1000);
  stepper1.setAcceleration(500);

  stepper2.setMaxSpeed(1000);
  stepper2.setAcceleration(500);

  stepper3.setMaxSpeed(300);
  stepper3.setAcceleration(100);

  stepper4.setMaxSpeed(1000);
  stepper4.setAcceleration(500);

  Serial.begin(9600);
  Serial.println("SCARA Arm with 4 Motors Controller Ready");
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    int commaIndex = data.indexOf(',');
    if (commaIndex != -1) {
      theta1 = data.substring(0, commaIndex).toFloat();
      theta2 = data.substring(commaIndex + 1).toFloat();
      gripper_theta = -(theta1 + theta2);

      Serial.print("Theta1: ");
      Serial.print(theta1);
      Serial.print("  ,Theta2:  ");
      Serial.print(theta2);
      Serial.print("  ,gripper_theta:  ");
      Serial.println(gripper_theta);
    }
  }



  // Set target angles for simultaneous movement
  moveToTargetAngles(theta1, -theta2, -2000, 0);  // Base: 30, Arm Joint 1: 45, Arm Joint 2: 60, Gripper: 15
  delay(2000);
}

// Function to move all joints to target angles simultaneously
void moveToTargetAngles(float targetAngle1, float targetAngle2, float targetAngle3, float targetAngle4) {
  // Calculate steps for each joint
  long steps1 = angleToSteps(targetAngle1 - currentAngle1);
  long steps2 = angleToSteps(targetAngle2 - currentAngle2);
  long steps3 = angleToSteps(targetAngle3 - currentAngle3);
  long steps4 = angleToSteps(targetAngle4 - currentAngle4);

  // Set target positions for all steppers
  stepper1.move(steps1*3);
  stepper2.move(steps2*3);
  stepper3.move(steps3);
  stepper4.move(steps4);

  // Run all steppers simultaneously using run()
  while (stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0 || stepper3.distanceToGo() != 0 || stepper4.distanceToGo() != 0) {
    stepper1.run();  // Incrementally move stepper 1 (Base)
    stepper2.run();  // Incrementally move stepper 2 (Arm Joint 1)
    stepper3.run();  // Incrementally move stepper 3 (Arm Joint 2)
    stepper4.run();  // Incrementally move stepper 4 (Gripper)
  }

  // Update current angles after movement
  currentAngle1 = targetAngle1;
  currentAngle2 = targetAngle2;
  currentAngle3 = targetAngle3;
  currentAngle4 = targetAngle4;
}

// Function to convert an angle (degrees) to steps for stepper motor
long angleToSteps(float angle) {
  const float stepsPerRevolution = 3200.0;  // Assuming 200 steps per revolution
  const float degreesPerStep = 360.0 / stepsPerRevolution;
  return (long)(angle / degreesPerStep);
}
