"""Sentiment labels used by the review response and face images."""
from functools import lru_cache

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


@lru_cache(maxsize=1024)
def review_sentiment(text):
    score = _analyzer.polarity_scores(text or "")["compound"]
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"
