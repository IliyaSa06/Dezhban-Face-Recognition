Dezhban Smart Attendance System

This project is a smart attendance system built using image processing and face recognition.
The user interface is developed with Tkinter, and all employee and attendance data are stored in MySQL.

✨ Features

Register new employees with a face image (via camera or file upload)

Store employee face encodings in the database

Automatic employee recognition and attendance logging

Modern user interface with custom buttons

Multi-camera support (camera selection available)

Real-time activity logs and system status updates

Attendance time saved in the database with employee ID

🛠️ Technologies & Libraries

Python 3.x

OpenCV
 → Image processing & camera integration

face_recognition
 → Face detection & recognition

MySQL
 → Database

Tkinter
 → GUI

Pillow (PIL)
 → Image handling

pickle
 → Store & load face encoding data

⚙️ Installation & Setup
1. Clone the project
git clone https://github.com/USERNAME/Dezhban-Face-Attendance.git
cd Dezhban-Face-Attendance

2. Install dependencies
pip install opencv-python face-recognition mysql-connector-python pillow


⚠️ Note: face_recognition requires dlib
.
On Windows, it is recommended to install it using pre-built wheel packages.

3. Create the database

Run the following SQL commands in MySQL:

CREATE DATABASE face_attendance;

CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    face_encoding LONGTEXT NOT NULL
);

CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

4. Configure database connection

Update the db_config section in the main Python file:

db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'YOUR_PASSWORD',
    'database': 'face_attendance'
}

5. Run the program
python main.py

📷 How it works

Register New Employee → Add a new employee using the camera or by uploading an image file.

Start Attendance System → The system detects and recognizes employees in real time, logging their attendance automatically.

A log of activities is displayed inside the app.

📌 Screenshots

(You can add screenshots of the app here later)

👨‍💻 Developer

Developed by Sadra Rayaneh Novin Tabarestan
Version: 2.0

📜 License

This project is licensed under the MIT License.
