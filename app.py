from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
from datetime import datetime, time
import pandas as pd
import io

app = Flask(__name__)
DB_FILE = 'ot.db'

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
        CREATE TABLE IF NOT EXISTS ot_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_date TEXT,
            start_time TEXT,
            end_time TEXT,
            ot_hours REAL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS income_expense (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            amount REAL,
            category TEXT
        )
    ''')
    # ✅ แก้ตรงนี้: เพิ่ม note
    conn.execute('''
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            note TEXT
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


@app.route('/', methods=['GET', 'POST'])
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
        return redirect('/')

    sort_order = request.args.get('sort', 'desc')
    order_sql = 'ORDER BY work_date DESC' if sort_order == 'desc' else 'ORDER BY work_date ASC'
    records = conn.execute(f'SELECT * FROM ot_records {order_sql}').fetchall()
    total_ot = conn.execute('SELECT SUM(ot_hours) FROM ot_records').fetchone()[0] or 0

    monthly_ot = conn.execute('''
        SELECT strftime('%Y-%m', work_date) AS month, SUM(ot_hours) AS total
        FROM ot_records
        GROUP BY month
        ORDER BY month DESC
    ''').fetchall()
    conn.close()
    return render_template('index.html', records=records, total_ot=round(total_ot, 2),
                           sort_order=sort_order, monthly_ot=monthly_ot)

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
                     SET work_date=?, start_time=?, end_time=?, ot_hours=?
                     WHERE id = ?
                     ''', (work_date, start_time, end_time, ot_hours, id))
        conn.commit()
        conn.close()
        return redirect('/')
    record = conn.execute('SELECT * FROM ot_records WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('edit_ot.html', record=record)


@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM ot_records WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/income-expense', methods=['GET', 'POST'])
def income_expense():
    conn = get_db_connection()
    if request.method == 'POST':
        date = request.form['date']
        description = request.form['description']
        vendor = request.form.get('vendor') or None
        amount = float(request.form['amount'])
        category = request.form['category']
        conn.execute('''
                     INSERT INTO income_expense (date, description, amount, category, vendor)
                     VALUES (?, ?, ?, ?, ?)
                     ''', (date, description, amount, category, vendor))
        conn.commit()
        return redirect('/income-expense')

    records = conn.execute('SELECT * FROM income_expense ORDER BY date DESC').fetchall()
    total_income = conn.execute('SELECT SUM(amount) FROM income_expense WHERE category="income"').fetchone()[0] or 0
    total_expense = conn.execute('SELECT SUM(amount) FROM income_expense WHERE category="expense"').fetchone()[0] or 0
    monthly_summary = conn.execute('''
        SELECT strftime('%Y-%m', date) AS month, category, SUM(amount) AS total
        FROM income_expense
        GROUP BY month, category
        ORDER BY month DESC
    ''').fetchall()
    conn.close()
    return render_template('income_expense.html', records=records,
                           total_income=total_income, total_expense=total_expense,
                           monthly_summary=monthly_summary)

@app.route('/edit-income-expense/<int:id>', methods=['GET', 'POST'])
def edit_income_expense(id):
    conn = get_db_connection()
    if request.method == 'POST':
        date = request.form['date']
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        conn.execute('''
            UPDATE income_expense SET date=?, description=?, amount=?, category=? WHERE id=?
        ''', (date, description, amount, category, id))
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
            SELECT * FROM income_expense
            WHERE strftime('%Y-%m', date) = ?
            ORDER BY date ASC
        ''', conn, params=(year_month,))
        filename = f"income_expense_{year_month}.csv"
    else:
        df = pd.read_sql_query('''
            SELECT * FROM income_expense
            WHERE strftime('%Y-%m', date) = ? AND category = ?
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
        SELECT * FROM ot_records
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
        SELECT * FROM ot_records
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
        SELECT * FROM ot_records
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
        SELECT * FROM income_expense
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
        SELECT * FROM holidays
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
