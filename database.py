import sqlite3
from datetime import datetime

DB_NAME = "leads.db"


def connect():
    return sqlite3.connect(DB_NAME)


def setup_database():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            username TEXT,
            first_name TEXT,
            assigned_ib TEXT,
            assigned_ib_username TEXT,
            joined_at TEXT,
            clicked INTEGER DEFAULT 0,
            reminder_sent INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute("""
CREATE TABLE IF NOT EXISTS ibs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    active INTEGER DEFAULT 1
)
""")

    conn.commit()
    conn.close()


def create_lead(telegram_id, username, first_name, assigned_ib, assigned_ib_username):
    conn = connect()
    cursor = conn.cursor()

    joined_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO leads (
            telegram_id, username, first_name, assigned_ib,
            assigned_ib_username, joined_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (telegram_id, username, first_name, assigned_ib, assigned_ib_username, joined_at))

    lead_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return lead_id


def get_lead(lead_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    lead = cursor.fetchone()

    conn.close()
    return lead


def mark_clicked(lead_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("UPDATE leads SET clicked = 1 WHERE id = ?", (lead_id,))

    conn.commit()
    conn.close()


def mark_reminder_sent(lead_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("UPDATE leads SET reminder_sent = 1 WHERE id = ?", (lead_id,))

    conn.commit()
    conn.close()


def get_setting(key, default="0"):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return row[0]

    return default


def set_setting(key, value):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value)
        VALUES (?, ?)
    """, (key, value))

    conn.commit()
    conn.close()
    
def get_total_leads():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]

    conn.close()
    return total


def get_leads_by_ib():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT assigned_ib_username, COUNT(*)
        FROM leads
        GROUP BY assigned_ib_username
        ORDER BY COUNT(*) DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_clicked_leads():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM leads WHERE clicked = 1")
    clicked = cursor.fetchone()[0]

    conn.close()
    return clicked
def get_dashboard_stats():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE clicked = 1")
    clicked = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM leads
        WHERE DATE(joined_at) = DATE('now')
    """)
    today = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM leads
        WHERE joined_at >= DATETIME('now', '-7 days')
    """)
    week = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM leads
        WHERE joined_at >= DATETIME('now', '-30 days')
    """)
    month = cursor.fetchone()[0]

    cursor.execute("""
        SELECT assigned_ib_username, COUNT(*)
        FROM leads
        GROUP BY assigned_ib_username
        ORDER BY COUNT(*) DESC
        LIMIT 3
    """)
    top_ibs = cursor.fetchall()

    conn.close()

    return {
        "total": total,
        "clicked": clicked,
        "today": today,
        "week": week,
        "month": month,
        "top_ibs": top_ibs,
    }
    
def save_dashboard_message(chat_id, topic_id, message_id):
    set_setting("dashboard_chat_id", str(chat_id))
    set_setting("dashboard_topic_id", str(topic_id))
    set_setting("dashboard_message_id", str(message_id))


def get_dashboard_message():
    chat_id = get_setting("dashboard_chat_id", None)
    topic_id = get_setting("dashboard_topic_id", None)
    message_id = get_setting("dashboard_message_id", None)

    if not chat_id or not topic_id or not message_id:
        return None

    return {
        "chat_id": int(chat_id),
        "topic_id": int(topic_id),
        "message_id": int(message_id),
    }
def set_setting(key, value):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value)
        VALUES (?, ?)
    """, (key, str(value)))

    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return row[0]

    return default
    
def get_latest_lead_by_telegram_id(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM leads
        WHERE telegram_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (telegram_id,))

    lead = cursor.fetchone()

    conn.close()
    return lead
    
def add_ib(name, username):
    username = username.replace("@", "")

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO ibs (name, username, active)
        VALUES (?, ?, 1)
    """, (name, username))

    conn.commit()
    conn.close()


def remove_ib(username):
    username = username.replace("@", "")

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("UPDATE ibs SET active = 0 WHERE username = ?", (username,))

    conn.commit()
    conn.close()


def get_active_ibs():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, username
        FROM ibs
        WHERE active = 1
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [{"name": row[0], "username": row[1]} for row in rows]