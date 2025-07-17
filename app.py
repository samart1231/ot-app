from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import sqlite3
from datetime import datetime, time
import pandas as pd
import io

app = Flask(__name__)
DB_FILE = 'ot.db'
app.secret_key = 'your_secret_key'

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # ตัวอย่างการตรวจสอบผู้ใช้
        if username == 'March1123' and password == '9586awdxQW../43':
            flash('Login successful!', 'success')
            return redirect(url_for('index'))  # เปลี่ยนไปยังหน้า index
        else:
            flash('Invalid credentials. Please try again.', 'error')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    return "Welcome to the Dashboard!"

@app.route('/')
def home():
    return redirect(url_for('login'))


def is_holiday(date_str):
    conn = get_db_connection()
    result = conn.execute('SELECT 1 FROM holidays WHERE date = ?', (date_str,)).fetchone()
    conn.close()
    return result is not None


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS ot_records
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     work_date
                     TEXT,
                     start_time
                     TEXT,
                     end_time
                     TEXT,
                     ot_hours
                     REAL
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
                     date
                     TEXT,
                     description
                     TEXT,
                     amount
                     REAL,
                     category
                     TEXT
                 )
                 ''')
    # ✅ แก้ตรงนี้: เพิ่ม note
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS holidays
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     date
                     TEXT
                     UNIQUE,
                     note
                     TEXT
                 )
                 ''')
    conn.commit()
    conn.close()


def calculate_ot(start_str, end_str):
    start = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
    end = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")
    date_str = start.strftime("%Y-%m-%d")

    # ❌ ไม่คิด OT วันอาทิตย์
    if start.weekday() == 6:
        return 0.0

    breaks = []
    if is_holiday(date_str):
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
def index():
    conn = get_db_connection()
    if request.method == 'POST':
        work_date = request.form['work_date']
        end_time = request.form['end_time']
        start_time = f"{work_date}T08:00"
        ot_hours = calculate_ot(start_time, end_time)
        conn.execute('INSERT INTO ot_records (work_date, start_time, end_time, ot_hours) VALUES (?, ?, ?, ?)',
                     (work_date, start_time, end_time, ot_hours))
        conn.commit()
        return redirect(url_for('index'))

    # รับเดือนที่เลือก หรือใช้เดือนปัจจุบันเป็นค่าเริ่มต้น
    from datetime import datetime
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    sort_order = request.args.get('sort', 'desc')
    order_sql = 'ORDER BY work_date DESC' if sort_order == 'desc' else 'ORDER BY work_date ASC'
    
    # กรองข้อมูลตามเดือนที่เลือก
    month_filter = f"WHERE strftime('%Y-%m', work_date) = ?"
    
    # นับจำนวนรายการในเดือนที่เลือก
    total_records = conn.execute(f'SELECT COUNT(*) FROM ot_records {month_filter}', (selected_month,)).fetchone()[0]
    
    # ดึงข้อมูลทั้งหมดสำหรับเดือนที่เลือก (ไม่มี pagination)
    records = conn.execute(f'SELECT * FROM ot_records {month_filter} {order_sql}', 
                          (selected_month,)).fetchall()
    
    # คำนวณ OT รวมสำหรับเดือนที่เลือก
    monthly_total_ot = conn.execute(f'SELECT SUM(ot_hours) FROM ot_records {month_filter}', (selected_month,)).fetchone()[0] or 0
    
    # ดึงรายการเดือนทั้งหมดที่มีข้อมูล
    available_months = conn.execute('''
                                   SELECT DISTINCT strftime('%Y-%m', work_date) AS month
                                   FROM ot_records
                                   ORDER BY month DESC
                                   ''').fetchall()
    
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
                              GROUP BY month
                              ORDER BY month DESC
                              ''').fetchall()
    
    # คำนวณ OT รวมทั้งหมด
    total_ot = conn.execute('SELECT SUM(ot_hours) FROM ot_records').fetchone()[0] or 0
    
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
def edit_ot(id):
    conn = get_db_connection()
    if request.method == 'POST':
        work_date = request.form['work_date']
        end_time = request.form['end_time']
        start_time = f"{work_date}T08:00"
        ot_hours = calculate_ot(start_time, end_time)
        conn.execute('''
                     UPDATE ot_records
                     SET work_date=?,
                         start_time=?,
                         end_time=?,
                         ot_hours=?
                     WHERE id = ?
                     ''', (work_date, start_time, end_time, ot_hours, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    record = conn.execute('SELECT * FROM ot_records WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('edit_ot.html', record=record)


@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM ot_records WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/income-expense', methods=['GET', 'POST'])
def income_expense():
    conn = get_db_connection()
    if request.method == 'POST':
        date = request.form['date']
        category = request.form['category']
        items_data = request.form.get('items_data')  # JSON string จาก JavaScript
        description = request.form.get('description')  # รายการสินค้าที่สร้างอัตโนมัติ
        amount = float(request.form['amount'])
        vendor = request.form.get('vendor') or None

        # ตรวจสอบว่ามีข้อมูลรายการสินค้าหรือไม่
        if not items_data or not description:
            flash('กรุณาเลือกรายการสินค้า', 'error')
            return redirect('/income-expense')

        # บันทึกลงฐานข้อมูล
        conn.execute('''
                     INSERT INTO income_expense (date, description, amount, category, vendor)
                     VALUES (?, ?, ?, ?, ?)
                     ''', (date, description, amount, 'expense', vendor))  # กำหนดเป็น expense
        conn.commit()
        flash('บันทึกข้อมูลเรียบร้อยแล้ว', 'success')
        return redirect('/income-expense')

    # รับเดือนที่เลือก หรือใช้เดือนปัจจุบันเป็นค่าเริ่มต้น
    from datetime import datetime
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    sort_order = request.args.get('sort', 'desc')
    order_sql = 'ORDER BY date DESC' if sort_order == 'desc' else 'ORDER BY date ASC'
    
    # กรองข้อมูลตามเดือนที่เลือก
    month_filter = f"WHERE strftime('%Y-%m', date) = ?"
    
    # นับจำนวนรายการในเดือนที่เลือก
    total_records = conn.execute(f'SELECT COUNT(*) FROM income_expense {month_filter}', (selected_month,)).fetchone()[0]
    
    # ดึงข้อมูลทั้งหมดสำหรับเดือนที่เลือก (ไม่มี pagination)
    records = conn.execute(f'SELECT * FROM income_expense {month_filter} {order_sql}', 
                          (selected_month,)).fetchall()
    
    # คำนวณยอดรวมสำหรับเดือนที่เลือก
    monthly_total_income = conn.execute(f'SELECT SUM(amount) FROM income_expense {month_filter} AND category="income"', (selected_month,)).fetchone()[0] or 0
    monthly_total_expense = conn.execute(f'SELECT SUM(amount) FROM income_expense {month_filter} AND category="expense"', (selected_month,)).fetchone()[0] or 0
    
    # ดึงรายการเดือนทั้งหมดที่มีข้อมูล
    available_months = conn.execute('''
                                   SELECT DISTINCT strftime('%Y-%m', date) AS month
                                   FROM income_expense
                                   ORDER BY month DESC
                                   ''').fetchall()
    
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
    total_income = conn.execute('SELECT SUM(amount) FROM income_expense WHERE category="income"').fetchone()[0] or 0
    total_expense = conn.execute('SELECT SUM(amount) FROM income_expense WHERE category="expense"').fetchone()[0] or 0
    
    # ดึงข้อมูลสำหรับตารางสรุปรายเดือน (แสดงทุกเดือน)
    monthly_summary = conn.execute('''
                                   SELECT strftime('%Y-%m', date) AS month, category, SUM(amount) AS total
                                   FROM income_expense
                                   GROUP BY month, category
                                   ORDER BY month DESC
                                   ''').fetchall()
    
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
def edit_income_expense(id):
    conn = get_db_connection()
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
                     WHERE id = ?
                     ''', (date, description, amount, category, vendor, id))  # ✅ ครบ 6 ค่า
        conn.commit()
        conn.close()
        return redirect('/income-expense')

    record = conn.execute('SELECT * FROM income_expense WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('edit_income_expense.html', record=record)


@app.route('/delete-income-expense/<int:id>', methods=['POST'])
def delete_income_expense(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM income_expense WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/income-expense')


@app.route('/export-<category>/<year_month>')
def export_income_expense_month(category, year_month):
    conn = get_db_connection()
    if category == 'all':
        df = pd.read_sql_query('''
                               SELECT *
                               FROM income_expense
                               WHERE strftime('%Y-%m', date) = ?
                               ORDER BY date ASC
                               ''', conn, params=(year_month,))
        filename = f"income_expense_{year_month}.csv"
    else:
        df = pd.read_sql_query('''
                               SELECT *
                               FROM income_expense
                               WHERE strftime('%Y-%m', date) = ?
                                 AND category = ?
                               ORDER BY date ASC
                               ''', conn, params=(year_month, category))
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
def export_year_ot(year):
    conn = get_db_connection()
    df = pd.read_sql_query('''
                           SELECT *
                           FROM ot_records
                           WHERE strftime('%Y', work_date) = ?
                           ORDER BY work_date ASC
                           ''', conn, params=(year,))
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
def export_month_csv(year_month):
    conn = get_db_connection()
    df = pd.read_sql_query('''
                           SELECT *
                           FROM ot_records
                           WHERE strftime('%Y-%m', work_date) = ?
                           ORDER BY work_date ASC
                           ''', conn, params=(year_month,))
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
def month_view(year_month):
    conn = get_db_connection()
    records = conn.execute('''
                           SELECT *
                           FROM ot_records
                           WHERE strftime('%Y-%m', work_date) = ?
                           ORDER BY work_date ASC
                           ''', (year_month,)).fetchall()
    total = sum(row['ot_hours'] for row in records)
    conn.close()
    return render_template('month.html', records=records, month=year_month, total=round(total, 2))


@app.route('/income-expense/month/<year_month>')
def income_expense_month_view(year_month):
    conn = get_db_connection()
    records = conn.execute('''
                           SELECT *
                           FROM income_expense
                           WHERE strftime('%Y-%m', date) = ?
                           ORDER BY date DESC
                           ''', (year_month,)).fetchall()
    conn.close()

    return render_template('income_expense_month.html', records=records, year_month=year_month)


@app.route('/delete-income-expense/<int:id>', methods=['POST'])
def delete_income_expense_month(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM income_expense WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer or '/income-expense')  # กลับไปหน้าก่อนหน้า


from datetime import datetime


@app.route('/holidays', methods=['GET', 'POST'])
def manage_holidays():
    conn = get_db_connection()

    if request.method == 'POST':
        date = request.form['date']
        note = request.form['note']
        conn.execute('INSERT INTO holidays (date, note) VALUES (?, ?)', (date, note))
        conn.commit()
        return redirect('/holidays')

    # 🟡 Filter ปีจาก query parameter เช่น ?year=2025
    year = request.args.get('year', datetime.now().year)
    holidays = conn.execute('''
                            SELECT *
                            FROM holidays
                            WHERE strftime('%Y', date) = ?
                            ORDER BY date DESC
                            ''', (str(year),)).fetchall()
    conn.close()
    return render_template('holidays.html', holidays=holidays, selected_year=year)


@app.route('/delete-holiday/<int:id>', methods=['POST'])
def delete_holiday(id):
    print(f"กำลังลบ holiday id={id}")
    conn = get_db_connection()
    conn.execute('DELETE FROM holidays WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/holidays')


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)