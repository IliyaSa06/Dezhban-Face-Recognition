# Dezhban Face Recognition System

An advanced face recognition-based attendance system with a modern user interface and MySQL database connectivity.

<img width="1920" height="1025" alt="Image" src="https://github.com/user-attachments/assets/24f37f4c-ab36-40dc-9330-d733c7554e35" />


## Features

- High-accuracy face recognition using the `face_recognition` library
- Modern and elegant GUI built with Tkinter
- Multiple camera support
- New employee registration with two methods: camera capture or image upload
- Automatic attendance recording
- MySQL database integration for data storage
- Activity logging and reporting
- Responsive and beautiful design

## Prerequisites

- Python 3.7 or higher
- MySQL Server
- Webcam

## Installation & Setup

1. Clone the repository:

```bash
git clone https://github.com/your-username/face-attendance-system.git
cd face-attendance-system
```

2. Install required libraries:

```bash
pip install -r requirements.txt
```

3. Set up MySQL database:

- Create a database named `face_attendance`
- Run the following SQL script to create necessary tables:

```sql
CREATE DATABASE face_attendance;

USE face_attendance;

CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    face_encoding TEXT NOT NULL,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);
```

4. Configure database connection:

Open `app.py` and modify the `db_config` section according to your MySQL settings:

```python
db_config = {
    'host': '127.0.0.1',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'face_attendance'
}
```

5. Run the application:

```bash
python app.py
```

## How to Use

### Register New Employee

1. Click the "Register New Employee" button.
2. Enter the employee's name and ID.
3. Choose image source:
   - Upload image from file
   - Capture from camera
4. The system will automatically detect and register the face.

### Start Attendance

1. Click the "Start Attendance" button.
2. The system will automatically detect faces and record attendance.
3. For each recognized person, their name and attendance status will be displayed.

### Camera Selection

If multiple cameras are available, you can select the desired camera from the dropdown menu.

## Project Structure

```
face-attendance-system/
│
├── app.py              # Main application file
├── requirements.txt    # List of required libraries
├── README.md          # Documentation file
└── images/            # Folder containing images and icons
```

## Libraries Used

- `opencv-python` - Image processing and camera management
- `face-recognition` - Face detection and recognition
- `mysql-connector-python` - MySQL database connection
- `pillow` - Image processing and display in Tkinter
- `numpy` - Numerical computations
- `tkinter` - GUI framework

## Troubleshooting

### Issue: "No camera found"

- Ensure the camera is properly connected.
- Check that the camera isn't locked by other applications.

### Issue: Database connection error

- Ensure MySQL Server is running.
- Verify connection settings in the `db_config` section.
- Make sure the database and required tables exist.

### Issue: face_recognition library won't install

- Ensure you have Python 3.7 or higher.
- Windows users may need to install Visual Studio Build Tools.

## Developers

- Designed and developed by Sadra Rayane Novin Tabestan Co.

## License

This project is released under the MIT License.

## Support

To report issues or suggest features, please use the Issues section on GitHub.
