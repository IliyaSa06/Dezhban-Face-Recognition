import cv2
import face_recognition
import mysql.connector
import numpy as np
from datetime import datetime
from kavenegar import KavenegarAPI, APIException, HTTPException

# تنظیمات سیستم
SMS_API_KEY = '4E35507450495143352F526A385838492B5956395159444C4B765876714775366F354A6455507A595053383D'
SMS_SENDER = '2000660110'

DB_CONFIG = {
    'host': "127.0.0.1",
    'user': "root",
    'password': "f63676367a",
    'database': "user information",
    'auth_plugin': 'mysql_native_password'
}


class FaceRecognitionSystem:
    def __init__(self):
        self.sms_api = KavenegarAPI(SMS_API_KEY)
        self.camera_manager = CameraManager()

    def send_sms(self, mobile, message):
        """ارسال پیامک با کاوه نگار"""
        try:
            params = {
                'sender': SMS_SENDER,
                'receptor': mobile,
                'message': message
            }
            response = self.sms_api.sms_send(params)
            print(f"✓ پیامک به {mobile} ارسال شد")
            return True
        except Exception as e:
            print(f"✗ خطای پیامک: {e}")
            return False

    def get_db_connection(self):
        """اتصال به پایگاه داده"""
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except mysql.connector.Error as err:
            print(f"✗ خطای پایگاه داده: {err}")
            return None

    def register_user(self, name, mobile, dob, face_encoding):
        """ثبت کاربر جدید"""
        conn = None
        try:
            conn = self.get_db_connection()
            if not conn:
                return False

            cursor = conn.cursor()

            # بررسی موبایل تکراری
            cursor.execute("SELECT Mobilenumber FROM users WHERE Mobilenumber = %s", (mobile,))
            if cursor.fetchone():
                print(f"✗ شماره {mobile} قبلا ثبت شده!")
                return False

            face_bytes = face_encoding.tobytes()
            reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # درج اطلاعات کاربر
            cursor.execute("""
                INSERT INTO users (Name, Mobilenumber, Birthday, Face, RegistrationDate)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, mobile, dob, face_bytes, reg_date))

            conn.commit()
            print(f"✓ ثبت نام: {name} ({mobile})")

            # ارسال پیامک تایید
            self.send_sms(mobile, f"ثبت نام شما با موفقیت انجام شد\nنام: {name}\nتاریخ: {reg_date}")
            return True

        except mysql.connector.Error as err:
            print(f"✗ خطای ثبت نام: {err}")
            return False
        finally:
            if conn and conn.is_connected():
                conn.close()

    def recognize_face(self, face_encoding):
        """تشخیص چهره"""
        conn = None
        try:
            conn = self.get_db_connection()
            if not conn:
                return {'exists': False}

            cursor = conn.cursor()

            cursor.execute("""
                SELECT Name, Mobilenumber, Birthday, Face 
                FROM users
            """)

            for (name, mobile, dob, face_bytes) in cursor:
                stored_encoding = np.frombuffer(face_bytes, dtype=np.float64)
                if face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.6)[0]:
                    return {
                        'name': name,
                        'mobile': mobile,
                        'dob': dob.strftime("%Y-%m-%d") if dob else None,
                        'exists': True
                    }

            return {'exists': False}

        except Exception as e:
            print(f"✗ خطای تشخیص: {e}")
            return {'exists': False}
        finally:
            if conn and conn.is_connected():
                conn.close()

    def process_frame(self, frame):
        """پردازش تصویر"""
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            top, right, bottom, left = int(top * 2), int(right * 2), int(bottom * 2), int(left * 2)

            result = self.recognize_face(face_encoding)
            color = (0, 255, 0) if result['exists'] else (0, 0, 255)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            status = result.get('name', 'ناشناس') if result['exists'] else "ناشناس"
            cv2.putText(frame, status, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        return frame, face_locations, face_encodings

    def run(self):
        """اجرای سیستم"""
        if not self.camera_manager.initialize_all_cameras():
            print("✗ دوربینی یافت نشد!")
            return

        print("سیستم تشخیص چهره فعال شد")
        print("دستورات: 's'=ثبت چهره, 'c'=تعویض دوربین, 'q'=خروج")

        while True:
            frame = self.camera_manager.get_active_frame()
            if frame is None:
                continue

            processed_frame, face_locs, face_encs = self.process_frame(frame)

            cv2.imshow('سیستم تشخیص چهره', processed_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('s') and face_locs:
                self.handle_face_capture(frame, face_locs, face_encs)
            elif key == ord('c'):
                self.camera_manager.switch_camera()
            elif key == ord('q'):
                break

        self.camera_manager.release_all()
        cv2.destroyAllWindows()
        print("سیستم خاموش شد.")

    def handle_face_capture(self, frame, face_locs, face_encs):
        """مدیریت ثبت چهره"""
        face_encoding = face_encs[0] if face_encs else face_recognition.face_encodings(
            cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), face_locs)[0]

        result = self.recognize_face(face_encoding)

        if result['exists']:
            print(f"\n✓ کاربر شناسایی شد: {result['name']}")
            print(f"موبایل: {result['mobile']}")
            print(f"تاریخ تولد: {result['dob']}\n")
        else:
            print("\nکاربر جدید تشخیص داده شد. لطفا اطلاعات را وارد کنید:")
            name = input("نام کامل: ").strip()
            mobile = input("شماره موبایل: ").strip()
            dob = input("تاریخ تولد (YYYY-MM-DD): ").strip()

            if self.register_user(name, mobile, dob, face_encoding):
                print("✓ ثبت نام موفقیت آمیز!\n")
            else:
                print("✗ ثبت نام ناموفق!\n")


class CameraManager:
    def __init__(self):
        self.cameras = {}
        self.active_camera = None
        self.available_cameras = []

    def detect_cameras(self, max_check=5):
        """شناسایی دوربین‌ها"""
        self.available_cameras = []
        for i in range(max_check):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                self.available_cameras.append(i)
                cap.release()
        return self.available_cameras

    def initialize_all_cameras(self):
        """راه‌اندازی دوربین‌ها"""
        self.detect_cameras()
        if not self.available_cameras:
            return False

        for cam_id in self.available_cameras:
            cap = cv2.VideoCapture(cam_id)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cameras[cam_id] = cap

        if self.cameras:
            self.active_camera = next(iter(self.cameras))
            return True
        return False

    def get_active_frame(self):
        """دریافت فریم از دوربین فعال"""
        if self.active_camera is None:
            return None

        ret, frame = self.cameras[self.active_camera].read()
        return frame if ret else None

    def switch_camera(self):
        """تعویض دوربین فعال"""
        if len(self.cameras) < 2:
            return

        current_idx = self.available_cameras.index(self.active_camera)
        next_idx = (current_idx + 1) % len(self.available_cameras)
        self.active_camera = self.available_cameras[next_idx]
        print(f"دوربین فعال: {self.active_camera}")

    def release_all(self):
        """آزادسازی منابع"""
        for cap in self.cameras.values():
            cap.release()
        self.cameras = {}
        self.active_camera = None


if __name__ == "__main__":
    system = FaceRecognitionSystem()
    system.run()