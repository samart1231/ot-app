#!/usr/bin/env python3
"""
สคริปต์สำหรับติดตั้ง dependencies สำหรับ Google OAuth
"""

import subprocess
import sys
import os

def install_package(package):
    """ติดตั้ง package ด้วย pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ ติดตั้ง {package} สำเร็จ")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ ไม่สามารถติดตั้ง {package} ได้")
        return False

def main():
    print("🔧 กำลังติดตั้ง dependencies สำหรับ Google OAuth...")
    print()
    
    # รายการ packages ที่ต้องติดตั้ง
    packages = [
        "Flask-OAuthlib==0.9.6",
        "requests==2.31.0", 
        "python-dotenv==1.0.0"
    ]
    
    success_count = 0
    
    for package in packages:
        print(f"📦 กำลังติดตั้ง {package}...")
        if install_package(package):
            success_count += 1
        print()
    
    print(f"📊 สรุป: ติดตั้งสำเร็จ {success_count}/{len(packages)} packages")
    
    if success_count == len(packages):
        print("🎉 ติดตั้ง dependencies ครบถ้วนแล้ว!")
        print("🚀 คุณสามารถรันแอปพลิเคชันได้แล้ว")
        print("💡 หากต้องการใช้ Google OAuth ให้ตั้งค่าตาม GOOGLE_OAUTH_SETUP.md")
    else:
        print("⚠️ มีบาง packages ที่ติดตั้งไม่สำเร็จ")
        print("💡 ลองใช้คำสั่ง: pip install -r requirements.txt")

if __name__ == "__main__":
    main() 