import sqlite3
import os

def check_schema():
    db_path = 'users.db'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    columns = c.fetchall()
    print("Column Info (id, name, type, notnull, dflt_value, pk):")
    for col in columns:
        print(col)
    conn.close()

if __name__ == "__main__":
    check_schema()
