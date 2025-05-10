#!/bin/bash
virtualenv venv
source venv/bin/activate
# ติดตั้ง python + flask ถ้ายังไม่มี
echo ">> ตรวจสอบและติดตั้ง Python & Flask"
echo ">> สวัสดีคุณ สามารถ กำลังเปิดแอป"
# รันแอป
echo ">> เริ่มต้นแอป OT..."
python app.py
