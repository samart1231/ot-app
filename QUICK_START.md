# คู่มือการใช้งานแบบง่าย

## ปัญหา: "Google OAuth ไม่พร้อมใช้งาน"

### วิธีแก้ไขแบบง่าย

#### 1. เปิด Terminal และไปที่โฟลเดอร์โปรเจค
```bash
cd /home/samat/ot-app
```

#### 2. สร้างและเปิดใช้งาน Virtual Environment
```bash
# สร้าง virtual environment
python3 -m venv venv

# เปิดใช้งาน virtual environment
source venv/bin/activate
```

**หากเจอปัญหา:** `bash: venv/bin/activate: No such file or directory`
- ดูไฟล์ `FIX_VENV.md` สำหรับวิธีแก้ไข
- หรือติดตั้งโดยตรง: `pip install Flask-OAuthlib==0.9.6`

#### 3. ติดตั้ง Dependencies
```bash
pip install Flask-OAuthlib==0.9.6
pip install requests==2.31.0
pip install python-dotenv==1.0.0
```

#### 4. ตรวจสอบการติดตั้ง
```bash
python -c "import flask_oauthlib; print('สำเร็จ!')"
```

#### 5. รันแอปพลิเคชัน
```bash
python app.py
```

#### 6. เปิดเบราว์เซอร์
ไปที่: `http://localhost:5000`

### หากยังมีปัญหา

#### วิธีที่ 1: ใช้ --user flag
```bash
pip install --user Flask-OAuthlib==0.9.6
```

#### วิธีที่ 2: ใช้ pip3
```bash
pip3 install Flask-OAuthlib==0.9.6
```

#### วิธีที่ 3: สร้าง Virtual Environment ใหม่
```bash
python3 -m venv newenv
source newenv/bin/activate
pip install -r requirements.txt
```

### การใช้งาน

1. **เปิดเบราว์เซอร์ไปที่:** `http://localhost:5000`
2. **สมัครสมาชิก** หรือ **ล็อกอิน** ด้วย email/password
3. **หากติดตั้ง Google OAuth สำเร็จ** จะเห็นปุ่ม "เข้าสู่ระบบด้วย Google"
4. **เริ่มใช้งานฟีเจอร์ต่างๆ**

### หมายเหตุ

- แอปจะทำงานได้ปกติแม้ไม่มี Google OAuth
- คุณสามารถใช้ email/password ล็อกอินได้
- Google OAuth เป็นฟีเจอร์เสริมเท่านั้น
- หากมีปัญหา ให้ดูไฟล์ `TROUBLESHOOTING.md` 