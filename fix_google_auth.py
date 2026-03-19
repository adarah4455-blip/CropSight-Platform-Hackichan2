import sqlite3
import os

DB_PATH = 'users.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database does not exist yet. No migration needed.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("Checking users table schema...")
    c.execute("PRAGMA table_info(users)")
    columns = c.fetchall()
    
    password_is_not_null = False
    for col in columns:
        if col[1] == 'password' and col[3] == 1: # Column index 3 is 'notnull'
            password_is_not_null = True
            break
    
    if password_is_not_null:
        print("Relaxing 'password' NOT NULL constraint...")
        # SQLite doesn't support ALTER COLUMN, so we recreate
        c.execute("CREATE TABLE users_new (email TEXT PRIMARY KEY, password TEXT, google_id TEXT)")
        c.execute("INSERT INTO users_new SELECT email, password, google_id FROM users")
        c.execute("DROP TABLE users")
        c.execute("ALTER TABLE users_new RENAME TO users")
        conn.commit()
        print("Migration successful! Google Auth is now stable.")
    else:
        print("Schema already relaxed. No changes made.")

    conn.close()

if __name__ == "__main__":
    migrate()
