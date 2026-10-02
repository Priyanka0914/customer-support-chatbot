import json
import os
import random

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Minimum cosine similarity to the closest training example before we trust
# a match. Below this, we admit we don't know rather than guessing.
SIMILARITY_THRESHOLD = 0.30
FALLBACK_RESPONSE = "I'm sorry, I didn't quite understand that. Could you rephrase, or type 'agent' to talk to a human?"

ORDER_AWARE_TAGS = {"order_status", "refund", "cancel_order"}


class ChatbotEngine:
    """Small retrieval-based chatbot: TF-IDF vectorizes every example phrase
    in intents.json once at startup. An incoming message is matched against
    all example phrases by cosine similarity, and the tag of the closest
    match is used — provided it's similar enough. This is far more reliable
    than a probabilistic classifier when the training set is this small."""

    def __init__(self, intents_path=None):
        if intents_path is None:
            intents_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intents.json")

        with open(intents_path, "r", encoding="utf-8") as f:
            self.intents = json.load(f)["intents"]

        self.responses = {}
        self.pattern_tags = []
        patterns = []
        for intent in self.intents:
            self.responses[intent["tag"]] = intent["responses"]
            for pattern in intent["patterns"]:
                patterns.append(pattern)
                self.pattern_tags.append(intent["tag"])

        self.vectorizer = TfidfVectorizer(lowercase=True)
        self.pattern_vectors = self.vectorizer.fit_transform(patterns)

    def classify(self, message: str) -> dict:
        """Return the best-matching tag + confidence, with no side effects
        (no DB lookups, no session mutation) — kept separate from
        get_response so it's easy to unit test in isolation."""
        if not message or not message.strip():
            return {"tag": None, "confidence": 0.0}

        vect = self.vectorizer.transform([message])
        similarities = cosine_similarity(vect, self.pattern_vectors)[0]
        best_idx = similarities.argmax()
        confidence = float(similarities[best_idx])
        tag = self.pattern_tags[best_idx]

        if confidence < SIMILARITY_THRESHOLD:
            return {"tag": "fallback", "confidence": round(confidence, 3)}

        return {"tag": tag, "confidence": round(confidence, 3)}

    def get_response(self, message: str) -> dict:
        """Standalone response (no order lookup / session context). Used
        directly by tests and by app.py for any tag that isn't order-aware."""
        classification = self.classify(message)
        tag = classification["tag"]

        if tag is None:
            return {"response": "Could you tell me a bit more about what you need?", "tag": None, "confidence": 0.0}
        if tag == "fallback":
            return {"response": FALLBACK_RESPONSE, "tag": "fallback", "confidence": classification["confidence"]}

        return {
            "response": random.choice(self.responses[tag]),
            "tag": tag,
            "confidence": classification["confidence"],
        }
