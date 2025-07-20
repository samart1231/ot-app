# การตั้งค่า Google OAuth สำหรับแอป OT

## ขั้นตอนการตั้งค่า Google OAuth

### 1. สร้าง Google Cloud Project

1. ไปที่ [Google Cloud Console](https://console.cloud.google.com/)
2. สร้างโปรเจคใหม่หรือเลือกโปรเจคที่มีอยู่
3. เปิดใช้งาน Google+ API และ Google OAuth2 API

### 2. สร้าง OAuth 2.0 Credentials

1. ไปที่ "APIs & Services" > "Credentials"
2. คลิก "Create Credentials" > "OAuth 2.0 Client IDs"
3. เลือก "Web application"
4. ตั้งชื่อ Client ID
5. เพิ่ม Authorized redirect URIs:
   - สำหรับ development: `http://localhost:5000/login/google/authorized`
   - สำหรับ production: `https://yourdomain.com/login/google/authorized`

### 3. ตั้งค่า Environment Variables

สร้างไฟล์ `.env` ในโฟลเดอร์โปรเจค:

```env
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
SECRET_KEY=your_secret_key_here
DATABASE_FILE=ot.db
```

**หมายเหตุ:** ไฟล์ `.env` จะถูก ignore โดย git เพื่อความปลอดภัย

### 4. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 5. รันแอปพลิเคชัน

```bash
python app.py
```

## การใช้งาน

1. เปิดเบราว์เซอร์ไปที่ `http://localhost:5000`
2. คลิกปุ่ม "เข้าสู่ระบบด้วย Google"
3. อนุญาตให้แอปเข้าถึงข้อมูล Google
4. ระบบจะสร้างบัญชีใหม่หรือเข้าสู่ระบบด้วยบัญชีที่มีอยู่

## หมายเหตุ

- ข้อมูลผู้ใช้จะถูกเก็บในฐานข้อมูล SQLite
- รูปโปรไฟล์และชื่อจะถูกเก็บใน session
- ผู้ใช้ที่ล็อกอินด้วย Google จะมี password_hash เป็น 'google_oauth' 