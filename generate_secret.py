#!/usr/bin/env python3
import secrets
import string

def generate_secret_key(length=32):
    """สร้าง SECRET_KEY ที่ปลอดภัย"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    secret_key = generate_secret_key()
    print(f"SECRET_KEY={secret_key}")
    print("\nคัดลอก SECRET_KEY นี้ไปใส่ในไฟล์ .env") 