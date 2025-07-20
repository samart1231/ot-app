#!/usr/bin/env python3
"""
สคริปต์สำหรับสร้าง virtual environment และติดตั้ง dependencies
"""

import subprocess
import sys
import os
import shutil

def run_command(command, description):
    """รันคำสั่งและแสดงผลลัพธ์"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} สำเร็จ")
            return True
        else:
            print(f"❌ {description} ไม่สำเร็จ")
            print(f"ข้อผิดพลาด: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} ไม่สำเร็จ: {e}")
        return False

def check_python():
    """ตรวจสอบ Python version"""
    print("🐍 ตรวจสอบ Python...")
    
    # ตรวจสอบ python
    if shutil.which("python"):
        result = subprocess.run(["python", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ พบ Python: {result.stdout.strip()}")
            return "python"
    
    # ตรวจสอบ python3
    if shutil.which("python3"):
        result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ พบ Python3: {result.stdout.strip()}")
            return "python3"
    
    print("❌ ไม่พบ Python")
    return None

def create_venv(python_cmd):
    """สร้าง virtual environment"""
    if os.path.exists("venv"):
        print("📁 พบ virtual environment อยู่แล้ว")
        return True
    
    return run_command(f"{python_cmd} -m venv venv", "สร้าง virtual environment")

def install_dependencies():
    """ติดตั้ง dependencies"""
    packages = [
        "Flask-OAuthlib==0.9.6",
        "requests==2.31.0",
        "python-dotenv==1.0.0"
    ]
    
    success_count = 0
    
    for package in packages:
        if run_command(f"pip install {package}", f"ติดตั้ง {package}"):
            success_count += 1
    
    return success_count == len(packages)

def main():
    print("🔧 ตั้งค่า Virtual Environment และ Dependencies")
    print("=" * 50)
    
    # ตรวจสอบ Python
    python_cmd = check_python()
    if not python_cmd:
        print("❌ ไม่พบ Python กรุณาติดตั้ง Python ก่อน")
        return
    
    # สร้าง virtual environment
    if not create_venv(python_cmd):
        print("❌ ไม่สามารถสร้าง virtual environment ได้")
        print("💡 ลองติดตั้ง packages โดยตรง:")
        print("   pip install Flask-OAuthlib==0.9.6")
        return
    
    # เปิดใช้งาน virtual environment
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
    else:  # Linux/Mac
        activate_cmd = "source venv/bin/activate"
    
    print(f"🔄 เปิดใช้งาน virtual environment...")
    print(f"💡 ใช้คำสั่ง: {activate_cmd}")
    
    # ติดตั้ง dependencies
    if install_dependencies():
        print("\n🎉 ตั้งค่าสำเร็จ!")
        print("🚀 คุณสามารถรันแอปพลิเคชันได้แล้ว")
        print("\n📋 ขั้นตอนต่อไป:")
        print("1. เปิดใช้งาน virtual environment:")
        print(f"   {activate_cmd}")
        print("2. รันแอปพลิเคชัน:")
        print("   python app.py")
        print("3. เปิดเบราว์เซอร์ไปที่: http://localhost:5000")
    else:
        print("\n⚠️ มีปัญหาในการติดตั้ง dependencies")
        print("💡 ลองใช้คำสั่ง:")
        print("   pip install --user Flask-OAuthlib==0.9.6")

if __name__ == "__main__":
    main() 