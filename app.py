from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, time

HOLIDAYS = ["2025-05-01", "2025-05-06"]

app = Flask(__name__)
DB_FILE = 'ot.db'

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
    conn.commit()
    conn.close()

def calculate_ot(start_str, end_str):
    start = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
    end = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")
    if start.strftime("%Y-%m-%d") in HOLIDAYS:
        return round((end - start).total_seconds() / 3600, 2)
    base_time = time(13, 0) if start.weekday() == 5 else time(17, 30)
    if start.time() < base_time:
        start = start.replace(hour=base_time.hour, minute=base_time.minute)
    return round(max((end - start).total_seconds() / 3600, 0), 2)

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
def edit(id):
    conn = get_db_connection()
    if request.method == 'POST':
        work_date = request.form['work_date']
        end_time = request.form['end_time']
        start_time = f"{work_date}T08:00"
        ot_hours = calculate_ot(start_time, end_time)

        conn.execute('UPDATE ot_records SET work_date=?, start_time=?, end_time=?, ot_hours=? WHERE id=?',
                     (work_date, start_time, end_time, ot_hours, id))
        conn.commit()
        conn.close()
        return redirect('/')
    
    record = conn.execute('SELECT * FROM ot_records WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('edit.html', record=record)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
