#!/usr/bin/env python3
"""
สคริปต์ทดสอบการติดตั้ง Google OAuth
"""

def test_oauth_installation():
    """ทดสอบการติดตั้ง Flask-OAuthlib"""
    print("🔍 ทดสอบการติดตั้ง Google OAuth...")
    print("=" * 40)
    
    try:
        import flask_oauthlib
        print("✅ Flask-OAuthlib ติดตั้งสำเร็จ!")
        print(f"   เวอร์ชัน: {flask_oauthlib.__version__}")
        return True
    except ImportError as e:
        print("❌ Flask-OAuthlib ไม่ได้ติดตั้ง")
        print(f"   ข้อผิดพลาด: {e}")
        return False

def test_other_dependencies():
    """ทดสอบ dependencies อื่นๆ"""
    print("\n🔍 ทดสอบ dependencies อื่นๆ...")
    print("=" * 40)
    
    dependencies = [
        ("flask", "Flask"),
        ("requests", "Requests"),
        ("dotenv", "Python-dotenv")
    ]
    
    all_installed = True
    
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✅ {name} ติดตั้งสำเร็จ")
        except ImportError:
            print(f"❌ {name} ไม่ได้ติดตั้ง")
            all_installed = False
    
    return all_installed

def main():
    print("🧪 ทดสอบการติดตั้ง Dependencies")
    print("=" * 50)
    
    # ทดสอบ Flask-OAuthlib
    oauth_ok = test_oauth_installation()
    
    # ทดสอบ dependencies อื่นๆ
    other_ok = test_other_dependencies()
    
    print("\n📊 สรุปผลการทดสอบ:")
    print("=" * 30)
    
    if oauth_ok and other_ok:
        print("🎉 ทุกอย่างพร้อมใช้งาน!")
        print("🚀 Google OAuth พร้อมใช้งาน")
        print("💡 คุณสามารถรันแอปพลิเคชันได้แล้ว")
    elif oauth_ok:
        print("⚠️ Flask-OAuthlib พร้อมใช้งาน แต่มี dependencies อื่นที่ขาดหาย")
        print("💡 ลองติดตั้ง: pip install requests python-dotenv")
    else:
        print("❌ Flask-OAuthlib ไม่พร้อมใช้งาน")
        print("💡 ลองติดตั้ง: pip install Flask-OAuthlib==0.9.6")
        print("📖 ดูรายละเอียดได้ที่ไฟล์ SIMPLE_FIX.md")
    
    print("\n🔧 คำสั่งที่แนะนำ:")
    print("1. pip install Flask-OAuthlib==0.9.6")
    print("2. pip install requests==2.31.0")
    print("3. pip install python-dotenv==1.0.0")
    print("4. python app.py")

if __name__ == "__main__":
    main() 