"""Order lookup, chat logging, and analytics — backed by a small SQLite
database. This is what turns the bot from 'canned responses' into
something that actually looks up real (seeded) data."""

import os
import re
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chatbot_data.db")
DB_PATH = os.path.abspath(DB_PATH)

# Matches order IDs like ORD1001, ord2044, etc.
ORDER_ID_PATTERN = re.compile(r"\bORD\d{3,6}\b", re.IGNORECASE)

SEED_ORDERS = [
    ("ORD1001", "Wireless Mouse", "Shipped", "2026-08-05"),
    ("ORD1002", "Mechanical Keyboard", "Delivered", "2026-07-28"),
    ("ORD1003", "USB-C Hub", "Processing", "2026-08-10"),
    ("ORD1004", "Laptop Stand", "Cancelled", "2026-07-15"),
    ("ORD1005", "Noise Cancelling Headphones", "Delivered", "2026-07-20"),
    ("ORD1006", "Webcam 1080p", "Shipped", "2026-08-08"),
    ("ORD1007", "External SSD 1TB", "Processing", "2026-08-11"),
    ("ORD1008", "Monitor 27-inch", "Delivered", "2026-07-02"),
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist yet, and seed sample orders once."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            item TEXT NOT NULL,
            status TEXT NOT NULL,
            order_date TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            message TEXT,
            tag TEXT,
            confidence REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("SELECT COUNT(*) FROM orders")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO orders (order_id, item, status, order_date) VALUES (?, ?, ?, ?)",
            SEED_ORDERS,
        )
    conn.commit()
    conn.close()


def extract_order_id(message: str):
    """Pull an order ID like 'ORD1002' out of free text, if present."""
    match = ORDER_ID_PATTERN.search(message or "")
    return match.group(0).upper() if match else None


def lookup_order(order_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE order_id = ?", (order_id.upper(),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def log_message(session_id: str, message: str, tag: str, confidence: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chat_logs (session_id, message, tag, confidence) VALUES (?, ?, ?, ?)",
        (session_id, message, tag, confidence),
    )
    conn.commit()
    conn.close()


def get_analytics():
    """Aggregate stats over logged conversations — total messages, unique
    sessions, and a breakdown of how often each intent was matched."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM chat_logs")
    total_messages = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(DISTINCT session_id) AS total FROM chat_logs")
    total_sessions = cur.fetchone()["total"]

    cur.execute("""
        SELECT tag, COUNT(*) AS count
        FROM chat_logs
        GROUP BY tag
        ORDER BY count DESC
    """)
    intent_breakdown = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {
        "total_messages": total_messages,
        "total_sessions": total_sessions,
        "intent_breakdown": intent_breakdown,
    }
