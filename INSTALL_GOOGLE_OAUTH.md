# การติดตั้ง Google OAuth Dependencies

## ปัญหาที่พบ
หากคุณเจอ error `ModuleNotFoundError: No module named 'flask_oauthlib'` ให้ทำตามขั้นตอนนี้:

## วิธีแก้ไข

### 1. เปิดใช้งาน Virtual Environment

```bash
# ใช้ venv
source venv/bin/activate

# หรือใช้ myenv
source myenv/bin/activate
```

### 2. ติดตั้ง Dependencies

```bash
# ติดตั้งทั้งหมด
pip install -r requirements.txt

# หรือติดตั้งทีละตัว
pip install Flask-OAuthlib==0.9.6
pip install requests==2.31.0
pip install python-dotenv==1.0.0
```

### 3. ตรวจสอบการติดตั้ง

```bash
python -c "import flask_oauthlib; print('Flask-OAuthlib installed successfully')"
```

## การใช้งาน

### แอปจะทำงานได้ 2 แบบ:

1. **แบบปกติ** (ไม่มี Google OAuth):
   - ใช้ email/password ล็อกอิน
   - ปุ่ม Google จะแสดงเป็นสีเทาและไม่สามารถคลิกได้

2. **แบบเต็ม** (มี Google OAuth):
   - ใช้ email/password ล็อกอิน
   - ใช้ Google OAuth ล็อกอิน
   - ปุ่ม Google จะทำงานได้ปกติ

## การตั้งค่า Google OAuth

หลังจากติดตั้ง dependencies แล้ว ให้ทำตามคู่มือใน `GOOGLE_OAUTH_SETUP.md`

## หมายเหตุ

- แอปจะแสดง warning หาก Flask-OAuthlib ไม่ได้ติดตั้ง
- ฟีเจอร์อื่นๆ จะทำงานได้ปกติแม้ไม่มี Google OAuth
- สามารถเพิ่ม Google OAuth ได้ในภายหลังโดยการติดตั้ง dependencies 