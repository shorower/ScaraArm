import tkinter as tk
import math
import serial  # Import the pyserial library
import time

class ScaraArmControl:
    def __init__(self, root):
        self.root = root
        self.root.title("SCARA Arm Control")
        
        # Initialize serial communication (make sure the correct port is used)
        # self.arduino = serial.Serial(port='/dev/cu.usbmodem101', baudrate=9600, timeout=1)  # Replace with your Arduino port
        self.arduino = serial.Serial(port='/dev/cu.usbmodem11201', baudrate=9600, timeout=1)  # Replace with your Arduino port
        time.sleep(2)  # Give some time for the connection to establish

        # Set canvas size to 1200x550
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

        # Button to add multiple (X, Y) values
        self.add_point_button = tk.Button(root, text="Add Point", command=self.add_point)
        self.add_point_button.grid(row=5, column=0, pady=10)

        # Button to process the points one by one
        self.process_button = tk.Button(root, text="Process All Points", command=self.process_points)
        self.process_button.grid(row=5, column=1, pady=10)

        # Control button for reset
        self.reset_button = tk.Button(root, text="Reset", command=self.reset_arm)
        self.reset_button.grid(row=5, column=2, pady=10)

        # Labels to display calculated angles (theta1 and theta2)
        self.theta1_label = tk.Label(root, text="Theta θ1:    0°")
        self.theta1_label.grid(row=3, column=4)
        self.theta2_label = tk.Label(root, text="Theta θ2:    0°")
        self.theta2_label.grid(row=4, column=4)

        # List to store multiple (X, Y) points
        self.points_list = []

        # Text box to display the points list
        self.points_text = tk.Text(root, height=28, width=15)
        self.points_text.grid(row=0, column=4, rowspan=6, padx=10)

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

        # print("Q1: ", Q1, "  ", "Q2: ", Q2)

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
        """Draw the SCARA arm with the gripper centered at the end."""
        base_angle_rad = math.radians(base_angle)
        elbow_angle_rad = math.radians(elbow_angle)

        origin_x = 600
        origin_y = 400

        shoulder_x = origin_x + self.link1_length * math.cos(base_angle_rad)
        shoulder_y = origin_y - self.link1_length * math.sin(base_angle_rad)

        elbow_x = shoulder_x + self.link2_length * math.cos(base_angle_rad + elbow_angle_rad)
        elbow_y = shoulder_y - self.link2_length * math.sin(base_angle_rad + elbow_angle_rad)

        self.canvas.create_line(origin_x, origin_y, shoulder_x, shoulder_y, width=5, fill="blue")
        self.canvas.create_line(shoulder_x, shoulder_y, elbow_x, elbow_y, width=5, fill="red")

        self.canvas.create_oval(origin_x - 5, origin_y - 5, origin_x + 5, origin_y + 5, fill='black')
        self.canvas.create_oval(shoulder_x - 5, shoulder_y - 5, shoulder_x + 5, shoulder_y + 5, fill='black')
        self.canvas.create_oval(elbow_x - 5, elbow_y - 5, elbow_x + 5, elbow_y + 5, fill='black')

        # Gripper dimensions (centered at end effector)
        gripper_width = 20
        gripper_length = 40
        gripper_x1 = elbow_x - gripper_length / 2
        gripper_y1 = elbow_y - gripper_width / 2
        gripper_x2 = elbow_x + gripper_length / 2
        gripper_y2 = elbow_y + gripper_width / 2

        self.canvas.create_rectangle(gripper_x1, gripper_y1, gripper_x2, gripper_y2, fill="green")

    def update_arm_from_inputs(self):
        """Updates the SCARA arm position based on angle input fields."""
        self.canvas.delete("all")
        self.draw_graph_paper()

        try:
            # Get joint angles from input fields
            base_angle = float(self.theta1_entry.get())
            elbow_angle = float(self.theta2_entry.get())
        except ValueError:
            print("Please enter valid numbers for angles.")
            return

        # Update angle labels
        self.theta1_label.config(text=f"θ1: {round(base_angle, 2)}°")
        self.theta2_label.config(text=f"θ2: {round(elbow_angle, 2)}°")

        # Draw the arm
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

    def add_point(self):
        """Adds a point (X, Y) to the points list."""
        try:
            # Get the X and Y values from the input fields
            x = int(self.x_entry.get())
            y = int(self.y_entry.get())
            self.points_list.append((x, y))  # Add point to the list
            print(f"Added point: ({x}, {y})")
            self.x_entry.delete(0, tk.END)
            self.y_entry.delete(0, tk.END)

            # Update the points list in the text box
            self.points_text.insert(tk.END, f"({x}, {y})\n")  # Display point in the text box
        except ValueError:
            print("Please enter valid numbers for X and Y coordinates.")

    def process_points(self, index=0):
        """Processes each (X, Y) point in the points list one by one."""
        if index < len(self.points_list):
            x, y = self.points_list[index]
            print(f"Processing point: ({x}, {y})")

            # Update the input fields with the current (x, y) values
            self.x_entry.delete(0, tk.END)
            self.x_entry.insert(0, str(x))
            self.y_entry.delete(0, tk.END)
            self.y_entry.insert(0, str(y))

            # Update the arm's position and draw the graph for this point
            self.update_arm()

            # Schedule the next point to be processed after 20 seconds (20000 milliseconds)
            self.root.after(15000, self.process_points, index + 1)


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
        self.theta1_label.config(text="Theta θ1:    0°")
        self.theta2_label.config(text="Theta θ2:    0°")
        self.points_list = []
        self.points_text.delete(1.0, tk.END)
        self.update_arm()


if __name__ == "__main__":
    root = tk.Tk()
    app = ScaraArmControl(root)
    root.mainloop()
