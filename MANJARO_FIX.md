# การแก้ไขปัญหา Google OAuth บน Manjaro

## ปัญหา: "Google OAuth ไม่พร้อมใช้งาน"

### วิธีแก้ไขสำหรับ Manjaro

#### 1. เปิดใช้งาน Virtual Environment
```bash
source venv/bin/activate
```

#### 2. ลองติดตั้งด้วยคำสั่งต่างๆ

**คำสั่งที่ 1: ใช้ pip ใน virtual environment**
```bash
pip install Flask-OAuthlib==0.9.6
```

**คำสั่งที่ 2: ใช้ pip3**
```bash
pip3 install Flask-OAuthlib==0.9.6
```

**คำสั่งที่ 3: ใช้ --user flag**
```bash
pip install --user Flask-OAuthlib==0.9.6
```

**คำสั่งที่ 4: ใช้ python -m pip**
```bash
python -m pip install Flask-OAuthlib==0.9.6
```

**คำสั่งที่ 5: ใช้ python3 -m pip**
```bash
python3 -m pip install Flask-OAuthlib==0.9.6
```

#### 3. หากไม่สำเร็จ ให้ใช้ Package Manager

**ใช้ pacman:**
```bash
sudo pacman -S python-flask-oauthlib
```

**หรือใช้ yay (หากมี):**
```bash
yay -S python-flask-oauthlib
```

**หรือใช้ pamac (หากมี):**
```bash
pamac install python-flask-oauthlib
```

#### 4. ตรวจสอบการติดตั้ง
```bash
python -c "import flask_oauthlib; print('สำเร็จ!')"
```

#### 5. รันแอปพลิเคชัน
```bash
python app.py
```

### หากยังไม่สำเร็จ

#### วิธีที่ 1: อัปเดตระบบ
```bash
sudo pacman -Syu
```

#### วิธีที่ 2: ติดตั้ง Python development tools
```bash
sudo pacman -S python-pip python-setuptools
```

#### วิธีที่ 3: สร้าง virtual environment ใหม่
```bash
# ลบ virtual environment เก่า
rm -rf venv

# สร้างใหม่
python3 -m venv venv

# เปิดใช้งาน
source venv/bin/activate

# ติดตั้ง dependencies
pip install -r requirements.txt
```

### การตรวจสอบ

หลังจากติดตั้งแล้ว:
1. **รันแอป:** `python app.py`
2. **เปิดเบราว์เซอร์:** `http://localhost:5000`
3. **ตรวจสอบหน้า login:**
   - ปุ่ม Google ควรแสดงเป็นสีปกติ
   - ไม่ควรมีข้อความ "Google OAuth ไม่พร้อมใช้งาน"

### หมายเหตุ

- แอปจะทำงานได้ปกติแม้ไม่มี Google OAuth
- คุณสามารถใช้ email/password ล็อกอินได้
- Google OAuth เป็นฟีเจอร์เสริมเท่านั้น
- หากมีปัญหา ให้ลองคำสั่งต่างๆ ที่ระบุข้างต้น 