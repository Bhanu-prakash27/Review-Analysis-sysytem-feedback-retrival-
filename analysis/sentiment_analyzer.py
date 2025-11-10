# analysis/sentiment_analyzer.py
import nltk
from textblob import TextBlob
import re

# Make sure NLTK has stopwords
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class SentimentAnalyzer:
    """Simple sentiment and aspect-based analyzer using TextBlob"""

    def analyze_sentiment(self, text: str):
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        sentiment = "neutral"
        if polarity > 0.1:
            sentiment = "positive"
        elif polarity < -0.1:
            sentiment = "negative"

        words = text.lower().split()
        positive_words = [w for w in words if w in ["good", "great", "excellent", "amazing", "love"]]
        negative_words = [w for w in words if w in ["bad", "poor", "terrible", "hate", "awful"]]

        return {
            "sentiment": sentiment,
            "sentiment_score": round(polarity, 3),
            "positive_words": ", ".join(positive_words),
            "negative_words": ", ".join(negative_words),
        }

    def analyze_aspects(self, text: str):
        """Extract simple aspects from keywords"""
        aspects = {}
        aspect_keywords = {
            "battery": ["battery", "charge", "power"],
            "camera": ["camera", "photo", "picture"],
            "performance": ["speed", "performance", "fast", "lag"],
            "display": ["screen", "display", "resolution"],
            "sound": ["audio", "sound", "speaker"],
        }

        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        for aspect, keywords in aspect_keywords.items():
            if any(k in text.lower() for k in keywords):
                aspects[aspect] = {
                    "score": round(polarity, 3),
                    "mentions": [k for k in keywords if k in text.lower()]
                }

        return aspects


class FakeReviewDetector:
    """Very simple fake review detection"""
    
    def detect_fake(self, text: str, rating: float, review_length: int):
        suspicious = False
        reason = ""

        # Heuristic rules
        if review_length < 10:
            suspicious = True
            reason = "Review too short"
        elif review_length > 500:
            suspicious = True
            reason = "Review unusually long"
        elif rating in [1, 5] and ("!!!" in text or "!!!" in text):
            suspicious = True
            reason = "Extreme rating with suspicious text"

        return {
            "is_fake": suspicious,
            "label": reason if reason else "Looks genuine"
        }
