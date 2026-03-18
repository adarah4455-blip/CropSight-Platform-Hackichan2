import sqlite3
import hashlib
import os

DB_PATH = 'users.db'

def _hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return f"{salt}:{hashed}"

def _verify_password(stored_password, provided_password):
    salt, hashed = stored_password.split(':')
    return stored_password == _hash_password(provided_password, salt)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def create_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        hashed_pw = _hash_password(password)
        c.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    if user and _verify_password(user[0], password):
        return True
    return False
