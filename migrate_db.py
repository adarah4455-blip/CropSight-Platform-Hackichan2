import sqlite3
import os

DB_PATH = 'users.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # Check if column exists first
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        if 'google_id' not in columns:
            print("Adding 'google_id' column to 'users' table...")
            c.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column 'google_id' already exists.")
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
