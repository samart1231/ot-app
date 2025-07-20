# การแก้ไขปัญหา Google OAuth แบบง่าย

## ปัญหา: "Google OAuth ไม่พร้อมใช้งาน"

### วิธีแก้ไขแบบง่ายที่สุด

#### 1. เปิด Terminal และไปที่โฟลเดอร์โปรเจค
```bash
cd /home/samat/ot-app
```

#### 2. ลองติดตั้งด้วยคำสั่งต่างๆ

**คำสั่งที่ 1:**
```bash
pip install Flask-OAuthlib==0.9.6
```

**คำสั่งที่ 2:**
```bash
pip3 install Flask-OAuthlib==0.9.6
```

**คำสั่งที่ 3:**
```bash
pip install --user Flask-OAuthlib==0.9.6
```

**คำสั่งที่ 4:**
```bash
python -m pip install Flask-OAuthlib==0.9.6
```

**คำสั่งที่ 5:**
```bash
python3 -m pip install Flask-OAuthlib==0.9.6
```

#### 3. ตรวจสอบการติดตั้ง
```bash
python -c "import flask_oauthlib; print('สำเร็จ!')"
```

#### 4. รันแอปพลิเคชัน
```bash
python app.py
```

### หากยังไม่สำเร็จ

#### วิธีที่ 1: ใช้ conda (หากมี)
```bash
conda install flask-oauthlib
```

#### วิธีที่ 2: ใช้ apt (Ubuntu/Debian)
```bash
sudo apt-get install python3-flask-oauthlib
```

#### วิธีที่ 3: ใช้ pacman (Arch Linux/Manjaro)
```bash
sudo pacman -S python-flask-oauthlib
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