# การแก้ไขปัญหา Google OAuth

## ปัญหา: "Google OAuth ไม่พร้อมใช้งาน"

### สาเหตุ
- Flask-OAuthlib ยังไม่ได้ติดตั้ง
- Virtual environment ไม่ได้เปิดใช้งาน
- Dependencies ไม่ครบถ้วน

### วิธีแก้ไข

#### วิธีที่ 1: ใช้สคริปต์ติดตั้งอัตโนมัติ
```bash
python install_dependencies.py
```

#### วิธีที่ 2: ติดตั้งด้วยตนเอง

1. **เปิดใช้งาน Virtual Environment:**
```bash
# ใช้ venv
source venv/bin/activate

# หรือใช้ myenv
source myenv/bin/activate
```

2. **ติดตั้ง Dependencies:**
```bash
pip install Flask-OAuthlib==0.9.6
pip install requests==2.31.0
pip install python-dotenv==1.0.0
```

3. **ตรวจสอบการติดตั้ง:**
```bash
python -c "import flask_oauthlib; print('สำเร็จ!')"
```

#### วิธีที่ 3: ใช้ pip3
```bash
pip3 install Flask-OAuthlib==0.9.6
```

#### วิธีที่ 4: ใช้ --user flag
```bash
pip install --user Flask-OAuthlib==0.9.6
```

### การตรวจสอบ

หลังจากติดตั้งแล้ว ให้ตรวจสอบ:

1. **รันแอปพลิเคชัน:**
```bash
python app.py
```

2. **เปิดเบราว์เซอร์ไปที่:** `http://localhost:5000`

3. **ตรวจสอบหน้า login:**
   - ปุ่ม Google ควรแสดงเป็นสีปกติ
   - ไม่ควรมีข้อความ "Google OAuth ไม่พร้อมใช้งาน"

### หากยังมีปัญหา

1. **ตรวจสอบ Python version:**
```bash
python --version
```

2. **ตรวจสอบ pip version:**
```bash
pip --version
```

3. **ตรวจสอบ virtual environment:**
```bash
which python
which pip
```

4. **ลองสร้าง virtual environment ใหม่:**
```bash
python3 -m venv newenv
source newenv/bin/activate
pip install -r requirements.txt
```

### หมายเหตุ

- แอปจะทำงานได้ปกติแม้ไม่มี Google OAuth
- คุณสามารถใช้ email/password ล็อกอินได้
- Google OAuth เป็นฟีเจอร์เสริมเท่านั้น 