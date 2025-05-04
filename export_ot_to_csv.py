import sqlite3
import pandas as pd

# เชื่อมต่อฐานข้อมูล
conn = sqlite3.connect("ot.db")

# ดึงข้อมูลจากตาราง OT
df = pd.read_sql_query("SELECT * FROM ot_records", conn)

# บันทึกเป็น CSV
df.to_csv("ot_records.csv", index=False, encoding="utf-8-sig")  # ใส่ utf-8-sig เพื่อให้ Excel อ่านไทยได้

print("✅ ส่งออก ot_records.csv สำเร็จแล้ว!")
