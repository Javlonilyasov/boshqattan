import sqlite3

DB_NAME = "messages.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            message_id INTEGER,
            text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_message(user_id, username, message_id, text):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, username, message_id, text) VALUES (?, ?, ?, ?)",
              (user_id, username, message_id, text))
    conn.commit()
    conn.close()

def get_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT user_id, username FROM messages ORDER BY created_at DESC LIMIT 50")
    users = c.fetchall()
    conn.close()
    return users

def get_user_id_by_username(username: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id FROM messages WHERE username = ? ORDER BY created_at DESC LIMIT 1", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_all_user_ids():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT user_id FROM messages")
    ids = [row[0] for row in c.fetchall()]
    conn.close()
    return ids
