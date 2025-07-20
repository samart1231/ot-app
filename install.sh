#!/bin/bash

echo "🔧 กำลังติดตั้ง dependencies สำหรับ Google OAuth..."
echo ""

# ตรวจสอบ virtual environment
if [ -d "venv" ]; then
    echo "📁 พบ virtual environment: venv"
    echo "🔄 กำลังเปิดใช้งาน venv..."
    source venv/bin/activate
elif [ -d "myenv" ]; then
    echo "📁 พบ virtual environment: myenv"
    echo "🔄 กำลังเปิดใช้งาน myenv..."
    source myenv/bin/activate
else
    echo "⚠️ ไม่พบ virtual environment"
    echo "💡 แนะนำให้สร้าง virtual environment ก่อน"
fi

echo ""
echo "📦 กำลังติดตั้ง packages..."

# ติดตั้ง packages
pip install Flask-OAuthlib==0.9.6
if [ $? -eq 0 ]; then
    echo "✅ Flask-OAuthlib ติดตั้งสำเร็จ"
else
    echo "❌ Flask-OAuthlib ติดตั้งไม่สำเร็จ"
fi

pip install requests==2.31.0
if [ $? -eq 0 ]; then
    echo "✅ requests ติดตั้งสำเร็จ"
else
    echo "❌ requests ติดตั้งไม่สำเร็จ"
fi

pip install python-dotenv==1.0.0
if [ $? -eq 0 ]; then
    echo "✅ python-dotenv ติดตั้งสำเร็จ"
else
    echo "❌ python-dotenv ติดตั้งไม่สำเร็จ"
fi

echo ""
echo "🔍 กำลังตรวจสอบการติดตั้ง..."

# ตรวจสอบการติดตั้ง
python -c "import flask_oauthlib; print('✅ Flask-OAuthlib พร้อมใช้งาน')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 ติดตั้ง dependencies ครบถ้วนแล้ว!"
    echo "🚀 คุณสามารถรันแอปพลิเคชันได้แล้ว"
    echo "💡 หากต้องการใช้ Google OAuth ให้ตั้งค่าตาม GOOGLE_OAUTH_SETUP.md"
else
    echo ""
    echo "⚠️ มีปัญหาในการติดตั้ง"
    echo "💡 ลองใช้คำสั่ง: pip install --user Flask-OAuthlib==0.9.6"
fi 