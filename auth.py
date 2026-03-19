import sqlite3
import hashlib
import os
import json

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
            password TEXT,
            google_id TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS farms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            farm_name TEXT,
            latitude REAL,
            longitude REAL,
            boundary_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email) REFERENCES users (email)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            farm_name TEXT,
            health_score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email) REFERENCES users (email)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'unread',
            FOREIGN KEY (email) REFERENCES users (email)
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

def save_farm(email, farm_name, lat, lon, boundary):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    boundary_json = json.dumps(boundary)
    c.execute('''
        INSERT INTO farms (email, farm_name, latitude, longitude, boundary_json)
        VALUES (?, ?, ?, ?, ?)
    ''', (email, farm_name, lat, lon, boundary_json))
    conn.commit()
    conn.close()

def get_user_farms(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT farm_name, latitude, longitude, boundary_json, timestamp FROM farms WHERE email = ? ORDER BY timestamp DESC', (email,))
    farms = c.fetchall()
    conn.close()
    return farms

def save_analysis_record(email, farm_name, score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO analysis_history (email, farm_name, health_score)
        VALUES (?, ?, ?)
    ''', (email, farm_name, score))
    conn.commit()
    conn.close()

def get_analysis_history(email, farm_name=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if farm_name:
        c.execute('SELECT health_score, timestamp FROM analysis_history WHERE email = ? AND farm_name = ? ORDER BY timestamp ASC', (email, farm_name))
    else:
        c.execute('SELECT health_score, timestamp FROM analysis_history WHERE email = ? ORDER BY timestamp ASC', (email,))
    history = c.fetchall()
    conn.close()
    return history

def add_notification(email, message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO notifications (email, message) VALUES (?, ?)', (email, message))
    conn.commit()
    conn.close()

def get_notifications(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, message, timestamp, status FROM notifications WHERE email = ? ORDER BY timestamp DESC', (email,))
    notifs = c.fetchall()
    conn.close()
    return notifs

def mark_notif_read(notif_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE notifications SET status = "read" WHERE id = ?', (notif_id,))
    conn.commit()
    conn.close()

def login_google_user(email, google_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Check if user exists
    c.execute('SELECT email FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    if not user:
        # Create new Google user
        c.execute('INSERT INTO users (email, google_id) VALUES (?, ?)', (email, google_id))
    else:
        # Update existing user with Google ID if not present
        c.execute('UPDATE users SET google_id = ? WHERE email = ?', (google_id, email))
    conn.commit()
    conn.close()
    return True
