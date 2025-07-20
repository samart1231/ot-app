# OT App - ระบบจัดการ OT และรายรับ-รายจ่าย

แอปพลิเคชันสำหรับจัดการข้อมูล OT (Overtime) และรายรับ-รายจ่าย พร้อมฟีเจอร์ล็อกอินด้วย Google OAuth

## ฟีเจอร์หลัก

- 📅 **จัดการข้อมูล OT** - บันทึกและคำนวณชั่วโมง OT
- 💰 **จัดการรายรับ-รายจ่าย** - บันทึกและติดตามรายรับ-รายจ่าย
- 📊 **Export ข้อมูล** - ส่งออกข้อมูลเป็นไฟล์ CSV
- 🔐 **ระบบล็อกอิน** - รองรับ email/password และ Google OAuth
- 📱 **Responsive Design** - ใช้งานได้บนมือถือและคอมพิวเตอร์

## การติดตั้ง

### 1. Clone โปรเจค
```bash
git clone <repository-url>
cd ot-app
```

### 2. ติดตั้ง Dependencies
```bash
# ติดตั้ง dependencies พื้นฐาน
pip install -r requirements.txt

# หากต้องการ Google OAuth
pip install Flask-OAuthlib==0.9.6
```

### 3. ตั้งค่า Environment Variables
สร้างไฟล์ `.env` จาก `env_example.txt`:
```bash
cp env_example.txt .env
# แก้ไขไฟล์ .env และใส่ค่า Google OAuth credentials
```

### 4. รันแอปพลิเคชัน
```bash
python app.py
```

## การใช้งาน

1. เปิดเบราว์เซอร์ไปที่ `http://localhost:5000`
2. สมัครสมาชิกหรือล็อกอิน
3. เริ่มใช้งานฟีเจอร์ต่างๆ

## ฟีเจอร์ Google OAuth

หากต้องการใช้ Google OAuth:
1. ติดตั้ง dependencies ตาม `INSTALL_GOOGLE_OAUTH.md`
2. ตั้งค่า Google OAuth ตาม `GOOGLE_OAUTH_SETUP.md`
3. แอปจะแสดงปุ่ม "เข้าสู่ระบบด้วย Google"

## หมายเหตุ

- แอปจะทำงานได้ปกติแม้ไม่มี Google OAuth
- ข้อมูลจะถูกเก็บในฐานข้อมูล SQLite
- รองรับการใช้งานบนมือถือและคอมพิวเตอร์
