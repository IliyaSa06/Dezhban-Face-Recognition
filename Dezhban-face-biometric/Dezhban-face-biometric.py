import cv2
import face_recognition
import numpy as np
import mysql.connector
from datetime import datetime
import os
import pickle
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import webbrowser
from tkinter import font as tkfont
import threading

# Database connection settings
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'face_attendance'
}


class ModernButton(tk.Canvas):
    def __init__(self, master=None, text="", command=None, width=200, height=40,
                 color="#4a6baf", hover_color="#3a5a9f", text_color="white",
                 corner_radius=10, icon=None, *args, **kwargs):
        super().__init__(master, width=width, height=height,
                         highlightthickness=0, *args, **kwargs)

        self.command = command
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.text = text
        self.icon = icon

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

        self.draw_button()

    def draw_button(self, color=None):
        self.delete("all")
        bg_color = color if color else self.color

        # Draw rounded rectangle
        self.create_rounded_rect(0, 0, self.winfo_reqwidth(), self.winfo_reqheight(),
                                 radius=self.corner_radius, fill=bg_color)

        # Add text
        text_x = self.winfo_reqwidth() // 2
        if self.icon:
            text_x += 15
            img = tk.PhotoImage(file=self.icon)
            self.icon_img = img  # Keep reference
            self.create_image(25, self.winfo_reqheight() // 2, image=img)

        self.create_text(text_x, self.winfo_reqheight() // 2,
                         text=self.text, fill=self.text_color,
                         font=('Helvetica', 10, 'bold'))

    def create_rounded_rect(self, x1, y1, x2, y2, radius=10, **kwargs):
        points = [x1 + radius, y1,
                  x2 - radius, y1,
                  x2, y1,
                  x2, y1 + radius,
                  x2, y2 - radius,
                  x2, y2,
                  x2 - radius, y2,
                  x1 + radius, y2,
                  x1, y2,
                  x1, y2 - radius,
                  x1, y1 + radius,
                  x1, y1]

        return self.create_polygon(points, **kwargs, smooth=True)

    def on_enter(self, event):
        self.draw_button(self.hover_color)

    def on_leave(self, event):
        self.draw_button(self.color)

    def on_click(self, event):
        if self.command:
            self.command()


class ModernApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dezhban Attendance System")
        self.geometry("1000x700")
        self.configure(bg="#2a2a2a")

        # Load custom font
        try:
            self.custom_font = tkfont.Font(family="Arial", size=12)
        except:
            self.custom_font = tkfont.Font(family="Helvetica", size=12)

        # Initialize camera-related variables
        self.current_camera_index = 0
        self.available_cameras = self.detect_available_cameras()

        # If no cameras found, show error and exit
        if not self.available_cameras:
            messagebox.showerror("Error", "No camera found! Please check camera connection.")
            self.destroy()
            return

        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        self.last_attendance = {}

        self.setup_ui()

        # Load face data in background
        threading.Thread(target=self.load_face_data, daemon=True).start()

    def detect_available_cameras(self):
        cameras = []
        # Try up to 5 cameras
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    cameras.append(i)
                cap.release()
            else:
                cap.release()
        return cameras

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self, bg="#2a2a2a")
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        title_label = tk.Label(header_frame, text="Dezhban Attendance System",
                               font=(self.custom_font.actual()['family'], 18, 'bold'),
                               bg="#2a2a2a", fg="white")
        title_label.pack(side=tk.LEFT)

        # Main content
        main_frame = tk.Frame(self, bg="#2a2a2a")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left panel (controls)
        left_panel = tk.Frame(main_frame, bg="#3a3a3a", bd=0, highlightthickness=0,
                              relief=tk.RIDGE)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        left_panel.configure(width=250)

        # Right panel (display)
        right_panel = tk.Frame(main_frame, bg="#3a3a3a", bd=0, highlightthickness=0,
                               relief=tk.RIDGE)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Add controls to left panel
        control_title = tk.Label(left_panel, text="Operations Menu",
                                 font=(self.custom_font.actual()['family'], 12, 'bold'),
                                 bg="#3a3a3a", fg="white")
        control_title.pack(pady=(20, 10))

        # Buttons
        btn1 = ModernButton(left_panel, text="Register New Employee",
                            command=self.register_employee,
                            color="#4a6baf", hover_color="#3a5a9f",
                            width=220, height=45)
        btn1.pack(pady=10)

        btn2 = ModernButton(left_panel, text="Start Attendance",
                            command=self.start_attendance,
                            color="#4a8f7a", hover_color="#3a7f6a",
                            width=220, height=45)
        btn2.pack(pady=10)

        # Camera selection dropdown
        if len(self.available_cameras) > 1:
            camera_frame = tk.Frame(left_panel, bg="#3a3a3a")
            camera_frame.pack(pady=10)

            tk.Label(camera_frame, text="Select Camera:",
                     bg="#3a3a3a", fg="white").pack(side=tk.TOP, anchor=tk.W)

            self.camera_var = tk.StringVar()
            self.camera_var.set(f"Camera 1 (Index {self.available_cameras[0]})")

            camera_options = [f"Camera {i + 1} (Index {cam})" for i, cam in enumerate(self.available_cameras)]
            camera_dropdown = ttk.Combobox(camera_frame, textvariable=self.camera_var,
                                           values=camera_options, state="readonly")
            camera_dropdown.pack(fill=tk.X, pady=5)
            camera_dropdown.bind("<<ComboboxSelected>>", self.change_camera)

        # Status bar
        status_frame = tk.Frame(left_panel, bg="#2a2a2a")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        self.status_label = tk.Label(status_frame, text="Ready to work...",
                                     font=(self.custom_font.actual()['family'], 9),
                                     bg="#2a2a2a", fg="#aaaaaa")
        self.status_label.pack(pady=5)

        # Add display area to right panel
        self.display_frame = tk.Frame(right_panel, bg="#3a3a3a")
        self.display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Camera preview placeholder
        self.camera_label = tk.Label(self.display_frame, bg="#2a2a2a")
        self.camera_label.pack(fill=tk.BOTH, expand=True)

        # Log console
        log_frame = tk.Frame(right_panel, bg="#2a2a2a")
        log_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        log_title = tk.Label(log_frame, text="Activity Log",
                             font=(self.custom_font.actual()['family'], 10),
                             bg="#2a2a2a", fg="white")
        log_title.pack(anchor=tk.W, padx=5, pady=5)

        self.log_text = tk.Text(log_frame, height=8, width=80, bg="#1a1a1a",
                                fg="white", insertbackground="white",
                                font=(self.custom_font.actual()['family'], 9))
        self.log_text.pack(fill=tk.X, padx=5, pady=(0, 5))

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical",
                                  command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Footer
        footer_frame = tk.Frame(self, bg="#2a2a2a")
        footer_frame.pack(fill=tk.X, padx=20, pady=(5, 10))

        version_label = tk.Label(footer_frame, text="Version 2.0 - Designed by Iliya Saiedi",
                                 font=(self.custom_font.actual()['family'], 8),
                                 bg="#2a2a2a", fg="#666666")
        version_label.pack(side=tk.LEFT)

    def change_camera(self, event=None):
        selected_index = int(self.camera_var.get().split(" ")[1]) - 1
        if 0 <= selected_index < len(self.available_cameras):
            self.current_camera_index = selected_index
            self.log_message(f"Changed camera to Camera {self.current_camera_index + 1}")
        else:
            self.log_message("Error in camera selection")

    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        # Update status label
        self.status_label.config(text=message[:50] + "...")

    def connect_db(self):
        try:
            conn = mysql.connector.connect(**db_config)
            return conn
        except mysql.connector.Error as err:
            self.log_message(f"Database connection error: {err}")
            return None

    def load_face_data(self):
        conn = self.connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT employee_id, name, face_encoding FROM employees")
            results = cursor.fetchall()

            for employee_id, name, face_encoding in results:
                try:
                    encoding = pickle.loads(face_encoding.encode('latin1'))
                    self.known_face_encodings.append(encoding)
                    self.known_face_ids.append(employee_id)
                    self.known_face_names.append(name)
                except Exception as e:
                    self.log_message(f"Error loading face data for {name}: {e}")

            cursor.close()
            conn.close()
            self.log_message(f"Data loading completed. {len(self.known_face_names)} known faces.")

    def register_employee(self):
        self.log_message("Starting new employee registration process")

        name = simpledialog.askstring("Registration", "Enter employee name:", parent=self)
        if not name:
            return

        employee_id = simpledialog.askstring("Registration", "Enter employee ID:", parent=self)
        if not employee_id:
            return

        # Ask for image source
        choice = messagebox.askquestion("Image Source",
                                        "Do you want to upload image from file?\n(Otherwise, photo will be taken from camera)",
                                        parent=self)

        if choice == 'yes':
            self.upload_image_for_registration(name, employee_id)
        else:
            self.capture_image_for_registration(name, employee_id)

    def upload_image_for_registration(self, name, employee_id):
        file_path = filedialog.askopenfilename(
            title="Select Face Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )

        if file_path:
            try:
                image = cv2.imread(file_path)
                if image is None:
                    raise ValueError("Invalid image file format")

                success, message = self.register_new_face(name, employee_id, image)
                if success:
                    messagebox.showinfo("Success", "Registration completed successfully")
                    self.log_message(f"New employee registered: {name} (ID: {employee_id})")
                else:
                    messagebox.showerror("Error", message)
                    self.log_message(f"Registration error: {message}")
            except Exception as e:
                messagebox.showerror("Error", f"Image processing error: {str(e)}")
                self.log_message(f"Image processing error: {str(e)}")

    def capture_image_for_registration(self, name, employee_id):
        self.log_message(f"Starting registration for {name} with ID {employee_id}")

        # Create registration window
        reg_window = tk.Toplevel(self)
        reg_window.title("Register New Face")
        reg_window.geometry("800x600")
        reg_window.configure(bg="#2a2a2a")

        # Header
        header = tk.Frame(reg_window, bg="#3a3a3a")
        header.pack(fill=tk.X, padx=10, pady=10)

        # Camera frame
        cam_frame = tk.Frame(reg_window, bg="#2a2a2a")
        cam_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.cam_label = tk.Label(cam_frame, bg="#1a1a1a")
        self.cam_label.pack(fill=tk.BOTH, expand=True)

        # Controls
        btn_frame = tk.Frame(reg_window, bg="#2a2a2a")
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        btn_save = ModernButton(btn_frame, text="Save Image",
                                command=lambda: self.save_face(reg_window, name, employee_id),
                                color="#4a8f7a", hover_color="#3a7f6a",
                                width=120, height=40)
        btn_save.pack(side=tk.RIGHT, padx=10)

        btn_cancel = ModernButton(btn_frame, text="Cancel",
                                  command=reg_window.destroy,
                                  color="#8f4a4a", hover_color="#7f3a3a",
                                  width=120, height=40)
        btn_cancel.pack(side=tk.LEFT, padx=10)

        # Start camera
        self.cap = cv2.VideoCapture(self.available_cameras[self.current_camera_index])
        self.update_registration_frame(reg_window)

    def update_registration_frame(self, window):
        ret, frame = self.cap.read()
        if ret:
            # Detect faces
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)

            # Draw face boxes
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, "Face Detected", (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # Convert to PhotoImage
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            img = ImageTk.PhotoImage(image=img)

            self.cam_label.img = img
            self.cam_label.config(image=img)

        if window.winfo_exists():
            window.after(10, lambda: self.update_registration_frame(window))
        else:
            self.cap.release()

    def save_face(self, window, name, employee_id):
        ret, frame = self.cap.read()
        if ret:
            success, message = self.register_new_face(name, employee_id, frame)
            if success:
                messagebox.showinfo("Success", "Registration completed successfully", parent=window)
                self.log_message(f"New employee registered: {name} (ID: {employee_id})")
            else:
                messagebox.showerror("Error", message, parent=window)
                self.log_message(f"Registration error: {message}")

        self.cap.release()
        window.destroy()

    def register_new_face(self, name, employee_id, image):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)

        if len(face_locations) == 0:
            return False, "No face detected in the image"

        try:
            face_encoding = face_recognition.face_encodings(rgb_image, face_locations)[0]
            encoding_str = pickle.dumps(face_encoding).decode('latin1')

            conn = self.connect_db()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO employees (name, employee_id, face_encoding) VALUES (%s, %s, %s)",
                    (name, employee_id, encoding_str)
                )
                conn.commit()

                self.known_face_encodings.append(face_encoding)
                self.known_face_ids.append(employee_id)
                self.known_face_names.append(name)

                cursor.close()
                conn.close()
                return True, "Registration completed successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"

        return False, "Database connection error"

    def start_attendance(self):
        self.log_message("Starting attendance system")

        # Create attendance window
        att_window = tk.Toplevel(self)
        att_window.title("Attendance System")
        att_window.geometry("800x600")
        att_window.configure(bg="#2a2a2a")

        # Header
        header = tk.Frame(att_window, bg="#3a3a3a")
        header.pack(fill=tk.X, padx=10, pady=10)

        title = tk.Label(header, text="Attendance System Active",
                         font=(self.custom_font.actual()['family'], 12, 'bold'),
                         bg="#3a3a3a", fg="white")
        title.pack(pady=10)

        # Camera frame
        cam_frame = tk.Frame(att_window, bg="#2a2a2a")
        cam_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.att_cam_label = tk.Label(cam_frame, bg="#1a1a1a")
        self.att_cam_label.pack(fill=tk.BOTH, expand=True)

        # Controls
        btn_frame = tk.Frame(att_window, bg="#2a2a2a")
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        btn_stop = ModernButton(btn_frame, text="Stop System",
                                command=att_window.destroy,
                                color="#8f4a4a", hover_color="#7f3a3a",
                                width=150, height=40)
        btn_stop.pack(pady=10)

        # Start camera
        self.att_cap = cv2.VideoCapture(self.available_cameras[self.current_camera_index])
        self.update_attendance_frame(att_window)

    def update_attendance_frame(self, window):
        ret, frame = self.att_cap.read()
        if ret:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)

            if face_locations:
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    name = "Unknown"
                    employee_id = "Unknown"

                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)

                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]
                        employee_id = self.known_face_ids[best_match_index]

                        current_time = datetime.now()
                        last_time = self.last_attendance.get(employee_id)

                        if last_time is None or (current_time - last_time).seconds >= 5:
                            if self.mark_attendance(employee_id):
                                self.last_attendance[employee_id] = current_time
                                self.log_message(f"Attendance marked: {name} at {current_time.strftime('%H:%M:%S')}")

                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                    cv2.putText(frame, name, (left + 6, bottom - 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

                    if name != "Unknown":
                        cv2.putText(frame, "Present", (left + 6, bottom + 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            img = ImageTk.PhotoImage(image=img)

            self.att_cam_label.img = img
            self.att_cam_label.config(image=img)

        if window.winfo_exists():
            window.after(10, lambda: self.update_attendance_frame(window))
        else:
            self.att_cap.release()

    def mark_attendance(self, employee_id):
        conn = self.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO attendance (employee_id) VALUES (%s)",
                    (employee_id,)
                )
                conn.commit()
                return True
            except Exception as e:
                self.log_message(f"Attendance marking error: {e}")
                return False
            finally:
                cursor.close()
                conn.close()
        return False


if __name__ == "__main__":
    app = ModernApp()
    app.mainloop()