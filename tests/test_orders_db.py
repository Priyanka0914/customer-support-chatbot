import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot import orders_db


def setup_module(module):
    # Point the DB module at a throwaway temp file so these tests never
    # touch (or depend on) the real chatbot_data.db used by the app.
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    orders_db.DB_PATH = path
    orders_db.init_db()


def test_seed_orders_are_present():
    order = orders_db.lookup_order("ORD1001")
    assert order is not None
    assert order["item"] == "Wireless Mouse"


def test_lookup_unknown_order_returns_none():
    assert orders_db.lookup_order("ORD9999") is None


def test_lookup_is_case_insensitive():
    assert orders_db.lookup_order("ord1002") is not None


def test_extract_order_id_basic():
    assert orders_db.extract_order_id("What's the status of ORD1003?") == "ORD1003"


def test_extract_order_id_lowercase():
    assert orders_db.extract_order_id("check ord1004 please") == "ORD1004"


def test_extract_order_id_with_punctuation():
    assert orders_db.extract_order_id("order: ORD1005!!") == "ORD1005"


def test_extract_order_id_returns_none_when_absent():
    assert orders_db.extract_order_id("where is my order") is None


def test_extract_order_id_ignores_plain_numbers():
    # A bare number shouldn't be mistaken for an order ID — only the
    # ORD-prefixed pattern should match.
    assert orders_db.extract_order_id("I ordered 3 items on the 15th") is None


def test_log_message_and_analytics():
    orders_db.log_message("test-session-1", "hello", "greeting", 0.9)
    orders_db.log_message("test-session-1", "bye", "goodbye", 0.8)
    orders_db.log_message("test-session-2", "hi", "greeting", 0.95)

    stats = orders_db.get_analytics()
    assert stats["total_messages"] >= 3
    assert stats["total_sessions"] >= 2
    tags = [row["tag"] for row in stats["intent_breakdown"]]
    assert "greeting" in tags
