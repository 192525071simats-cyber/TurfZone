import sqlite3

conn = sqlite3.connect('turfzone.db')
cursor = conn.cursor()

tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    table_name = t[0]
    cols = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    print(table_name, ":", [c[1] for c in cols])

conn.close()
