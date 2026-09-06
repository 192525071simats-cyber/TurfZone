import sqlite3

conn = sqlite3.connect('turfzone.db')
cursor = conn.cursor()

# Check if addons column exists in bookings
cols = [c[1] for c in cursor.execute("PRAGMA table_info(bookings)").fetchall()]
if 'addons' not in cols:
    print("Adding 'addons' column to bookings table in turfzone.db...")
    cursor.execute("ALTER TABLE bookings ADD COLUMN addons TEXT")
    conn.commit()
    print("✓ Successfully added 'addons' column!")
else:
    print("Column 'addons' already exists.")

conn.close()
