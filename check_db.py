import sqlite3
import os

DB_PATH = 'users.db'

def check_schema():
    if not os.path.exists(DB_PATH):
        print("Database does not exist.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    columns = c.fetchall()
    conn.close()
    
    print("Columns in 'users' table:")
    for col in columns:
        print(col)

if __name__ == "__main__":
    check_schema()
