import uuid

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from chatbot import ChatbotEngine, orders_db, session_store

app = Flask(__name__)
CORS(app)

orders_db.init_db()
engine = ChatbotEngine()


def _order_lookup_response(order_id: str, tag: str) -> str:
    order = orders_db.lookup_order(order_id)
    if not order:
        return f"I couldn't find an order with ID {order_id}. Could you double-check it?"

    if tag == "order_status":
        return f"Order {order['order_id']} ({order['item']}) is currently: {order['status']}."
    if tag == "refund":
        return (f"Got it — I've started a refund request for order {order['order_id']} "
                f"({order['item']}). You'll get a confirmation email shortly.")
    if tag == "cancel_order":
        if order["status"] in ("Shipped", "Delivered"):
            return (f"Order {order['order_id']} has already {order['status'].lower()}, "
                    f"so it can't be cancelled — but I can start a return instead if you'd like.")
        return f"Order {order['order_id']} ({order['item']}) has been cancelled."
    return f"Order {order['order_id']}: {order['item']} — {order['status']}."


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not message.strip():
        return jsonify({"error": "No input provided."}), 400

    order_id = orders_db.extract_order_id(message)
    pending_tag = session_store.get_pending_intent(session_id)

    if pending_tag:
        if order_id:
            order = orders_db.lookup_order(order_id)
            if order:
                # Valid ID — resolve using the remembered intent and forget the pending state.
                session_store.clear_pending_intent(session_id)
                result = {"response": _order_lookup_response(order_id, pending_tag), "tag": pending_tag, "confidence": 1.0}
            else:
                # Wrong/unknown ID — stay in the pending state so they can retry,
                # instead of silently forgetting what we were waiting for.
                result = {
                    "response": f"I couldn't find an order with ID {order_id}. Could you double-check it?",
                    "tag": pending_tag,
                    "confidence": 1.0,
                }
        else:
            # No ID in this message. Let an explicit "talk to a human" request
            # escape the pending flow instead of trapping the user in a loop.
            classification = engine.get_response(message)
            if classification["tag"] == "human_agent":
                session_store.clear_pending_intent(session_id)
                result = classification
            else:
                result = {
                    "response": "I'm still waiting on that order ID — it should look like ORD1234.",
                    "tag": pending_tag,
                    "confidence": 1.0,
                }

    else:
        result = engine.get_response(message)

        if result["tag"] in ("order_status", "refund", "cancel_order"):
            if order_id:
                # ID was given in the same message — resolve immediately.
                result["response"] = _order_lookup_response(order_id, result["tag"])
            else:
                # No ID yet — remember we're waiting on one for this session.
                session_store.set_pending_intent(session_id, result["tag"])
        elif result["tag"] == "fallback" and order_id:
            # The message didn't clearly match any intent, but it does
            # contain a valid order ID out of the blue (no prior prompt for
            # one). The most reasonable assumption for a bare order number
            # is "what's the status of this?" — so default to that instead
            # of a generic "I don't understand."
            result = {"response": _order_lookup_response(order_id, "order_status"), "tag": "order_status", "confidence": 1.0}

    orders_db.log_message(session_id, message, result["tag"], result.get("confidence", 0.0))
    result["session_id"] = session_id
    return jsonify(result)


@app.route("/analytics")
def analytics():
    return jsonify(orders_db.get_analytics())


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)