import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot import ChatbotEngine

engine = ChatbotEngine()


# --- One sanity check per intent (18 total) ---

def test_greeting():
    assert engine.get_response("Hello there")["tag"] == "greeting"


def test_goodbye():
    assert engine.get_response("bye for now")["tag"] == "goodbye"


def test_thanks():
    assert engine.get_response("Thanks so much")["tag"] == "thanks"


def test_order_status():
    assert engine.get_response("Where is my package")["tag"] == "order_status"


def test_refund():
    assert engine.get_response("I want a refund for my order")["tag"] == "refund"


def test_cancel_order():
    assert engine.get_response("Please cancel my purchase")["tag"] == "cancel_order"


def test_shipping_info():
    assert engine.get_response("How long does shipping take")["tag"] == "shipping_info"


def test_change_address():
    assert engine.get_response("I need to change my shipping address")["tag"] == "change_address"


def test_payment_issue():
    assert engine.get_response("I was charged twice")["tag"] == "payment_issue"


def test_account_login():
    assert engine.get_response("I forgot my password")["tag"] == "account_login"


def test_product_availability():
    assert engine.get_response("Is this item in stock")["tag"] == "product_availability"


def test_warranty():
    assert engine.get_response("Does this come with a warranty")["tag"] == "warranty"


def test_technical_issue():
    assert engine.get_response("The website isn't working")["tag"] == "technical_issue"


def test_hours():
    assert engine.get_response("What are your business hours")["tag"] == "hours"


def test_pricing():
    assert engine.get_response("What's the price")["tag"] == "pricing"


def test_human_agent():
    assert engine.get_response("I want to talk to a human")["tag"] == "human_agent"


def test_complaint():
    assert engine.get_response("I want to file a complaint")["tag"] == "complaint"


def test_feedback():
    assert engine.get_response("I have a suggestion")["tag"] == "feedback"


# --- Edge cases ---

def test_empty_message_handled():
    result = engine.get_response("")
    assert result["tag"] is None


def test_whitespace_only_message_handled():
    result = engine.get_response("     ")
    assert result["tag"] is None


def test_gibberish_triggers_fallback():
    result = engine.get_response("asdkjh qlwkejh zxpoiuqwe")
    assert result["tag"] == "fallback"


def test_case_insensitivity():
    lower = engine.get_response("hello there")
    upper = engine.get_response("HELLO THERE")
    assert lower["tag"] == upper["tag"] == "greeting"


def test_punctuation_does_not_break_matching():
    result = engine.get_response("Hi!!! Can you help me???")
    assert result["tag"] == "greeting"


def test_long_rambling_message_still_classifies():
    msg = ("So basically I ordered this thing like two weeks ago and I still "
           "have no idea where it is, can you please just tell me where my order is")
    result = engine.get_response(msg)
    assert result["tag"] == "order_status"


def test_fallback_confidence_is_low():
    result = engine.get_response("purple elephant quantum sandwich")
    assert result["confidence"] < 0.30


def test_matched_intent_has_response_text():
    result = engine.get_response("Hi")
    assert isinstance(result["response"], str) and len(result["response"]) > 0
