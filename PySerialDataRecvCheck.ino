float theta1,theta2;

void setup() {
  // Initialize serial communication at 9600 baud rate
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    int commaIndex = data.indexOf(',');
    if (commaIndex != -1) {
      theta1 = data.substring(0, commaIndex).toFloat();
      theta2 = data.substring(commaIndex + 1).toFloat();

      Serial.print("Theta1: ");
      Serial.print(theta1);
      Serial.print("  ,Theta2:  ");
      Serial.println(theta2);
    }
  }
}
