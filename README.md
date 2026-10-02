# Customer Support Chatbot

A customer support chatbot built with Flask, scikit-learn, and SQLite. It
classifies messages into one of 18 support intents using TF-IDF + cosine
similarity, remembers context across turns (e.g. "what's my order status?"
→ "ORD1002"), looks up real order data from a seeded database, and logs
every conversation for basic analytics.

Includes a browser chat widget so it's demoable, not just testable via curl.

## What makes this more than a canned-response bot

- **Real order lookups.** `order_status`, `refund`, and `cancel_order`
  intents extract an order ID (pattern: `ORD1234`) from the message and
  query a seeded SQLite database — including business logic like refusing
  to cancel an order that's already shipped.
- **Multi-turn context.** If you ask about an order without giving an ID,
  the bot remembers it asked and resolves your next message (just the ID)
  in that context, instead of reclassifying it from scratch.
- **Conversation logging + analytics.** Every message is logged with its
  session, matched intent, and confidence. `GET /analytics` returns
  aggregate stats (total messages, unique sessions, intent breakdown).
- **A confidence threshold.** Low-similarity matches return an honest
  "I didn't understand that" instead of a confident wrong guess.

## Project structure

```
customer-support-chatbot/
├── app.py                  # Flask routes + order-lookup / session logic
├── chatbot/
│   ├── __init__.py
│   ├── engine.py            # TF-IDF + cosine similarity intent matching
│   ├── intents.json         # Training data — 18 intents, edit freely
│   ├── orders_db.py         # SQLite: orders table, chat logs, analytics
│   └── session_store.py     # In-memory multi-turn context tracking
├── templates/
│   └── index.html           # Chat widget page
├── static/
│   ├── style.css
│   └── script.js             # Persists session_id via localStorage
├── tests/
│   ├── test_engine.py        # 26 tests — one per intent + edge cases
│   ├── test_orders_db.py     # DB seeding, lookup, ID extraction, logging
│   └── test_api.py           # Full Flask API tests incl. multi-turn flow
├── requirements.txt
└── README.md
```

## Setup (VS Code / local machine)

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Open **http://127.0.0.1:5000** in your browser. Try:
1. "where is my order" → bot asks for an order ID
2. "ORD1002" → bot looks it up and replies with the real status

Sample seeded order IDs: `ORD1001` through `ORD1008` (see `chatbot/orders_db.py`
for the full list and statuses).

## API

**POST** `/chat`
```json
{ "message": "where is my order", "session_id": "optional-uuid" }
```
```json
{
  "response": "Sure, could you share your order ID so I can check that for you? It looks like ORD1234.",
  "tag": "order_status",
  "confidence": 1.0,
  "session_id": "generated-if-you-didn't-send-one"
}
```
Send the same `session_id` on your next request for multi-turn context to work.

**GET** `/analytics` — aggregate conversation stats.
**GET** `/health` — `{ "status": "ok" }`.

## Running tests

```bash
pytest tests/ -v
```
44 tests: one classification check per intent, edge cases (empty input,
gibberish, punctuation, case sensitivity, long messages), full DB behavior,
and full API behavior including the multi-turn order-lookup flow.

## Adding new intents

Edit `chatbot/intents.json` — add a `tag`, a few example `patterns`, and
some `responses`. No code changes needed; the model retrains from this
file on the next app start.

## Known limitations (and what to build next)

- **Session store is in-memory** (`chatbot/session_store.py`) — fine for a
  single dev-server process, but not shared across multiple workers/processes.
  A production version would back this with Redis or a database table.
- **No authentication** — anyone can look up any order ID if they guess it.
  A real system would tie orders to a logged-in customer.
- **TF-IDF + cosine similarity**, not embeddings/an LLM — works well for a
  small, well-separated intent set like this, but won't scale gracefully
  to hundreds of overlapping intents. A natural upgrade path is swapping
  in `sentence-transformers` for semantic matching.
- **SQLite** is fine for a demo; a real deployment would use Postgres/MySQL.

## Pushing to your own GitHub repo

```bash
git init
git add .
git commit -m "Initial commit: customer support chatbot"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```
