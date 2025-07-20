#!/usr/bin/env python3
"""
สคริปต์อัตโนมัติสำหรับติดตั้ง Google OAuth บน Manjaro
"""

import subprocess
import sys
import os
import platform

def run_command(command, description):
    """รันคำสั่งและแสดงผลลัพธ์"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} สำเร็จ")
            if result.stdout:
                print(f"   ผลลัพธ์: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} ไม่สำเร็จ")
            if result.stderr:
                print(f"   ข้อผิดพลาด: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} ไม่สำเร็จ: {e}")
        return False

def check_system():
    """ตรวจสอบระบบ"""
    print("🖥️ ตรวจสอบระบบ...")
    
    system = platform.system()
    if system == "Linux":
        print("✅ ระบบ: Linux")
        
        # ตรวจสอบ Manjaro
        try:
            with open("/etc/os-release", "r") as f:
                content = f.read()
                if "manjaro" in content.lower():
                    print("✅ ระบบ: Manjaro")
                    return "manjaro"
                else:
                    print("⚠️ ไม่ใช่ Manjaro แต่เป็น Linux")
                    return "linux"
        except:
            print("⚠️ ไม่สามารถตรวจสอบ OS ได้")
            return "unknown"
    else:
        print(f"⚠️ ระบบ: {system}")
        return "other"

def try_pip_install():
    """ลองติดตั้งด้วย pip"""
    print("\n📦 ลองติดตั้งด้วย pip...")
    
    commands = [
        ("pip install Flask-OAuthlib==0.9.6", "pip install"),
        ("pip3 install Flask-OAuthlib==0.9.6", "pip3 install"),
        ("pip install --user Flask-OAuthlib==0.9.6", "pip install --user"),
        ("python -m pip install Flask-OAuthlib==0.9.6", "python -m pip install"),
        ("python3 -m pip install Flask-OAuthlib==0.9.6", "python3 -m pip install")
    ]
    
    for command, desc in commands:
        if run_command(command, desc):
            return True
    
    return False

def try_package_manager():
    """ลองติดตั้งด้วย package manager"""
    print("\n📦 ลองติดตั้งด้วย package manager...")
    
    commands = [
        ("sudo pacman -S python-flask-oauthlib", "pacman install"),
        ("yay -S python-flask-oauthlib", "yay install"),
        ("pamac install python-flask-oauthlib", "pamac install")
    ]
    
    for command, desc in commands:
        if run_command(command, desc):
            return True
    
    return False

def test_installation():
    """ทดสอบการติดตั้ง"""
    print("\n🧪 ทดสอบการติดตั้ง...")
    
    try:
        import flask_oauthlib
        print("✅ Flask-OAuthlib ติดตั้งสำเร็จ!")
        print(f"   เวอร์ชัน: {flask_oauthlib.__version__}")
        return True
    except ImportError as e:
        print("❌ Flask-OAuthlib ไม่ได้ติดตั้ง")
        print(f"   ข้อผิดพลาด: {e}")
        return False

def main():
    print("🔧 ติดตั้ง Google OAuth บน Manjaro")
    print("=" * 50)
    
    # ตรวจสอบระบบ
    system = check_system()
    
    # ลองติดตั้งด้วย pip
    if try_pip_install():
        if test_installation():
            print("\n🎉 ติดตั้งสำเร็จด้วย pip!")
            print("🚀 Google OAuth พร้อมใช้งาน")
            return
    
    # ลองติดตั้งด้วย package manager
    if system == "manjaro":
        if try_package_manager():
            if test_installation():
                print("\n🎉 ติดตั้งสำเร็จด้วย package manager!")
                print("🚀 Google OAuth พร้อมใช้งาน")
                return
    
    print("\n❌ ไม่สามารถติดตั้งได้")
    print("💡 ลองทำด้วยตนเอง:")
    print("1. sudo pacman -S python-flask-oauthlib")
    print("2. หรือ pip install Flask-OAuthlib==0.9.6")
    print("3. ดูรายละเอียดได้ที่ไฟล์ MANJARO_FIX.md")

if __name__ == "__main__":
    main() 