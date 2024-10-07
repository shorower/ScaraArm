import speech_recognition as sr
import re
import serial
import time
import math



# Initialize the recognizer
r = sr.Recognizer()

arduino = serial.Serial(port='/dev/cu.usbmodem11201', baudrate=9600, timeout=1)  # Replace with your Arduino port
print("Connecting....")
time.sleep(10)

def recognize_speech():
    try:
        # Use the microphone as source for input
        with sr.Microphone() as source:
            print("Adjusting for ambient noise...")
            r.adjust_for_ambient_noise(source, duration=1)
            print("Listening... Please speak X-axis and Y-axis values.")
            
            # Listen for the user's input
            audio = r.listen(source)

            # Using Google's speech recognition
            speech_text = r.recognize_google(audio)
            print(f"You said: {speech_text}")
            return speech_text.lower()

    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
    return None

def extract_axis_values(speech_text):
    # Regular expression to match values like 'X-axis 10' or 'Y-axis 20'
    x_match = re.search(r"x[-\s]?axis[\s\-]?(\d+)", speech_text)
    y_match = re.search(r"y[-\s]?axis[\s\-]?(\d+)", speech_text)

    x_value = int(x_match.group(1)) if x_match else None
    y_value = int(y_match.group(1)) if y_match else None

    return x_value, y_value

def send_angles_to_arduino(x_value, y_value):
        """Send angles Q1 and Q2 to Arduino via serial communication."""
        try:
            # Prepare data to send, formatted as "Q1,Q2\n"
            data = f"{round(x_value, 2)},{round(y_value, 2)}\n"
            arduino.write(data.encode())  # Send data to Arduino
            print(f"Sent to Arduino: {data.strip()}")
        except Exception as e:
            print(f"Error sending data to Arduino: {e}")

def inverse_kinematics(x, y):
        """Calculates the joint angles for given x, y coordinates using inverse kinematics."""
        l1 = 290
        l2 = 180

        # Calculate the distance from the base to the target point
        r = math.sqrt(x**2 + y**2)

        if r > l1 + l2 or r < abs(l1 - l2):
            print("Point is out of reach for the arm.")
            return None, None  # Out of reach
        
        # Inverse Kinematics equations
        cos_angle2 = (r**2 - l1**2 - l2**2) / (2 * l1 * l2)
        angle2 = math.acos(cos_angle2)  # Elbow angle

        k1 = l1 + l2 * math.cos(angle2)
        k2 = l2 * math.sin(angle2)
        angle1 = math.atan2(y, x) - math.atan2(k2, k1)  # Base angle

        global Q1
        Q1 = math.degrees(angle1)
        global Q2
        Q2 = math.degrees(angle2)

        # print("Q1: ", Q1, "  ", "Q2: ", Q2)

        return Q1, Q2

if __name__ == "__main__":
    # Get the recognized speech
    
    while True:
        speech_text = recognize_speech() 
        
        if speech_text:
            # Extract X and Y axis values
            x_value, y_value = extract_axis_values(speech_text)
            
            # Output the results
            if x_value is not None and y_value is not None:
                inverse_kinematics(x_value, y_value)
                send_angles_to_arduino(Q1, Q2)
                print(f"X-axis value: {x_value}")
                print(f"Y-axis value: {y_value}")
            else:
                print("Could not find axis values in your speech. Please mention them clearly.")
