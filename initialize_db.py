import sqlite3


def create_database():
    # اتصال به پایگاه داده (اگر وجود نداشته باشد، ایجاد می‌شود)
    conn = sqlite3.connect('face_recognition.db')
    cursor = conn.cursor()

    # ایجاد جدول کاربران
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Mobilenumber TEXT UNIQUE NOT NULL,
        Birthday TEXT,
        Face BLOB NOT NULL,
        RegistrationDate TEXT NOT NULL
    )
    """)

    # ایجاد جدول برای لاگ ورودها (اختیاری)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        mobile TEXT,
        access_time TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()
    print("✅ پایگاه داده با موفقیت ایجاد شد: face_recognition.db")


if __name__ == "__main__":
    create_database()