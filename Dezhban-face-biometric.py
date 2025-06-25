import cvimport cv2
import face_recognition
import numpy as np
import mysql.connector
from datetime import datetime, timedelta
import os
import pickle


# تنظیمات اتصال به دیتابیس
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'f63676367a',
    'database': 'face_attendance'
}


class FaceAttendanceSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        self.last_attendance = {}  # برای ذخیره زمان آخرین حضور هر فرد
        self.load_face_data()

    def connect_db(self):
        try:
            conn = mysql.connector.connect(**db_config)
            return conn
        except mysql.connector.Error as err:
            print(f"Error: {err}")
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
                    print(f"Error loading face data for {name}: {e}")

            cursor.close()
            conn.close()

    def register_new_face(self, name, employee_id, image):
        # تبدیل تصویر به RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # تشخیص چهره
        face_locations = face_recognition.face_locations(rgb_image)
        if len(face_locations) == 0:
            return False, "No face detected in the image"

        try:
            # دریافت کدگذاری چهره
            face_encoding = face_recognition.face_encodings(rgb_image, face_locations)[0]
            encoding_str = pickle.dumps(face_encoding).decode('latin1')

            # ذخیره در دیتابیس
            conn = self.connect_db()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO employees (name, employee_id, face_encoding) VALUES (%s, %s, %s)",
                    (name, employee_id, encoding_str)
                )
                conn.commit()

                # افزودن به لیست چهره‌های شناخته شده
                self.known_face_encodings.append(face_encoding)
                self.known_face_ids.append(employee_id)
                self.known_face_names.append(name)

                cursor.close()
                conn.close()
                return True, "Registration successful"
        except Exception as e:
            return False, f"Error: {str(e)}"

        return False, "Database connection failed"

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
                print(f"Error marking attendance: {e}")
                return False
            finally:
                cursor.close()
                conn.close()
        return False

    def draw_multilanguage_text(self, image, text, position, font_scale, color, thickness):
        """
        تابع برای نمایش متن چندزبانه (فارسی و انگلیسی) روی تصویر
        """
        # تبدیل تصویر OpenCV به PIL
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)

        # تعیین فونت مناسب
        try:
            # ابتدا سعی می‌کنیم از فونت فارسی استفاده کنیم
            font_path = "arial.ttf" if os.path.exists("arial.ttf") else None
            if font_path:
                font = ImageFont.truetype(font_path, int(20 * font_scale))
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        # بررسی آیا متن حاوی کاراکترهای فارسی است
        if any('\u0600' <= char <= '\u06FF' for char in text):
            # پردازش متن فارسی
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
        else:
            bidi_text = text

        # رسم متن روی تصویر
        draw.text(position, bidi_text, font=font, fill=color)

        # تبدیل تصویر PIL به OpenCV
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def run_attendance(self):
        video_capture = cv2.VideoCapture(0)
        attendance_interval = 5  # حداقل فاصله زمانی بین دو ثبت حضور (ثانیه)

        while True:
            ret, frame = video_capture.read()
            if not ret:
                continue

            # کوچک کردن تصویر برای پردازش سریعتر
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # تشخیص چهره‌ها
            face_locations = face_recognition.face_locations(rgb_small_frame)

            if face_locations:
                # دریافت کدگذاری چهره‌ها
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    # مقایسه با چهره‌های شناخته شده
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    name = "Unknown"
                    employee_id = "Unknown"

                    # محاسبه فاصله چهره‌ها
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)

                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]
                        employee_id = self.known_face_ids[best_match_index]

                        # بررسی زمان آخرین حضور
                        current_time = datetime.now()
                        last_time = self.last_attendance.get(employee_id)

                        if last_time is None or (current_time - last_time).seconds >= attendance_interval:
                            # ثبت حضور
                            if self.mark_attendance(employee_id):
                                self.last_attendance[employee_id] = current_time
                                print(f"Attendance recorded: {name} at {current_time}")

                    # بزرگ کردن مختصات برای نمایش
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    # رسم مستطیل دور چهره
                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                    # نمایش نام با تابع چندزبانه
                    frame = self.draw_multilanguage_text(
                        frame,
                        name,
                        (left + 6, bottom - 30),
                        0.6,
                        (255, 255, 255),
                        1
                    )

                    if name != "Unknown":
                        frame = self.draw_multilanguage_text(
                            frame,
                            "Present",
                            (left + 6, bottom + 5),
                            0.6,
                            (0, 255, 0),
                            1
                        )

            # نمایش دستورالعمل
            frame = self.draw_multilanguage_text(
                frame,
                "Press 'q' to quit",
                (10, 30),
                0.7,
                (255, 255, 255),
                2
            )

            cv2.imshow('Face Attendance System', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

    def capture_for_registration(self, name, employee_id):
        video_capture = cv2.VideoCapture(0)

        while True:
            ret, frame = video_capture.read()
            if not ret:
                continue

            # نمایش دستورالعمل‌ها
            instruction_text = f"Registering: {name}\nPress 's' to save, 'q' to cancel"
            frame = self.draw_multilanguage_text(
                frame,
                instruction_text,
                (10, 30),
                0.7,
                (255, 255, 255),
                2
            )

            # تشخیص چهره
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)

            # نمایش مستطیل دور چهره
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            cv2.imshow('Register New Face', frame)

            key = cv2.waitKey(1)
            if key & 0xFF == ord('s'):  # ثبت با کلید s
                if face_locations:
                    video_capture.release()
                    cv2.destroyAllWindows()
                    return frame
                else:
                    print("No face detected! Try again.")

            elif key & 0xFF == ord('q'):  # انصراف با کلید q
                video_capture.release()
                cv2.destroyAllWindows()
                return None


def main_menu():
    system = FaceAttendanceSystem()

    while True:
        print("\nFace Attendance System")
        print("1. Register New Employee")
        print("2. Start Attendance")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            name = input("Enter employee name: ")
            employee_id = input("Enter employee ID: ")

            print("Opening camera for registration...")
            captured_frame = system.capture_for_registration(name, employee_id)

            if captured_frame is not None:
                success, message = system.register_new_face(name, employee_id, captured_frame)
                print(message)
                if success:
                    cv2.imshow("Registered Face", captured_frame)
                    cv2.waitKey(2000)
                    cv2.destroyAllWindows()

        elif choice == '2':
            print("Starting attendance system... Press 'q' to quit.")
            system.run_attendance()

        elif choice == '3':
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    # نصب کتابخانه‌های لازم برای پشتیبانی فارسی
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Installing required libraries for multilingual support...")
        os.system("pip install arabic-reshaper python-bidi pillow")
        import arabic_reshaper
        from bidi.algorithm import get_display
        from PIL import Image, ImageDraw, ImageFont

    main_menu()