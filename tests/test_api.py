import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Point the DB at a temp file BEFORE importing app, so these tests never
# touch the real chatbot_data.db.
from chatbot import orders_db
fd, _tmp_db_path = tempfile.mkstemp(suffix=".db")
os.close(fd)
orders_db.DB_PATH = _tmp_db_path

import app as app_module  # noqa: E402

app_module.app.testing = True
client = app_module.app.test_client()


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_index_page_loads():
    res = client.get("/")
    assert res.status_code == 200
    assert b"Customer Support" in res.data


def test_chat_missing_message_returns_400():
    res = client.post("/chat", json={})
    assert res.status_code == 400


def test_chat_greeting_returns_response_and_session_id():
    res = client.post("/chat", json={"message": "Hi there"})
    body = res.get_json()
    assert res.status_code == 200
    assert body["tag"] == "greeting"
    assert "session_id" in body


def test_chat_order_status_with_id_in_same_message():
    res = client.post("/chat", json={"message": "Where is order ORD1001?"})
    body = res.get_json()
    assert body["tag"] == "order_status"
    assert "Shipped" in body["response"]


def test_chat_order_status_unknown_id():
    res = client.post("/chat", json={"message": "Status of ORD9999 please"})
    body = res.get_json()
    assert "couldn't find" in body["response"]


def test_multi_turn_order_lookup_flow():
    """The core 'project-like' behavior: ask about an order without an ID,
    get asked to provide one, then reply with just the ID and have the bot
    remember what it was waiting for."""
    session_id = "multi-turn-test-session"

    first = client.post("/chat", json={"message": "where is my order", "session_id": session_id})
    first_body = first.get_json()
    assert first_body["tag"] == "order_status"
    assert "order ID" in first_body["response"] or "order id" in first_body["response"].lower()

    second = client.post("/chat", json={"message": "ORD1002", "session_id": session_id})
    second_body = second.get_json()
    assert second_body["tag"] == "order_status"
    assert "Delivered" in second_body["response"]


def test_multi_turn_refund_flow_unknown_order():
    session_id = "multi-turn-refund-session"

    client.post("/chat", json={"message": "I want a refund", "session_id": session_id})
    second = client.post("/chat", json={"message": "ORD8888", "session_id": session_id})
    body = second.get_json()
    assert "couldn't find" in body["response"]


def test_analytics_endpoint_structure():
    client.post("/chat", json={"message": "Hello"})
    res = client.get("/analytics")
    body = res.get_json()
    assert res.status_code == 200
    assert "total_messages" in body
    assert "total_sessions" in body
    assert "intent_breakdown" in body
    assert isinstance(body["intent_breakdown"], list)
