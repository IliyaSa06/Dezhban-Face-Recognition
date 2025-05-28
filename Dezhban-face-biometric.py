import cv2
import face_recognition
import mysql.connector
import numpy as np
from datetime import datetime


# SMS simulation function
def send_sms(mobile, message):
    print("\n--- SMS Simulation ---")
    print(f"To: {mobile}")
    print(f"Message: {message}")
    print("----------------------\n")
    return True


# Initialize database connection
def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",  # Replace with your MySQL username
        password="",  # Replace with your MySQL password
        database="user information"
    )


# Register new person
def register_person(name, mobile, dob, face_encoding):
    conn = get_db_connection()
    c = conn.cursor()
    registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("INSERT INTO users (Name, Mobilenumber, Birthday, Face) VALUES (%s, %s, %s, %s)",
              (name, mobile, dob, face_encoding.tobytes()))
    conn.commit()
    conn.close()

    message = f"Your information has been registered successfully. Name: {name}, Registration Date: {registration_date}"
    send_sms(mobile, message)


# Recognize face
def recognize_face(face_encoding):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT Name, Mobilenumber, Birthday, Face FROM users")

    for row in c.fetchall():
        stored_encoding = np.frombuffer(row[3], dtype=np.float64)
        matches = face_recognition.compare_faces([stored_encoding], face_encoding)

        if matches[0]:
            conn.close()
            return {
                'name': row[0],
                'mobile': row[1],
                'dob': row[2].strftime("%Y-%m-%d") if row[2] else None,
                'exists': True
            }

    conn.close()
    return {'exists': False}


# Main process with camera preview
def main():
    video_capture = cv2.VideoCapture(0)

    print("Face detection started. Press 's' to capture when ready or 'q' to quit.")

    while True:
        # Capture frame-by-frame
        ret, frame = video_capture.read()

        # Display the resulting frame
        cv2.imshow('Dajban - Face Registration', frame)

        # Wait for key press
        key = cv2.waitKey(1)

        if key == ord('s'):  # 's' pressed - capture image
            # Find face in the frame
            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)

            if len(face_encodings) == 0:
                print("No face detected. Please try again.")
                continue

            face_encoding = face_encodings[0]
            recognition_result = recognize_face(face_encoding)

            if recognition_result['exists']:
                print("\nUser recognized!")
                print(f"Name: {recognition_result['name']}")
                print(f"Mobile: {recognition_result['mobile']}")
                print(f"Date of Birth: {recognition_result['dob']}")
            else:
                print("\nNew user detected. Please enter information:")
                name = input("Full name: ")
                mobile = input("Mobile number: ")
                dob = input("Date of Birth (YYYY-MM-DD): ")

                register_person(name, mobile, dob, face_encoding)
                print("\nInformation registered successfully!")

            # Show confirmation for 3 seconds
            cv2.putText(frame, "Processing complete!", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow('Dajban - Face Registration', frame)
            cv2.waitKey(3000)

        elif key == ord('q'):  # 'q' pressed - quit
            break

    # Release everything when done
    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()