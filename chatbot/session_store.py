"""Tiny in-memory store for tracking multi-turn context — e.g. 'the bot
just asked this session for an order ID, and is waiting for the reply.'

This is intentionally simple (a plain dict) and NOT persistent or
multi-process safe. That's fine for a single dev-server demo; a real
deployment running multiple workers would back this with Redis or a
database table instead, so all workers share the same session state.
"""

_pending_context = {}


def get_pending_intent(session_id: str):
    return _pending_context.get(session_id)


def set_pending_intent(session_id: str, tag: str):
    _pending_context[session_id] = tag


def clear_pending_intent(session_id: str):
    _pending_context.pop(session_id, None)
