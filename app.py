from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
import sqlite3
from datetime import datetime, time
import pandas as pd
import io
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
DB_FILE = 'ot.db'
app.secret_key = 'your_secret_key_change_this_in_production'

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
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร', 'error')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('รหัสผ่านไม่ตรงกัน', 'error')
            return render_template('signup.html')
        
        # ตรวจสอบว่า email ซ้ำหรือไม่
        conn = get_db_connection()
        existing_user = conn.execute(
            'SELECT id FROM users WHERE email = ?', (email,)
        ).fetchone()
        
        if existing_user:
            flash('Email นี้ถูกใช้งานแล้ว', 'error')
            conn.close()
            return render_template('signup.html')
        
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
    
    return render_template('signup.html')

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

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('ออกจากระบบสำเร็จ', 'success')
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
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )
                 ''')
    
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
    conn.commit()
    conn.close()


def calculate_ot(start_str, end_str, user_id):
    start = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
    end = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")
    date_str = start.strftime("%Y-%m-%d")

    # ❌ ไม่คิด OT วันอาทิตย์
    if start.weekday() == 6:
        return 0.0

    breaks = []
    if is_holiday(date_str, user_id):
        breaks = [(12, 0, 13, 0)]
    elif start.weekday() == 5:  # เสาร์
        if start.time() < time(13, 0):
            start = datetime.combine(start.date(), time(13, 0))
        breaks = [(12, 0, 13, 0), (17, 0, 17, 30)]
    else:
        if start.time() < time(17, 30):
            start = datetime.combine(start.date(), time(17, 30))
        breaks = [(12, 0, 13, 0)]

    total_seconds = (end - start).total_seconds()

    for bh, bm, eh, em in breaks:
        brk_start = datetime.combine(start.date(), time(bh, bm))
        brk_end = datetime.combine(start.date(), time(eh, em))
        overlap_start = max(start, brk_start)
        overlap_end = min(end, brk_end)
        if overlap_start < overlap_end:
            total_seconds -= (overlap_end - overlap_start).total_seconds()

    return round(max(total_seconds / 3600, 0), 2)


@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    conn = get_db_connection()
    user_id = session['user_id']
    
    if request.method == 'POST':
        work_date = request.form['work_date']
        end_time = request.form['end_time']
        start_time = f"{work_date}T08:00"
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
                         available_months=selectable_months)


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
        transaction_type = request.form.get('transaction_type')
        category = request.form['category']
        items_data = request.form.get('items_data')  # JSON string จาก JavaScript
        description = request.form.get('description')  # รายการสินค้าที่สร้างอัตโนมัติ
        amount = float(request.form['amount'])
        vendor = request.form.get('vendor') or None

        print("=== DEBUG: Parsed Data ===")
        print("Date:", date)
        print("Transaction Type:", transaction_type)
        print("Category:", category)
        print("Items Data:", items_data)
        print("Description:", description)
        print("Amount:", amount)
        print("Vendor:", vendor)

        # ตรวจสอบประเภทรายการ
        if transaction_type == 'income':
            # สำหรับรายรับ
            if not description:
                description = f"รายรับ: {category}"
            conn.execute('''
                         INSERT INTO income_expense (user_id, date, description, amount, category, vendor)
                         VALUES (?, ?, ?, ?, ?, ?)
                         ''', (user_id, date, description, amount, 'income', vendor))
        else:
            # สำหรับรายจ่าย
            if not items_data or not description:
                flash('กรุณาเลือกรายการสินค้า', 'error')
                return redirect('/income-expense')

            conn.execute('''
                         INSERT INTO income_expense (user_id, date, description, amount, category, vendor)
                         VALUES (?, ?, ?, ?, ?, ?)
                         ''', (user_id, date, description, amount, 'expense', vendor))

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

        conn.execute('''
                     UPDATE income_expense
                     SET date=?,
                         description=?,
                         amount=?,
                         category=?,
                         vendor=?
                     WHERE id = ? AND user_id = ?
                     ''', (date, description, amount, category, vendor, id, user_id))  # ✅ ครบ 7 ค่า
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


# if __name__ == '__main__':
#     init_db()
#     app.run(host='0.0.0.0', port=5000)


if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=10000)