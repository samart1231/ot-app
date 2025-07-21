from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
import sqlite3
from datetime import datetime, time, timedelta
import pandas as pd
import io
import os
import re
import csv
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
# import requests
import json
from config import Config
import os

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']
DB_FILE = app.config['DATABASE_FILE']

# Google OAuth Configuration (optional)
try:
    import requests
    GOOGLE_OAUTH_AVAILABLE = True
    print("Google OAuth enabled with requests library")
except ImportError:
    GOOGLE_OAUTH_AVAILABLE = False
    print("Warning: requests not installed. Google OAuth will be disabled.")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_or_create_user_from_google(google_user_info):
    """สร้างหรือดึงข้อมูลผู้ใช้จาก Google OAuth"""
    conn = get_db_connection()
    
    # ตรวจสอบว่าผู้ใช้มีอยู่แล้วหรือไม่
    user = conn.execute(
        'SELECT id, email FROM users WHERE email = ?', (google_user_info['email'],)
    ).fetchone()
    
    if user:
        # ผู้ใช้มีอยู่แล้ว
        conn.close()
        return user
    else:
        # สร้างผู้ใช้ใหม่
        conn.execute(
            'INSERT INTO users (email, password_hash, google_id, name) VALUES (?, ?, ?, ?)',
            (google_user_info['email'], 'google_oauth', google_user_info.get('id'), google_user_info.get('name', ''))
        )
        conn.commit()
        
        # ดึงข้อมูลผู้ใช้ที่เพิ่งสร้าง
        new_user = conn.execute(
            'SELECT id, email FROM users WHERE email = ?', (google_user_info['email'],)
        ).fetchone()
        conn.close()
        return new_user

@app.route('/add', methods=['POST'])
def add_income_expense():
    # รับค่าจากฟอร์ม
    category = request.form['category']
    item = request.form['item']
    amount = request.form['amount']
    date = request.form['date']

    # รวม category กับ item เป็นข้อความเดียว
    detail = f"{category}: {item}"

    # บันทึกค่าลงฐานข้อมูล
    # db.execute('INSERT INTO income_expense (detail, amount, date) VALUES (?, ?, ?)', (detail, amount, date))

    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # ตรวจสอบความถูกต้องของข้อมูล
        if not validate_email(email):
            flash('รูปแบบ email ไม่ถูกต้อง', 'error')
            return render_template('signup.html', config={'GOOGLE_OAUTH_AVAILABLE': GOOGLE_OAUTH_AVAILABLE})
        
        if len(password) < 6:
            flash('รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร', 'error')
            return render_template('signup.html', config={'GOOGLE_OAUTH_AVAILABLE': GOOGLE_OAUTH_AVAILABLE})
        
        if password != confirm_password:
            flash('รหัสผ่านไม่ตรงกัน', 'error')
            return render_template('signup.html', config={'GOOGLE_OAUTH_AVAILABLE': GOOGLE_OAUTH_AVAILABLE})
        
        # ตรวจสอบว่า email ซ้ำหรือไม่
        conn = get_db_connection()
        existing_user = conn.execute(
            'SELECT id FROM users WHERE email = ?', (email,)
        ).fetchone()
        
        if existing_user:
            flash('Email นี้ถูกใช้งานแล้ว', 'error')
            conn.close()
            return render_template('signup.html', config={'GOOGLE_OAUTH_AVAILABLE': GOOGLE_OAUTH_AVAILABLE})
        
        # สร้างผู้ใช้ใหม่
        password_hash = generate_password_hash(password)
        conn.execute(
            'INSERT INTO users (email, password_hash) VALUES (?, ?)',
            (email, password_hash)
        )
        conn.commit()
        conn.close()
        
        flash('สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html', config={'GOOGLE_OAUTH_AVAILABLE': GOOGLE_OAUTH_AVAILABLE})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            'SELECT id, email, password_hash FROM users WHERE email = ?', (email,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            flash('เข้าสู่ระบบสำเร็จ!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email หรือรหัสผ่านไม่ถูกต้อง', 'error')

    return render_template('login.html', config={'GOOGLE_OAUTH_AVAILABLE': GOOGLE_OAUTH_AVAILABLE})


@app.route('/logout')
def logout():
    session.clear()
    flash('ออกจากระบบสำเร็จ', 'success')
    return redirect(url_for('login'))

@app.route('/login/google')
def google_login():
    """เริ่มต้น Google OAuth login"""
    if not GOOGLE_OAUTH_AVAILABLE:
        flash('Google OAuth ไม่พร้อมใช้งาน กรุณาติดตั้ง requests', 'error')
        return redirect(url_for('login'))
    
    # ตรวจสอบว่า credentials ถูกตั้งค่าหรือไม่
    if not app.config['GOOGLE_CLIENT_ID'] or not app.config['GOOGLE_CLIENT_SECRET']:
        flash('Google OAuth credentials ยังไม่ได้ตั้งค่า กรุณาตั้งค่า GOOGLE_CLIENT_ID และ GOOGLE_CLIENT_SECRET', 'error')
        return redirect(url_for('login'))
    
    import urllib.parse
    redirect_uri = url_for('google_authorized', _external=True)
    params = {
        'client_id': app.config['GOOGLE_CLIENT_ID'],
        'redirect_uri': redirect_uri,
        'scope': 'openid email profile',
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    print(f"DEBUG: Auth URL: {auth_url}")
    return redirect(auth_url)

@app.route('/login/google/authorized')
def google_authorized():
    """จัดการ callback จาก Google OAuth"""
    if not GOOGLE_OAUTH_AVAILABLE:
        flash('Google OAuth ไม่พร้อมใช้งาน', 'error')
        return redirect(url_for('login'))
    
    try:
        import requests
        import urllib.parse
        
        # รับ authorization code
        code = request.args.get('code')
        if not code:
            flash('ไม่ได้รับ authorization code จาก Google', 'error')
            return redirect(url_for('login'))
        
        print(f"DEBUG: Received code: {code}")
        
        # แลกเปลี่ยน code เป็น access token
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'client_id': app.config['GOOGLE_CLIENT_ID'],
            'client_secret': app.config['GOOGLE_CLIENT_SECRET'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('google_authorized', _external=True)
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_info = token_response.json()
        
        print(f"DEBUG: Token response: {token_info}")
        
        # ดึงข้อมูลผู้ใช้
        userinfo_url = 'https://openidconnect.googleapis.com/v1/userinfo'
        headers = {'Authorization': f"Bearer {token_info['access_token']}"}
        userinfo_response = requests.get(userinfo_url, headers=headers)
        userinfo_response.raise_for_status()
        user_info = userinfo_response.json()
        
        print(f"DEBUG: User info: {user_info}")
        
        user_info_dict = {
            'id': user_info.get('sub'),
            'email': user_info.get('email'),
            'name': user_info.get('name', ''),
            'picture': user_info.get('picture', '')
        }
        
        print(f"DEBUG: Processed user info: {user_info_dict}")
        
        # สร้างหรือดึงข้อมูลผู้ใช้
        user = get_or_create_user_from_google(user_info_dict)
        
        print(f"DEBUG: User from DB: {user}")
        
        if user:
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_name'] = user_info_dict.get('name', '')
            session['user_picture'] = user_info_dict.get('picture', '')
            flash('เข้าสู่ระบบด้วย Google สำเร็จ!', 'success')
            return redirect(url_for('index'))
        else:
            flash('เกิดข้อผิดพลาดในการเข้าสู่ระบบ', 'error')
            return redirect(url_for('login'))
    except Exception as e:
        print(f"DEBUG: Google OAuth error: {str(e)}")
        flash('การเข้าสู่ระบบด้วย Google ล้มเหลว', 'error')
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return "Welcome to the Dashboard!"

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))


def is_holiday(date_str, user_id):
    conn = get_db_connection()
    result = conn.execute('SELECT 1 FROM holidays WHERE user_id = ? AND date = ?', (user_id, date_str)).fetchone()
    conn.close()
    return result is not None


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    
    # Users table
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS users
                 (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     email TEXT UNIQUE NOT NULL,
                     password_hash TEXT NOT NULL,
                     google_id TEXT,
                     name TEXT,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )
                 ''')
    
    # เพิ่มคอลัมน์สำหรับ Google OAuth ถ้ายังไม่มี
    try:
        conn.execute('ALTER TABLE users ADD COLUMN google_id TEXT')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE users ADD COLUMN name TEXT')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS ot_records
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     user_id INTEGER NOT NULL,
                     work_date
                     TEXT,
                     start_time
                     TEXT,
                     end_time
                     TEXT,
                     ot_hours
                     REAL,
                     FOREIGN KEY (user_id) REFERENCES users (id)
                 )
                 ''')
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS income_expense
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     user_id INTEGER NOT NULL,
                     date
                     TEXT,
                     description
                     TEXT,
                     amount
                     REAL,
                     category
                     TEXT,
                     vendor
                     TEXT,
                     FOREIGN KEY (user_id) REFERENCES users (id)
                 )
                 ''')
    
    # เพิ่มคอลัมน์ vendor ถ้ายังไม่มี (สำหรับฐานข้อมูลเก่า)
    try:
        conn.execute('ALTER TABLE income_expense ADD COLUMN vendor TEXT')
    except sqlite3.OperationalError:
        # คอลัมน์มีอยู่แล้ว
        pass
    
    # เพิ่มคอลัมน์ main_category และ sub_category
    try:
        conn.execute('ALTER TABLE income_expense ADD COLUMN main_category TEXT')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE income_expense ADD COLUMN sub_category TEXT')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    # ✅ แก้ตรงนี้: เพิ่ม note
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS holidays
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     user_id INTEGER NOT NULL,
                     date
                     TEXT,
                     note
                     TEXT,
                     FOREIGN KEY (user_id) REFERENCES users (id),
                     UNIQUE(user_id, date)
                 )
                 ''')
    
    # เพิ่มตาราง work_settings
    conn.execute('''
        CREATE TABLE IF NOT EXISTS work_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            work_start_time TEXT DEFAULT '08:00',
            work_end_time TEXT DEFAULT '17:00',
            ot_rate REAL DEFAULT 50.00,
            work_days TEXT DEFAULT '1,2,3,4,5',
            lunch_start TEXT DEFAULT '12:00',
            lunch_end TEXT DEFAULT '13:00',
            morning_break_start TEXT DEFAULT '10:00',
            morning_break_end TEXT DEFAULT '10:15',
            afternoon_break_start TEXT DEFAULT '15:00',
            afternoon_break_end TEXT DEFAULT '15:15',
            evening_break_start TEXT DEFAULT '17:00',
            evening_break_end TEXT DEFAULT '17:30',
            morning_break_ot TEXT DEFAULT '0',
            afternoon_break_ot TEXT DEFAULT '0',
            evening_break_ot TEXT DEFAULT '0',
            saturday_ot_enabled TEXT DEFAULT '0',
            saturday_ot_start_time TEXT DEFAULT '12:00',
            saturday_ot_rate_multiplier TEXT DEFAULT '2.0',
            saturday_whole_day_ot TEXT DEFAULT '0',
            weekday_ot_enabled TEXT DEFAULT '0',
            weekday_ot_days TEXT DEFAULT '',
            weekday_ot_start_time TEXT DEFAULT '18:00',
            weekday_ot_rate_multiplier TEXT DEFAULT '1.5',
            night_ot_enabled TEXT DEFAULT '0',
            night_ot_rate_multiplier TEXT DEFAULT '2.0',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id)
        )
    ''')
    
    # เพิ่มคอลัมน์ใหม่สำหรับฐานข้อมูลเก่า
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN lunch_start TEXT DEFAULT "12:00"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN lunch_end TEXT DEFAULT "13:00"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN morning_break_start TEXT DEFAULT "10:00"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN morning_break_end TEXT DEFAULT "10:15"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN afternoon_break_start TEXT DEFAULT "15:00"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN afternoon_break_end TEXT DEFAULT "15:15"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN evening_break_start TEXT DEFAULT "17:00"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN evening_break_end TEXT DEFAULT "17:30"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN morning_break_ot TEXT DEFAULT "0"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN afternoon_break_ot TEXT DEFAULT "0"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN evening_break_ot TEXT DEFAULT "0"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    # เพิ่มคอลัมน์ใหม่สำหรับการตั้งค่าโอทีวันเสาร์
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN saturday_ot_enabled TEXT DEFAULT "0"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN saturday_ot_start_time TEXT DEFAULT "12:00"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN saturday_ot_rate_multiplier TEXT DEFAULT "2.0"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN saturday_whole_day_ot TEXT DEFAULT "0"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    # เพิ่มคอลัมน์ใหม่สำหรับการตั้งค่าโอทีวันธรรมดา
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN weekday_ot_enabled TEXT DEFAULT "0"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN weekday_ot_days TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN weekday_ot_start_time TEXT DEFAULT "18:00"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN weekday_ot_rate_multiplier TEXT DEFAULT "1.5"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    # เพิ่มคอลัมน์ใหม่สำหรับการตั้งค่าโอทีช่วงดึก
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN night_ot_enabled TEXT DEFAULT "0"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    try:
        conn.execute('ALTER TABLE work_settings ADD COLUMN night_ot_rate_multiplier TEXT DEFAULT "2.0"')
    except sqlite3.OperationalError:
        pass  # คอลัมน์มีอยู่แล้ว
    
    conn.commit()
    conn.close()




def calculate_night_ot(start, end, multiplier):
    """คำนวณโอทีช่วงดึก (22:00-06:00)"""
    night_start = datetime.combine(start.date(), time(22, 0))
    night_end = datetime.combine(start.date() + timedelta(days=1), time(6, 0))
    
    # คำนวณเวลาที่ทับซ้อนกับช่วงดึก
    overlap_start = max(start, night_start)
    overlap_end = min(end, night_end)
    
    if overlap_start < overlap_end:
        night_hours = (overlap_end - overlap_start).total_seconds() / 3600
        return night_hours * multiplier
    return 0.0


def calculate_saturday_ot(start, end, saturday_start_time, multiplier, whole_day_ot, breaks):
    """คำนวณโอทีวันเสาร์"""
    if whole_day_ot == '1':
        # คิดโอทีทั้งวัน
        total_hours = (end - start).total_seconds() / 3600
        # หักเวลาพัก
        for bh, bm, eh, em in breaks:
            brk_start = datetime.combine(start.date(), time(bh, bm))
            brk_end = datetime.combine(start.date(), time(eh, em))
            overlap_start = max(start, brk_start)
            overlap_end = min(end, brk_end)
            if overlap_start < overlap_end:
                total_hours -= (overlap_end - overlap_start).total_seconds() / 3600
        return total_hours * multiplier
    else:
        # คิดโอทีตามเวลาที่กำหนด
        saturday_start = datetime.combine(start.date(), datetime.strptime(saturday_start_time, "%H:%M").time())
        
        # ถ้าเริ่มงานก่อนเวลาโอที ให้เริ่มคิดจากเวลาโอที
        if start < saturday_start:
            start = saturday_start
        
        if start < end:
            total_hours = (end - start).total_seconds() / 3600
            # หักเวลาพัก
            for bh, bm, eh, em in breaks:
                brk_start = datetime.combine(start.date(), time(bh, bm))
                brk_end = datetime.combine(start.date(), time(eh, em))
                overlap_start = max(start, brk_start)
                overlap_end = min(end, brk_end)
                if overlap_start < overlap_end:
                    total_hours -= (overlap_end - overlap_start).total_seconds() / 3600
            return total_hours * multiplier
        return 0.0

def calculate_ot(start_str, end_str, user_id):
    start = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
    end = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")
    date_str = start.strftime("%Y-%m-%d")

    # ดึงการตั้งค่าเวลาทำงานของผู้ใช้
    conn = get_db_connection()
    work_settings = conn.execute('''
        SELECT work_start_time, work_end_time, work_days,
               lunch_start, lunch_end,
               evening_break_start, evening_break_end,
               evening_break_ot,
               saturday_ot_enabled, saturday_ot_start_time, saturday_ot_rate_multiplier, saturday_whole_day_ot,
               weekday_ot_enabled, weekday_ot_days, weekday_ot_start_time, weekday_ot_rate_multiplier,
               night_ot_enabled, night_ot_rate_multiplier
        FROM work_settings 
        WHERE user_id = ?
    ''', (user_id,)).fetchone()
    conn.close()
    
    # ใช้ค่าเริ่มต้นถ้าไม่มีการตั้งค่า
    work_start_time = work_settings['work_start_time'] if work_settings else '08:00'
    work_end_time = work_settings['work_end_time'] if work_settings else '17:00'
    work_days = work_settings['work_days'].split(',') if work_settings else ['1', '2', '3', '4', '5']
    
    # 🔧 แก้ไขการแปลงวันในสัปดาห์
    python_weekday = start.weekday()  # 0=จันทร์, 1=อังคาร, ..., 6=อาทิตย์
    
    # แปลงเป็นรูปแบบที่ฐานข้อมูลใช้
    if python_weekday == 6:  # อาทิตย์
        current_weekday = '0'
    else:
        current_weekday = str(python_weekday + 1)  # จันทร์=1, อังคาร=2, ...
    
    # เพิ่ม debug เพื่อตรวจสอบ
    print(f"🔍 DEBUG: Python weekday={python_weekday}, DB weekday={current_weekday}, work_days={work_days}")
    
    # เวลาพักเที่ยง
    lunch_start = work_settings['lunch_start'] if work_settings else '12:00'
    lunch_end = work_settings['lunch_end'] if work_settings else '13:00'
    
    # เวลาเบรคเย็น
    evening_break_start = work_settings['evening_break_start'] if work_settings else '17:00'
    evening_break_end = work_settings['evening_break_end'] if work_settings else '17:30'
    
    # การตั้งค่าโอทีในเบรคเย็น
    evening_break_ot = work_settings['evening_break_ot'] if work_settings else '0'
    
    # การตั้งค่าโอทีวันเสาร์
    saturday_ot_enabled = work_settings['saturday_ot_enabled'] if work_settings else '0'
    saturday_ot_start_time = work_settings['saturday_ot_start_time'] if work_settings else '12:00'
    saturday_ot_rate_multiplier = float(work_settings['saturday_ot_rate_multiplier']) if work_settings else 2.0
    saturday_whole_day_ot = work_settings['saturday_whole_day_ot'] if work_settings else '0'
    
    # การตั้งค่าโอทีวันธรรมดา
    weekday_ot_enabled = work_settings['weekday_ot_enabled'] if work_settings else '0'
    weekday_ot_days = work_settings['weekday_ot_days'].split(',') if work_settings and work_settings['weekday_ot_days'] else []
    weekday_ot_start_time = work_settings['weekday_ot_start_time'] if work_settings else '18:00'
    weekday_ot_rate_multiplier = float(work_settings['weekday_ot_rate_multiplier']) if work_settings else 1.5
    
    # การตั้งค่าโอทีช่วงดึก
    night_ot_enabled = work_settings['night_ot_enabled'] if work_settings else '0'
    night_ot_rate_multiplier = float(work_settings['night_ot_rate_multiplier']) if work_settings else 2.0
    
    # ตรวจสอบว่าเป็นวันทำงานหรือไม่
    if current_weekday not in work_days:
        print(f"❌ ไม่ใช่วันทำงาน: current_weekday={current_weekday}, work_days={work_days}")
        return 0.0

    # 🔧 แก้ไขการตรวจสอบวันเสาร์
    is_saturday = current_weekday == '6'  # เปลี่ยนจาก '5' เป็น '6'
    
    # ตรวจสอบว่าเป็นวันธรรมดาที่เปิดใช้โอทีพิเศษหรือไม่
    is_weekday_ot_enabled = weekday_ot_enabled == '1' and current_weekday in weekday_ot_days
    
    # คำนวณเวลาเริ่มงานและเลิกงานปกติ
    work_start = datetime.strptime(f"{date_str} {work_start_time}", "%Y-%m-%d %H:%M")
    work_end = datetime.strptime(f"{date_str} {work_end_time}", "%Y-%m-%d %H:%M")
    
    # เริ่มคิด OT หลังจากเวลาเลิกงานปกติ (เฉพาะเมื่อเป็นโอทีปกติ)
    # ถ้าเป็นวันเสาร์ที่เปิดใช้โอทีพิเศษ หรือวันธรรมดาที่เปิดใช้โอทีพิเศษ จะไม่บังคับให้เริ่มหลังเวลาเลิกงาน
    if not ((is_saturday and saturday_ot_enabled == '1') or is_weekday_ot_enabled):
        if start.time() < work_end.time():
            start = work_end

    # สร้างรายการเวลาพักจากฐานข้อมูล
    breaks = []
    
    # ตรวจสอบว่าเป็นวันหยุดหรือไม่
    if is_holiday(date_str, user_id):
        # วันหยุด - มีแค่พักเที่ยง
        lunch_start_h, lunch_start_m = map(int, lunch_start.split(':'))
        lunch_end_h, lunch_end_m = map(int, lunch_end.split(':'))
        breaks.append((lunch_start_h, lunch_start_m, lunch_end_h, lunch_end_m))
    else:
        # วันทำงานปกติ - มีพักเที่ยงและเบรคเย็น (จันทร์-เสาร์)
        # เพิ่มเวลาพักเที่ยง
        lunch_start_h, lunch_start_m = map(int, lunch_start.split(':'))
        lunch_end_h, lunch_end_m = map(int, lunch_end.split(':'))
        breaks.append((lunch_start_h, lunch_start_m, lunch_end_h, lunch_end_m))
        
        # เพิ่มเวลาเบรคเย็น (จันทร์-เสาร์) ถ้าไม่คิดโอที
        if evening_break_ot == '0':
            evening_start_h, evening_start_m = map(int, evening_break_start.split(':'))
            evening_end_h, evening_end_m = map(int, evening_break_end.split(':'))
            breaks.append((evening_start_h, evening_start_m, evening_end_h, evening_end_m))

    # คำนวณโอทีตามลำดับความสำคัญ
    total_ot_hours = 0.0
    
    # 1. โอทีช่วงดึก (22:00-06:00) - สูงสุด
    if night_ot_enabled == '1':
        night_ot_hours = calculate_night_ot(start, end, night_ot_rate_multiplier)
        total_ot_hours += night_ot_hours
    
    # 2. โอทีวันเสาร์
    if is_saturday and saturday_ot_enabled == '1':
        saturday_ot_hours = calculate_saturday_ot(start, end, saturday_ot_start_time, saturday_ot_rate_multiplier, saturday_whole_day_ot, breaks)
        total_ot_hours += saturday_ot_hours
    
    # 3. โอทีวันธรรมดา
    elif is_weekday_ot_enabled:
        weekday_ot_hours = calculate_weekday_ot(start, end, weekday_ot_start_time, weekday_ot_rate_multiplier, breaks)
        total_ot_hours += weekday_ot_hours
    
    # 4. โอทีปกติ (หลังเวลาเลิกงาน)
    else:
        normal_ot_hours = calculate_normal_ot(start, end, breaks)
        total_ot_hours += normal_ot_hours

    print(f"🔍 DEBUG: Final OT hours = {total_ot_hours}")
    return round(total_ot_hours, 2)

def calculate_weekday_ot(start, end, weekday_start_time, multiplier, breaks):
    """คำนวณโอทีวันธรรมดา"""
    weekday_start = datetime.combine(start.date(), datetime.strptime(weekday_start_time, "%H:%M").time())
    
    # ถ้าเริ่มงานก่อนเวลาโอที ให้เริ่มคิดจากเวลาโอที
    if start < weekday_start:
        start = weekday_start
    
    if start < end:
        total_hours = (end - start).total_seconds() / 3600
        # หักเวลาพัก
        for bh, bm, eh, em in breaks:
            brk_start = datetime.combine(start.date(), time(bh, bm))
            brk_end = datetime.combine(start.date(), time(eh, em))
            overlap_start = max(start, brk_start)
            overlap_end = min(end, brk_end)
            if overlap_start < overlap_end:
                total_hours -= (overlap_end - overlap_start).total_seconds() / 3600
        return total_hours * multiplier
    return 0.0


def calculate_normal_ot(start, end, breaks):
    """คำนวณโอทีปกติ (หลังเวลาเลิกงาน)"""
    total_seconds = (end - start).total_seconds()

    for bh, bm, eh, em in breaks:
        brk_start = datetime.combine(start.date(), time(bh, bm))
        brk_end = datetime.combine(start.date(), time(eh, em))
        overlap_start = max(start, brk_start)
        overlap_end = min(end, brk_end)
        if overlap_start < overlap_end:
            total_seconds -= (overlap_end - overlap_start).total_seconds()

    return max(total_seconds / 3600, 0)


@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    conn = get_db_connection()
    user_id = session['user_id']
    
    if request.method == 'POST':
        work_date = request.form['work_date']
        end_time = request.form['end_time']
        
        # ดึงเวลาเริ่มงานจากฐานข้อมูล
        work_settings = conn.execute('''
            SELECT work_start_time 
            FROM work_settings 
            WHERE user_id = ?
        ''', (user_id,)).fetchone()
        
        work_start_time = work_settings['work_start_time'] if work_settings else '08:00'
        start_time = f"{work_date}T{work_start_time}"
        
        ot_hours = calculate_ot(start_time, end_time, user_id)
        conn.execute('INSERT INTO ot_records (user_id, work_date, start_time, end_time, ot_hours) VALUES (?, ?, ?, ?, ?)',
                     (user_id, work_date, start_time, end_time, ot_hours))
        conn.commit()
        return redirect(url_for('index'))

    # รับเดือนที่เลือก หรือใช้เดือนปัจจุบันเป็นค่าเริ่มต้น
    from datetime import datetime
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))

    sort_order = request.args.get('sort', 'desc')
    order_sql = 'ORDER BY work_date DESC' if sort_order == 'desc' else 'ORDER BY work_date ASC'
    
    # กรองข้อมูลตามเดือนที่เลือกและ user_id
    month_filter = f"WHERE user_id = ? AND strftime('%Y-%m', work_date) = ?"
    
    # นับจำนวนรายการในเดือนที่เลือก
    total_records = conn.execute(f'SELECT COUNT(*) FROM ot_records {month_filter}', (user_id, selected_month)).fetchone()[0]
    
    # ดึงข้อมูลทั้งหมดสำหรับเดือนที่เลือก (ไม่มี pagination)
    records = conn.execute(f'SELECT * FROM ot_records {month_filter} {order_sql}', 
                          (user_id, selected_month)).fetchall()
    
    # คำนวณ OT รวมสำหรับเดือนที่เลือก
    monthly_total_ot = conn.execute(f'SELECT SUM(ot_hours) FROM ot_records {month_filter}', (user_id, selected_month)).fetchone()[0] or 0
    
    # ดึงรายการเดือนทั้งหมดที่มีข้อมูล
    available_months = conn.execute('''
                                   SELECT DISTINCT strftime('%Y-%m', work_date) AS month
                                   FROM ot_records
                                   WHERE user_id = ?
                                   ORDER BY month DESC
                                   ''', (user_id,)).fetchall()
    
    # สร้างรายการเดือนสำหรับเลือก (ย้อนหลัง 12 เดือน และล่วงหน้า 6 เดือน)
    from datetime import datetime, timedelta
    import calendar
    
    selectable_months = []
    current_date = datetime.now()
    
    # สร้างรายการเดือน (ย้อนหลัง 12 เดือน)
    for i in range(12, -1, -1):  # 12 เดือนย้อนหลัง + เดือนปัจจุบัน
        date = datetime(current_date.year, current_date.month, 1) - timedelta(days=i*30)
        date = date.replace(day=1)  # ให้เป็นวันที่ 1 ของเดือน
        month_str = date.strftime('%Y-%m')
        
        # ตรวจสอบว่าเดือนนี้มีข้อมูลหรือไม่
        has_data = any(month['month'] == month_str for month in available_months)
        
        selectable_months.append({
            'month': month_str,
            'display': f"{date.strftime('%Y-%m')} ({calendar.month_name[date.month]} {date.year})",
            'has_data': has_data
        })
    
    # เพิ่มเดือนล่วงหน้า 6 เดือน
    for i in range(1, 7):
        date = datetime(current_date.year, current_date.month, 1) + timedelta(days=i*32)
        date = date.replace(day=1)  # ให้เป็นวันที่ 1 ของเดือน
        month_str = date.strftime('%Y-%m')
        
        selectable_months.append({
            'month': month_str,
            'display': f"{date.strftime('%Y-%m')} ({calendar.month_name[date.month]} {date.year})",
            'has_data': False  # เดือนล่วงหน้าจะไม่มีข้อมูล
        })
    
    # ดึงข้อมูลสำหรับตารางรวมรายเดือน (แสดงทุกเดือน)
    monthly_ot = conn.execute('''
                              SELECT strftime('%Y-%m', work_date) AS month, SUM(ot_hours) AS total
                              FROM ot_records
                              WHERE user_id = ?
                              GROUP BY month
                              ORDER BY month DESC
                              ''', (user_id,)).fetchall()
    
    # คำนวณ OT รวมทั้งหมด
    total_ot = conn.execute('SELECT SUM(ot_hours) FROM ot_records WHERE user_id = ?', (user_id,)).fetchone()[0] or 0
    
    # ดึงเวลาเริ่มงานสำหรับแสดงในหน้า
    work_settings = conn.execute('''
        SELECT work_start_time 
        FROM work_settings 
        WHERE user_id = ?
    ''', (user_id,)).fetchone()
    
    work_start_time = work_settings['work_start_time'] if work_settings else '08:00'
    
    conn.close()
    return render_template('index.html', 
                         records=records, 
                         monthly_total_ot=round(monthly_total_ot, 2),
                         total_ot=round(total_ot, 2),
                         sort_order=sort_order, 
                         monthly_ot=monthly_ot,
                         page=1, 
                         total_pages=1, 
                         total_records=total_records,
                         selected_month=selected_month,
                         available_months=selectable_months,
                         work_start_time=work_start_time)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_ot(id):
    conn = get_db_connection()
    user_id = session['user_id']
    if request.method == 'POST':
        work_date = request.form['work_date']
        end_time = request.form['end_time']
        start_time = f"{work_date}T08:00"
        ot_hours = calculate_ot(start_time, end_time, user_id)
        conn.execute('''
                     UPDATE ot_records
                     SET work_date=?,
                         start_time=?,
                         end_time=?,
                         ot_hours=?
                     WHERE id = ? AND user_id = ?
                     ''', (work_date, start_time, end_time, ot_hours, id, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    record = conn.execute('SELECT * FROM ot_records WHERE id=? AND user_id=?', (id, user_id)).fetchone()
    conn.close()
    return render_template('edit_ot.html', record=record)


@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    conn = get_db_connection()
    user_id = session['user_id']
    conn.execute('DELETE FROM ot_records WHERE id=? AND user_id=?', (id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/income-expense', methods=['GET', 'POST'])
@login_required
def income_expense():
    conn = get_db_connection()
    user_id = session['user_id']
    
    if request.method == 'POST':
        # Debug: แสดงข้อมูลที่ได้รับ
        print("=== DEBUG: Form Data ===")
        print("Form data:", request.form)
        print("Files:", request.files)
        
        date = request.form['date']
        category = request.form['category']  # income หรือ expense
        main_category = request.form.get('main_category', '')
        sub_category = request.form.get('sub_category', '')
        combined_category = request.form.get('combined_category', '')
        items_data = request.form.get('items_data')  # JSON string จาก JavaScript
        description = request.form.get('description', '')  # รายการสินค้าที่สร้างอัตโนมัติ
        amount = request.form.get('amount')
        calculated_amount = request.form.get('calculated_amount')
        vendor = request.form.get('vendor') or None

        print("=== DEBUG: Parsed Data ===")
        print("Date:", date)
        print("Category:", category)
        print("Main Category:", main_category)
        print("Sub Category:", sub_category)
        print("Combined Category:", combined_category)
        print("Items Data:", items_data)
        print("Description:", description)
        print("Amount:", amount)
        print("Calculated Amount:", calculated_amount)
        print("Vendor:", vendor)

        # ตรวจสอบประเภทรายการ
        if category == 'income':
            # สำหรับรายรับ
            if not amount or float(amount) <= 0:
                flash('กรุณากรอกจำนวนเงินที่ถูกต้อง', 'error')
                return redirect('/income-expense')
            
            if not description:
                description = f"รายรับ: {main_category}"
            
            conn.execute('''
                         INSERT INTO income_expense (user_id, date, description, amount, category, vendor, main_category, sub_category)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                         ''', (user_id, date, description, float(amount), 'income', vendor, main_category, sub_category))
        else:
            # สำหรับรายจ่าย
            if not items_data:
                flash('กรุณาเลือกรายการสินค้า', 'error')
                return redirect('/income-expense')

            # ใช้ calculated_amount หรือ amount
            final_amount = float(calculated_amount) if calculated_amount else float(amount or 0)
            
            if final_amount <= 0:
                flash('กรุณากรอกจำนวนเงินที่ถูกต้อง', 'error')
                return redirect('/income-expense')

            conn.execute('''
                         INSERT INTO income_expense (user_id, date, description, amount, category, vendor, main_category, sub_category)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                         ''', (user_id, date, description, final_amount, 'expense', vendor, main_category, sub_category))

        conn.commit()
        flash('บันทึกข้อมูลเรียบร้อยแล้ว', 'success')
        return redirect('/income-expense')

    # รับเดือนที่เลือก หรือใช้เดือนปัจจุบันเป็นค่าเริ่มต้น
    from datetime import datetime
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    sort_order = request.args.get('sort', 'desc')
    order_sql = 'ORDER BY date DESC' if sort_order == 'desc' else 'ORDER BY date ASC'
    
    # กรองข้อมูลตามเดือนที่เลือกและ user_id
    month_filter = f"WHERE user_id = ? AND strftime('%Y-%m', date) = ?"
    
    # นับจำนวนรายการในเดือนที่เลือก
    total_records = conn.execute(f'SELECT COUNT(*) FROM income_expense {month_filter}', (user_id, selected_month)).fetchone()[0]
    
    # ดึงข้อมูลทั้งหมดสำหรับเดือนที่เลือก (ไม่มี pagination)
    records = conn.execute(f'SELECT * FROM income_expense {month_filter} {order_sql}', 
                          (user_id, selected_month)).fetchall()
    
    # คำนวณยอดรวมสำหรับเดือนที่เลือก
    monthly_total_income = conn.execute(f'SELECT SUM(amount) FROM income_expense {month_filter} AND category="income"', (user_id, selected_month)).fetchone()[0] or 0
    monthly_total_expense = conn.execute(f'SELECT SUM(amount) FROM income_expense {month_filter} AND category="expense"', (user_id, selected_month)).fetchone()[0] or 0
    
    # ดึงรายการเดือนทั้งหมดที่มีข้อมูล
    available_months = conn.execute('''
                                   SELECT DISTINCT strftime('%Y-%m', date) AS month
                                   FROM income_expense
                                   WHERE user_id = ?
                                   ORDER BY month DESC
                                   ''', (user_id,)).fetchall()
    
    # สร้างรายการเดือนสำหรับเลือก (ย้อนหลัง 12 เดือน และล่วงหน้า 6 เดือน)
    from datetime import datetime, timedelta
    import calendar
    
    selectable_months = []
    current_date = datetime.now()
    
    # สร้างรายการเดือน (ย้อนหลัง 12 เดือน)
    for i in range(12, -1, -1):  # 12 เดือนย้อนหลัง + เดือนปัจจุบัน
        date = datetime(current_date.year, current_date.month, 1) - timedelta(days=i*30)
        date = date.replace(day=1)  # ให้เป็นวันที่ 1 ของเดือน
        month_str = date.strftime('%Y-%m')
        
        # ตรวจสอบว่าเดือนนี้มีข้อมูลหรือไม่
        has_data = any(month['month'] == month_str for month in available_months)
        
        selectable_months.append({
            'month': month_str,
            'display': f"{date.strftime('%Y-%m')} ({calendar.month_name[date.month]} {date.year})",
            'has_data': has_data
        })
    
    # เพิ่มเดือนล่วงหน้า 6 เดือน
    for i in range(1, 7):
        date = datetime(current_date.year, current_date.month, 1) + timedelta(days=i*32)
        date = date.replace(day=1)  # ให้เป็นวันที่ 1 ของเดือน
        month_str = date.strftime('%Y-%m')
        
        selectable_months.append({
            'month': month_str,
            'display': f"{date.strftime('%Y-%m')} ({calendar.month_name[date.month]} {date.year})",
            'has_data': False  # เดือนล่วงหน้าจะไม่มีข้อมูล
        })
    
    # คำนวณยอดรวมทั้งหมด
    total_income = conn.execute('SELECT SUM(amount) FROM income_expense WHERE user_id = ? AND category="income"', (user_id,)).fetchone()[0] or 0
    total_expense = conn.execute('SELECT SUM(amount) FROM income_expense WHERE user_id = ? AND category="expense"', (user_id,)).fetchone()[0] or 0
    
    # ดึงข้อมูลสำหรับตารางสรุปรายเดือน (แสดงทุกเดือน)
    monthly_summary = conn.execute('''
                                   SELECT strftime('%Y-%m', date) AS month, category, SUM(amount) AS total
                                   FROM income_expense
                                   WHERE user_id = ?
                                   GROUP BY month, category
                                   ORDER BY month DESC
                                   ''', (user_id,)).fetchall()
    
    conn.close()
    return render_template('income_expense.html', 
                         records=records,
                         monthly_total_income=monthly_total_income,
                         monthly_total_expense=monthly_total_expense,
                         total_income=total_income, 
                         total_expense=total_expense,
                         monthly_summary=monthly_summary,
                         selected_month=selected_month,
                         available_months=selectable_months,
                         total_records=total_records,
                         sort_order=sort_order)


@app.route('/edit-income-expense/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_income_expense(id):
    conn = get_db_connection()
    user_id = session['user_id']
    if request.method == 'POST':
        date = request.form['date']
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        vendor = request.form['vendor']  # ✅ ต้องมีตัวนี้
        main_category = request.form.get('main_category', '')
        sub_category = request.form.get('sub_category', '')

        conn.execute('''
                     UPDATE income_expense
                     SET date=?,
                         description=?,
                         amount=?,
                         category=?,
                         vendor=?,
                         main_category=?,
                         sub_category=?
                     WHERE id = ? AND user_id = ?
                     ''', (date, description, amount, category, vendor, main_category, sub_category, id, user_id))  # ✅ ครบ 9 ค่า
        conn.commit()
        conn.close()
        return redirect('/income-expense')

    record = conn.execute('SELECT * FROM income_expense WHERE id=? AND user_id=?', (id, user_id)).fetchone()
    conn.close()
    return render_template('edit_income_expense.html', record=record)


@app.route('/delete-income-expense/<int:id>', methods=['POST'])
@login_required
def delete_income_expense(id):
    conn = get_db_connection()
    user_id = session['user_id']
    conn.execute('DELETE FROM income_expense WHERE id=? AND user_id=?', (id, user_id))
    conn.commit()
    conn.close()
    return redirect('/income-expense')


@app.route('/export-<category>/<year_month>')
@login_required
def export_income_expense_month(category, year_month):
    conn = get_db_connection()
    user_id = session['user_id']
    
    # Check if year_month is a year (4 digits) or year-month (7 digits)
    if len(year_month) == 4:  # Year only
        if category == 'all':
            df = pd.read_sql_query('''
                                   SELECT *
                                   FROM income_expense
                                   WHERE user_id = ? AND strftime('%Y', date) = ?
                                   ORDER BY date ASC
                                   ''', conn, params=[user_id, year_month])
            filename = f"income_expense_{year_month}.csv"
        else:
            df = pd.read_sql_query('''
                                   SELECT *
                                   FROM income_expense
                                   WHERE user_id = ? AND strftime('%Y', date) = ?
                                     AND category = ?
                                   ORDER BY date ASC
                                   ''', conn, params=[user_id, year_month, category])
            filename = f"{category}_{year_month}.csv"
    else:  # Year-month format
        if category == 'all':
            df = pd.read_sql_query('''
                                   SELECT *
                                   FROM income_expense
                                   WHERE user_id = ? AND strftime('%Y-%m', date) = ?
                                   ORDER BY date ASC
                                   ''', conn, params=[user_id, year_month])
            filename = f"income_expense_{year_month}.csv"
        else:
            df = pd.read_sql_query('''
                                   SELECT *
                                   FROM income_expense
                                   WHERE user_id = ? AND strftime('%Y-%m', date) = ?
                                     AND category = ?
                                   ORDER BY date ASC
                                   ''', conn, params=[user_id, year_month, category])
            filename = f"{category}_{year_month}.csv"
    
    conn.close()

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_buffer.seek(0)

    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


@app.route('/export-year/<year>')
@login_required
def export_year_ot(year):
    conn = get_db_connection()
    user_id = session['user_id']
    df = pd.read_sql_query('''
                           SELECT *
                           FROM ot_records
                           WHERE user_id = ? AND strftime('%Y', work_date) = ?
                           ORDER BY work_date ASC
                           ''', conn, params=[user_id, year])
    conn.close()

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_buffer.seek(0)

    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"ot_{year}.csv"
    )


@app.route('/export-month/<year_month>')
@login_required
def export_month_csv(year_month):
    conn = get_db_connection()
    user_id = session['user_id']
    df = pd.read_sql_query('''
                           SELECT *
                           FROM ot_records
                           WHERE user_id = ? AND strftime('%Y-%m', work_date) = ?
                           ORDER BY work_date ASC
                           ''', conn, params=[user_id, year_month])
    conn.close()

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_buffer.seek(0)

    filename = f"ot_{year_month}.csv"
    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


@app.route('/month/<year_month>')
@login_required
def month_view(year_month):
    conn = get_db_connection()
    user_id = session['user_id']
    records = conn.execute('''
                           SELECT *
                           FROM ot_records
                           WHERE user_id = ? AND strftime('%Y-%m', work_date) = ?
                           ORDER BY work_date ASC
                           ''', (user_id, year_month)).fetchall()
    total = sum(row['ot_hours'] for row in records)
    conn.close()
    return render_template('month.html', records=records, month=year_month, total=round(total, 2))


@app.route('/income-expense/month/<year_month>')
@login_required
def income_expense_month_view(year_month):
    conn = get_db_connection()
    user_id = session['user_id']
    records = conn.execute('''
                           SELECT *
                           FROM income_expense
                           WHERE user_id = ? AND strftime('%Y-%m', date) = ?
                           ORDER BY date DESC
                           ''', (user_id, year_month)).fetchall()
    conn.close()

    return render_template('income_expense_month.html', records=records, year_month=year_month)


@app.route('/income-expense/year/<year>')
@login_required
def income_expense_year_view(year):
    conn = get_db_connection()
    user_id = session['user_id']
    
    # Get all records for the year
    records = conn.execute('''
                           SELECT *
                           FROM income_expense
                           WHERE user_id = ? AND strftime('%Y', date) = ?
                           ORDER BY date DESC
                           ''', (user_id, year)).fetchall()
    
    # Calculate yearly totals
    yearly_income = conn.execute('''
                                  SELECT COALESCE(SUM(amount), 0) as total
                                  FROM income_expense
                                  WHERE user_id = ? AND strftime('%Y', date) = ? AND category = 'income'
                                  ''', (user_id, year)).fetchone()['total']
    
    yearly_expense = conn.execute('''
                                   SELECT COALESCE(SUM(amount), 0) as total
                                   FROM income_expense
                                   WHERE user_id = ? AND strftime('%Y', date) = ? AND category = 'expense'
                                   ''', (user_id, year)).fetchone()['total']
    
    # Get monthly breakdown
    monthly_data = conn.execute('''
                                 SELECT strftime('%Y-%m', date) as month,
                                        SUM(CASE WHEN category = 'income' THEN amount ELSE 0 END) as income,
                                        SUM(CASE WHEN category = 'expense' THEN amount ELSE 0 END) as expense,
                                        COUNT(*) as count
                                 FROM income_expense
                                 WHERE user_id = ? AND strftime('%Y', date) = ?
                                 GROUP BY strftime('%Y-%m', date)
                                 ORDER BY month ASC
                                 ''', (user_id, year)).fetchall()
    
    conn.close()
    
    return render_template('income_expense_year.html', 
                         records=records, 
                         year=year, 
                         yearly_income=yearly_income,
                         yearly_expense=yearly_expense,
                         monthly_data=monthly_data)


@app.route('/delete-income-expense-month/<int:id>', methods=['POST'])
@login_required
def delete_income_expense_month(id):
    conn = get_db_connection()
    user_id = session['user_id']
    conn.execute('DELETE FROM income_expense WHERE id=? AND user_id=?', (id, user_id))
    conn.commit()
    conn.close()
    return redirect(request.referrer or '/income-expense')  # กลับไปหน้าก่อนหน้า


from datetime import datetime


@app.route('/holidays', methods=['GET', 'POST'])
@login_required
def manage_holidays():
    conn = get_db_connection()
    user_id = session['user_id']

    if request.method == 'POST':
        date = request.form['date']
        note = request.form['note']
        conn.execute('INSERT INTO holidays (user_id, date, note) VALUES (?, ?, ?)', (user_id, date, note))
        conn.commit()
        return redirect('/holidays')

    # 🟡 Filter ปีจาก query parameter เช่น ?year=2025
    year = request.args.get('year', datetime.now().year)
    holidays = conn.execute('''
                            SELECT *
                            FROM holidays
                            WHERE user_id = ? AND strftime('%Y', date) = ?
                            ORDER BY date DESC
                            ''', (user_id, str(year))).fetchall()
    conn.close()
    return render_template('holidays.html', holidays=holidays, selected_year=year)


@app.route('/delete-holiday/<int:id>', methods=['POST'])
@login_required
def delete_holiday(id):
    print(f"กำลังลบ holiday id={id}")
    conn = get_db_connection()
    user_id = session['user_id']
    conn.execute('DELETE FROM holidays WHERE id=? AND user_id=?', (id, user_id))
    conn.commit()
    conn.close()
    return redirect('/holidays')


@app.route('/import-csv', methods=['GET', 'POST'])
@login_required
def import_csv():
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('กรุณาเลือกไฟล์ CSV', 'error')
            return redirect('/import-csv')
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('กรุณาเลือกไฟล์ CSV', 'error')
            return redirect('/import-csv')
        
        if not file.filename.endswith('.csv'):
            flash('กรุณาเลือกไฟล์ CSV เท่านั้น', 'error')
            return redirect('/import-csv')
        
        try:
            # อ่านไฟล์ CSV
            df = pd.read_csv(file, encoding='utf-8')
            
            # ตรวจสอบคอลัมน์ที่จำเป็น
            required_columns = ['date', 'description', 'amount', 'category']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                flash(f'ไฟล์ CSV ต้องมีคอลัมน์: {", ".join(missing_columns)}', 'error')
                return redirect('/import-csv')
            
            conn = get_db_connection()
            user_id = session['user_id']
            
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # ตรวจสอบข้อมูล
                    date = str(row['date']).strip()
                    description = str(row['description']).strip()
                    amount = float(row['amount'])
                    category = str(row['category']).strip().lower()
                    vendor = str(row.get('vendor', '')).strip() if 'vendor' in df.columns else None
                    
                    # ตรวจสอบความถูกต้องของข้อมูล
                    if not date or not description or amount <= 0:
                        errors.append(f'แถว {index + 1}: ข้อมูลไม่ครบถ้วนหรือไม่ถูกต้อง')
                        error_count += 1
                        continue
                    
                    # ตรวจสอบรูปแบบวันที่
                    try:
                        datetime.strptime(date, '%Y-%m-%d')
                    except ValueError:
                        errors.append(f'แถว {index + 1}: รูปแบบวันที่ไม่ถูกต้อง (ใช้ YYYY-MM-DD)')
                        error_count += 1
                        continue
                    
                    # ตรวจสอบประเภท
                    if category not in ['income', 'expense']:
                        errors.append(f'แถว {index + 1}: ประเภทต้องเป็น income หรือ expense')
                        error_count += 1
                        continue
                    
                    # บันทึกข้อมูล
                    conn.execute('''
                                 INSERT INTO income_expense (user_id, date, description, amount, category, vendor)
                                 VALUES (?, ?, ?, ?, ?, ?)
                                 ''', (user_id, date, description, amount, category, vendor))
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f'แถว {index + 1}: {str(e)}')
                    error_count += 1
            
            conn.commit()
            conn.close()
            
            if success_count > 0:
                flash(f'นำเข้าข้อมูลสำเร็จ {success_count} รายการ', 'success')
            
            if error_count > 0:
                flash(f'มีข้อผิดพลาด {error_count} รายการ', 'error')
                # บันทึก error log
                with open('import_errors.log', 'a', encoding='utf-8') as f:
                    f.write(f'\n=== Import Errors {datetime.now()} ===\n')
                    for error in errors:
                        f.write(f'{error}\n')
            
            return redirect('/income-expense')
            
        except Exception as e:
            flash(f'เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}', 'error')
            return redirect('/import-csv')
    
    return render_template('import_csv.html')

@app.route('/export-template')
@login_required
def export_template():
    # สร้างไฟล์ template CSV
    template_data = {
        'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'description': ['เงินเดือน', 'ซื้ออาหาร', 'ค่าเดินทาง'],
        'amount': [50000, 150, 50],
        'category': ['income', 'expense', 'expense'],
        'vendor': ['บริษัท', 'ร้านอาหาร', 'รถเมล์']
    }
    
    df = pd.DataFrame(template_data)
    
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_buffer.seek(0)
    
    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='income_expense_template.csv'
    )

@app.route('/import-ot-csv', methods=['GET', 'POST'])
@login_required
def import_ot_csv():
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('กรุณาเลือกไฟล์ CSV', 'error')
            return redirect('/import-ot-csv')
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('กรุณาเลือกไฟล์ CSV', 'error')
            return redirect('/import-ot-csv')
        
        if not file.filename.endswith('.csv'):
            flash('กรุณาเลือกไฟล์ CSV เท่านั้น', 'error')
            return redirect('/import-ot-csv')
        
        try:
            # อ่านไฟล์ CSV
            df = pd.read_csv(file, encoding='utf-8')
            
            # ตรวจสอบคอลัมน์ที่จำเป็น
            required_columns = ['work_date', 'end_time']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                flash(f'ไฟล์ CSV ต้องมีคอลัมน์: {", ".join(missing_columns)}', 'error')
                return redirect('/import-ot-csv')
            
            conn = get_db_connection()
            user_id = session['user_id']
            
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # ตรวจสอบข้อมูล
                    work_date = str(row['work_date']).strip()
                    end_time = str(row['end_time']).strip()
                    
                    # ตรวจสอบความถูกต้องของข้อมูล
                    if not work_date or not end_time:
                        errors.append(f'แถว {index + 1}: ข้อมูลไม่ครบถ้วน')
                        error_count += 1
                        continue
                    
                    # ตรวจสอบรูปแบบวันที่
                    try:
                        datetime.strptime(work_date, '%Y-%m-%d')
                    except ValueError:
                        errors.append(f'แถว {index + 1}: รูปแบบวันที่ไม่ถูกต้อง (ใช้ YYYY-MM-DD)')
                        error_count += 1
                        continue
                    
                    # ตรวจสอบรูปแบบเวลา
                    try:
                        # รองรับหลายรูปแบบ
                        if 'T' in end_time:
                            datetime.strptime(end_time, '%Y-%m-%dT%H:%M')
                        else:
                            # ถ้าไม่มี T ให้เพิ่มเข้าไป
                            end_time = f"{work_date}T{end_time}"
                            datetime.strptime(end_time, '%Y-%m-%dT%H:%M')
                    except ValueError:
                        errors.append(f'แถว {index + 1}: รูปแบบเวลาไม่ถูกต้อง (ใช้ HH:MM หรือ YYYY-MM-DDTHH:MM)')
                        error_count += 1
                        continue
                    
                    # สร้าง start_time (08:00 ของวันที่ทำงาน)
                    start_time = f"{work_date}T08:00"
                    
                    # คำนวณ OT hours
                    ot_hours = calculate_ot(start_time, end_time, user_id)
                    
                    # บันทึกข้อมูล
                    conn.execute('''
                                 INSERT INTO ot_records (user_id, work_date, start_time, end_time, ot_hours)
                                 VALUES (?, ?, ?, ?, ?)
                                 ''', (user_id, work_date, start_time, end_time, ot_hours))
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f'แถว {index + 1}: {str(e)}')
                    error_count += 1
            
            conn.commit()
            conn.close()
            
            if success_count > 0:
                flash(f'นำเข้าข้อมูล OT สำเร็จ {success_count} รายการ', 'success')
            
            if error_count > 0:
                flash(f'มีข้อผิดพลาด {error_count} รายการ', 'error')
                # บันทึก error log
                with open('import_ot_errors.log', 'a', encoding='utf-8') as f:
                    f.write(f'\n=== Import OT Errors {datetime.now()} ===\n')
                    for error in errors:
                        f.write(f'{error}\n')
            
            return redirect('/index')
            
        except Exception as e:
            flash(f'เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}', 'error')
            return redirect('/import-ot-csv')
    
    return render_template('import_ot_csv.html')

@app.route('/export-ot-template')
@login_required
def export_ot_template():
    # สร้างไฟล์ template CSV สำหรับ OT
    template_data = {
        'work_date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'end_time': ['2024-01-01T20:00', '2024-01-02T19:30', '2024-01-03T18:00']
    }
    
    df = pd.DataFrame(template_data)
    
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_buffer.seek(0)
    
    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='ot_records_template.csv'
    )

# Settings page
@app.route('/settings')
@login_required
def settings():
    conn = get_db_connection()
    user_id = session['user_id']
    
    # ดึงการตั้งค่าเวลาทำงานของผู้ใช้
    work_settings = conn.execute('''
        SELECT work_start_time, work_end_time, ot_rate, work_days,
               lunch_start, lunch_end,
               evening_break_start, evening_break_end,
               evening_break_ot,
               saturday_ot_enabled, saturday_ot_start_time, saturday_ot_rate_multiplier, saturday_whole_day_ot,
               weekday_ot_enabled, weekday_ot_days, weekday_ot_start_time, weekday_ot_rate_multiplier,
               night_ot_enabled, night_ot_rate_multiplier
        FROM work_settings 
        WHERE user_id = ?
    ''', (user_id,)).fetchone()
    
    conn.close()
    
    return render_template('settings.html', work_settings=work_settings)

# Change password
@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password != confirm_password:
        flash('รหัสผ่านใหม่ไม่ตรงกัน', 'error')
        return redirect('/settings')
    
    if len(new_password) < 6:
        flash('รหัสผ่านใหม่ต้องมีอย่างน้อย 6 ตัวอักษร', 'error')
        return redirect('/settings')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if not check_password_hash(user['password_hash'], current_password):
        conn.close()
        flash('รหัสผ่านปัจจุบันไม่ถูกต้อง', 'error')
        return redirect('/settings')
    
    hashed_password = generate_password_hash(new_password)
    conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (hashed_password, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('เปลี่ยนรหัสผ่านสำเร็จ', 'success')
    return redirect('/settings')

# Update work time settings
@app.route('/update-work-time-settings', methods=['POST'])
@login_required
def update_work_time_settings():
    user_id = session['user_id']
    work_start_time = request.form.get('work_start_time', '08:00')
    work_end_time = request.form.get('work_end_time', '17:00')
    ot_rate = request.form.get('ot_rate', '50.00')
    work_days = request.form.getlist('work_days')
    
    # เวลาพักเที่ยง
    lunch_start = request.form.get('lunch_start', '12:00')
    lunch_end = request.form.get('lunch_end', '13:00')
    
    # เวลาเบรคเย็น
    evening_break_start = request.form.get('evening_break_start', '17:00')
    evening_break_end = request.form.get('evening_break_end', '17:30')
    
    # การตั้งค่าโอทีในเบรคเย็น
    evening_break_ot = '1' if request.form.get('evening_break_ot') else '0'
    
    # การตั้งค่าโอทีวันเสาร์
    saturday_ot_enabled = '1' if request.form.get('saturday_ot_enabled') else '0'
    saturday_ot_start_time = request.form.get('saturday_ot_start_time', '12:00')
    saturday_ot_rate_multiplier = request.form.get('saturday_ot_rate_multiplier', '2.0')
    saturday_whole_day_ot = '1' if request.form.get('saturday_whole_day_ot') else '0'
    
    # การตั้งค่าโอทีวันธรรมดา
    weekday_ot_enabled = '1' if request.form.get('weekday_ot_enabled') else '0'
    weekday_ot_days = request.form.getlist('weekday_ot_days')
    weekday_ot_start_time = request.form.get('weekday_ot_start_time', '18:00')
    weekday_ot_rate_multiplier = request.form.get('weekday_ot_rate_multiplier', '1.5')
    
    # การตั้งค่าโอทีช่วงดึก
    night_ot_enabled = '1' if request.form.get('night_ot_enabled') else '0'
    night_ot_rate_multiplier = request.form.get('night_ot_rate_multiplier', '2.0')
    
    # แปลง work_days เป็น string
    work_days_str = ','.join(work_days) if work_days else '1,2,3,4,5'
    
    # แปลง weekday_ot_days เป็น string
    weekday_ot_days_str = ','.join(weekday_ot_days) if weekday_ot_days else ''
    
    conn = get_db_connection()
    
    # ตรวจสอบว่ามีการตั้งค่าแล้วหรือไม่
    existing = conn.execute('SELECT id FROM work_settings WHERE user_id = ?', (user_id,)).fetchone()
    
    if existing:
        # อัพเดทการตั้งค่าที่มีอยู่
        conn.execute('''
            UPDATE work_settings 
            SET work_start_time = ?, work_end_time = ?, ot_rate = ?, work_days = ?,
                lunch_start = ?, lunch_end = ?,
                evening_break_start = ?, evening_break_end = ?,
                evening_break_ot = ?,
                saturday_ot_enabled = ?, saturday_ot_start_time = ?, saturday_ot_rate_multiplier = ?, saturday_whole_day_ot = ?,
                weekday_ot_enabled = ?, weekday_ot_days = ?, weekday_ot_start_time = ?, weekday_ot_rate_multiplier = ?,
                night_ot_enabled = ?, night_ot_rate_multiplier = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (work_start_time, work_end_time, ot_rate, work_days_str,
              lunch_start, lunch_end,
              evening_break_start, evening_break_end,
              evening_break_ot,
              saturday_ot_enabled, saturday_ot_start_time, saturday_ot_rate_multiplier, saturday_whole_day_ot,
              weekday_ot_enabled, weekday_ot_days_str, weekday_ot_start_time, weekday_ot_rate_multiplier,
              night_ot_enabled, night_ot_rate_multiplier,
              user_id))
    else:
        # สร้างการตั้งค่าใหม่
        conn.execute('''
            INSERT INTO work_settings (
                user_id, work_start_time, work_end_time, ot_rate, work_days,
                lunch_start, lunch_end,
                evening_break_start, evening_break_end,
                evening_break_ot,
                saturday_ot_enabled, saturday_ot_start_time, saturday_ot_rate_multiplier, saturday_whole_day_ot,
                weekday_ot_enabled, weekday_ot_days, weekday_ot_start_time, weekday_ot_rate_multiplier,
                night_ot_enabled, night_ot_rate_multiplier
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, work_start_time, work_end_time, ot_rate, work_days_str,
              lunch_start, lunch_end,
              evening_break_start, evening_break_end,
              evening_break_ot,
              saturday_ot_enabled, saturday_ot_start_time, saturday_ot_rate_multiplier, saturday_whole_day_ot,
              weekday_ot_enabled, weekday_ot_days_str, weekday_ot_start_time, weekday_ot_rate_multiplier,
              night_ot_enabled, night_ot_rate_multiplier))
    
    conn.commit()
    conn.close()
    
    flash('บันทึกการตั้งค่าเวลาทำงานสำเร็จ', 'success')
    return redirect('/settings')

# Update display settings
@app.route('/update-display-settings', methods=['POST'])
@login_required
def update_display_settings():
    # ในอนาคตสามารถบันทึกการตั้งค่าลงฐานข้อมูลได้
    flash('บันทึกการตั้งค่าสำเร็จ', 'success')
    return redirect('/settings')

# Export all OT data
@app.route('/export-all-ot')
@login_required
def export_all_ot():
    conn = get_db_connection()
    records = conn.execute('''
        SELECT * FROM ot_records 
        WHERE user_id = ? 
        ORDER BY work_date DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    # สร้าง CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['วันที่', 'เวลาเริ่ม', 'เวลาสิ้นสุด', 'จำนวนชั่วโมง OT'])
    
    for record in records:
        writer.writerow([
            record['work_date'],
            record['start_time'],
            record['end_time'],
            record['ot_hours']
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=all_ot_records.csv',
            'Content-Type': 'text/csv; charset=utf-8-sig'
        }
    )

# Export all income/expense data
@app.route('/export-all-income-expense')
@login_required
def export_all_income_expense():
    conn = get_db_connection()
    records = conn.execute('''
        SELECT * FROM income_expense 
        WHERE user_id = ? 
        ORDER BY date DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    # สร้าง CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['วันที่', 'ประเภท', 'หมวดหมู่หลัก', 'หมวดหมู่ย่อย', 'รายละเอียด', 'จำนวนเงิน', 'แท็ก'])
    
    for record in records:
        writer.writerow([
            record['date'],
            'รายรับ' if record['category'] == 'income' else 'รายจ่าย',
            record['main_category'],
            record['sub_category'],
            record['description'],
            record['amount'],
            record['tags']
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=all_income_expense.csv',
            'Content-Type': 'text/csv; charset=utf-8-sig'
        }
    )

# Delete account
@app.route('/delete-account')
@login_required
def delete_account():
    user_id = session['user_id']
    
    conn = get_db_connection()
    # ลบข้อมูลทั้งหมดของผู้ใช้
    conn.execute('DELETE FROM ot_records WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM income_expense WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    session.clear()
    flash('ลบบัญชีเรียบร้อยแล้ว', 'success')
    return redirect('/login')


# if __name__ == '__main__':
#     init_db()
#     app.run(host='0.0.0.0', port=5000)


if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=10000)