import tkinter as tk
import math
import serial  # Import the pyserial library
import time



class ScaraArmControl:
    def __init__(self, root):
        self.root = root
        self.root.title("SCARA Arm Control")
        
        # Initialize serial communication (make sure the correct port is used)
        self.arduino = serial.Serial(port='/dev/cu.usbmodem101', baudrate=9600, timeout=1)  # Replace with your Arduino port
        time.sleep(2)  # Give some time for the connection to establish

        # Set canvas size to 800x500
        self.canvas = tk.Canvas(root, width=1200, height=550, bg='white')
        self.canvas.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
        
        # Draw graph paper background with millimeter units
        self.draw_graph_paper()

        # SCARA arm lengths (in millimeters)
        self.link1_length = 290  # First link length (mm)
        self.link2_length = 180  # Second link length (mm)

        # X and Y coordinate input fields
        self.create_input_field("X Coordinate (mm):", 1, 0)
        self.create_input_field("Y Coordinate (mm):", 2, 0)

        # Input fields for Q1 and Q2 angles
        self.create_input_field("Base Angle θ1 (degrees):", 3, 0)
        self.create_input_field("Elbow Angle θ2 (degrees):", 4, 0)

        # Button to move the arm based on input coordinates
        self.move_button = tk.Button(root, text="Move to Position", command=self.update_arm)
        self.move_button.grid(row=1, column=2, pady=10)

        # Button to set angles from input fields
        self.set_angles_button = tk.Button(root, text="Set Angles", command=self.update_arm_from_inputs)
        self.set_angles_button.grid(row=3, column=2, pady=10)

        # Control button for reset
        self.reset_button = tk.Button(root, text="Reset", command=self.reset_arm)
        self.reset_button.grid(row=4, column=2, pady=10)

        # Labels to display calculated angles (theta1 and theta2)
        self.theta1_label = tk.Label(root, text="Theta θ1:    0°")
        self.theta1_label.grid(row=3, column=4)
        self.theta2_label = tk.Label(root, text="Theta θ2:    0°")
        self.theta2_label.grid(row=4, column=4)

        # Initial drawing of SCARA arm
        self.update_arm()

    def create_input_field(self, text, row, col):
        """Create a label and entry field for input."""
        label = tk.Label(self.root, text=text)
        label.grid(row=row, column=col)

        entry = tk.Entry(self.root)
        entry.grid(row=row, column=col + 1)
        entry.insert(0, " ")  # Default value 0

        if "X" in text:
            self.x_entry = entry
        elif "Y" in text:
            self.y_entry = entry
        elif "θ1" in text:
            self.theta1_entry = entry
        else:
            self.theta2_entry = entry

    def draw_graph_paper(self):
        """Draws a graph paper-like background on the canvas with units in millimeters."""
        # Grid size for graph paper (20 pixels = 20 millimeters)
        grid_size = 20

        # Origin of the graph (center of the canvas)
        origin_x = 600
        origin_y = 400

        # Draw vertical lines with unit labels
        for x in range(0, 1200, grid_size):
            self.canvas.create_line(x, 0, x, 550, fill='lightgray')
            distance_from_origin = (x - origin_x)  # Distance from the center
            if x != origin_x:  # Skip the center point for labeling
                self.canvas.create_text(x, origin_y, text=f"{distance_from_origin} mm", fill='black', font=('Arial', 8), angle=90)

        # Draw horizontal lines with unit labels
        for y in range(0, 550, grid_size):
            self.canvas.create_line(0, y, 1200, y, fill='lightgray')
            distance_from_origin = (origin_y - y)  # Distance from the center
            if y != origin_y:  # Skip the center point for labeling
                self.canvas.create_text(origin_x, y, text=f"{distance_from_origin} mm", fill='black', font=('Arial', 8))

    def inverse_kinematics(self, x, y):
        """Calculates the joint angles for given x, y coordinates using inverse kinematics."""
        l1 = self.link1_length
        l2 = self.link2_length

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

        print("Q1: ", Q1, "  ", "Q2: ", Q2)

        return Q1, Q2

    def update_arm(self):
        """Updates the SCARA arm position based on the X, Y input fields."""
        # Clear the canvas and redraw graph paper
        self.canvas.delete("all")
        self.draw_graph_paper()

        try:
            # Get X and Y positions from input fields
            x = float(self.x_entry.get())
            y = float(self.y_entry.get())
        except ValueError:
            print("Please enter valid numbers for X and Y coordinates.")
            return

        # Perform inverse kinematics to find the joint angles
        base_angle, elbow_angle = self.inverse_kinematics(x, y)

        if base_angle is None or elbow_angle is None:
            return  # Skip drawing if the point is out of reach

        # Update angle labels
        self.theta1_label.config(text=f"θ1: {round(base_angle, 2)}°")
        self.theta2_label.config(text=f"θ2: {round(elbow_angle, 2)}°")

        # Draw the arm
        self.draw_arm(base_angle, elbow_angle)

        # Send angles to Arduino
        self.send_angles_to_arduino(Q1, Q2)

    def draw_arm(self, base_angle, elbow_angle):
        """Draw the SCARA arm on the canvas given the angles."""
        # Convert angles to radians for the calculations
        base_angle_rad = math.radians(base_angle)
        elbow_angle_rad = math.radians(elbow_angle)

        # Origin of the SCARA arm (center of the canvas)
        origin_x = 600
        origin_y = 400
        
        # Calculate position of first joint (shoulder)
        shoulder_x = origin_x + self.link1_length * math.cos(base_angle_rad)
        shoulder_y = origin_y - self.link1_length * math.sin(base_angle_rad)
        
        # Calculate position of second joint (elbow)
        elbow_x = shoulder_x + self.link2_length * math.cos(base_angle_rad + elbow_angle_rad)
        elbow_y = shoulder_y - self.link2_length * math.sin(base_angle_rad + elbow_angle_rad)

        # Draw the arm on the canvas
        self.canvas.create_line(origin_x, origin_y, shoulder_x, shoulder_y, width=5, fill="blue")  # Link 1
        self.canvas.create_line(shoulder_x, shoulder_y, elbow_x, elbow_y, width=5, fill="red")    # Link 2

        # Draw joints
        self.canvas.create_oval(origin_x - 5, origin_y - 5, origin_x + 5, origin_y + 5, fill='black')  # Base joint
        self.canvas.create_oval(shoulder_x - 5, shoulder_y - 5, shoulder_x + 5, shoulder_y + 5, fill='black')  # Shoulder joint
        self.canvas.create_oval(elbow_x - 5, elbow_y - 5, elbow_x + 5, elbow_y + 5, fill='black')  # Elbow joint

    def update_arm_from_inputs(self):
        """Updates the SCARA arm position based on input fields for Q1 and Q2 angles."""
        try:
            # Get angles from input fields
            base_angle = float(self.theta1_entry.get())
            elbow_angle = float(self.theta2_entry.get())
        except ValueError:
            print("Please enter valid numbers for θ1 and θ2.")
            return

        # Update angle labels
        self.theta1_label.config(text=f"θ1: {round(base_angle, 2)}°")
        self.theta2_label.config(text=f"θ2: {round(elbow_angle, 2)}°")

        # Clear the canvas and redraw graph paper
        self.canvas.delete("all")
        self.draw_graph_paper()

        # Draw the arm using the input angles
        self.draw_arm(base_angle, elbow_angle)

        # Send angles to Arduino
        self.send_angles_to_arduino(base_angle, elbow_angle)
        

    def send_angles_to_arduino(self, base_angle, elbow_angle):
        """Send angles Q1 and Q2 to Arduino via serial communication."""
        try:
            # Prepare data to send, formatted as "Q1,Q2\n"
            data = f"{round(base_angle, 2)},{round(elbow_angle, 2)}\n"
            self.arduino.write(data.encode())  # Send data to Arduino
            print(f"Sent to Arduino: {data.strip()}")
        except Exception as e:
            print(f"Error sending data to Arduino: {e}")

    def reset_arm(self):
        """Resets the SCARA arm to the initial position."""
        self.x_entry.delete(0, tk.END)
        self.x_entry.insert(0, " ")
        self.y_entry.delete(0, tk.END)
        self.y_entry.insert(0, " ")
        self.theta1_entry.delete(0, tk.END)
        self.theta1_entry.insert(0, "0")
        self.theta2_entry.delete(0, tk.END)
        self.theta2_entry.insert(0, "0")
        self.update_arm()

# Create the main window
root = tk.Tk()
scara_control = ScaraArmControl(root)
root.mainloop()
