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
