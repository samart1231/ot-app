#!/usr/bin/env python3
"""
สคริปต์ทดสอบการติดตั้ง Google OAuth แบบง่าย
"""

def main():
    print("🧪 ทดสอบการติดตั้ง Google OAuth")
    print("=" * 40)
    
    try:
        import flask_oauthlib
        print("✅ Flask-OAuthlib ติดตั้งสำเร็จ!")
        print(f"   เวอร์ชัน: {flask_oauthlib.__version__}")
        print("\n🎉 Google OAuth พร้อมใช้งาน!")
        print("🚀 คุณสามารถใช้ Google ล็อกอินได้แล้ว")
        return True
    except ImportError as e:
        print("❌ Flask-OAuthlib ไม่ได้ติดตั้ง")
        print(f"   ข้อผิดพลาด: {e}")
        print("\n💡 วิธีแก้ไข:")
        print("1. เปิดใช้งาน virtual environment:")
        print("   source venv/bin/activate")
        print("2. ติดตั้ง Flask-OAuthlib:")
        print("   pip install Flask-OAuthlib==0.9.6")
        print("3. หรือใช้คำสั่งอื่น:")
        print("   pip3 install Flask-OAuthlib==0.9.6")
        print("   pip install --user Flask-OAuthlib==0.9.6")
        print("\n📖 ดูรายละเอียดได้ที่ไฟล์ FINAL_FIX.md")
        return False

if __name__ == "__main__":
    main() 