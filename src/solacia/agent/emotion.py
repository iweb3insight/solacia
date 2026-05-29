"""
Solacia - Emotion Detector

Silently detects user emotion using keyword matching (fast path)
and LLM fallback (slow path).
"""

import logging
from typing import Optional
from openai import OpenAI
from solacia.config import settings

logger = logging.getLogger(__name__)


# Emotion type definitions
EMOTIONS = {
    "happy": {
        "name": "joyful",
        "style": "share the excitement",
        "keywords": ["haha", "great", "awesome", "amazing", "yay", "happy", "excited", "wonderful", "love it", "lol"]
    },
    "calm": {
        "name": "calm",
        "style": "casual chat",
        "keywords": ["fine", "okay", "alright", "normal", "meh", "not bad"]
    },
    "anxious": {
        "name": "anxious",
        "style": "gentle reassurance",
        "keywords": ["nervous", "worried", "anxious", "can't sleep", "stress", "stressed", "scared", "uneasy", "overthinking"]
    },
    "sad": {
        "name": "sad",
        "style": "warm companionship",
        "keywords": ["sad", "hurts", "crying", "upset", "lonely", "down", "depressed", "heartbroken", "miss"]
    },
    "angry": {
        "name": "angry",
        "style": "listen without judgment",
        "keywords": ["angry", "furious", "hate", "annoyed", "frustrated", "frustrating", "pissed", "unfair", "ridiculous"]
    },
    "confused": {
        "name": "confused",
        "style": "patient guidance",
        "keywords": ["confused", "lost", "don't understand", "what should", "no idea", "torn", "uncertain"]
    }
}


class EmotionDetector:
    """Detects user emotion silently (no explicit questioning)."""

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )

    def detect(self, text: str) -> str:
        """
        Detect emotion from user input text.

        Args:
            text: User input text.

        Returns:
            Emotion identifier (happy/calm/anxious/sad/angry/confused).
        """
        # Fast path: keyword matching
        keyword_emotion = self._detect_by_keywords(text)
        if keyword_emotion:
            return keyword_emotion

        # Slow path: LLM-based detection
        return self._detect_by_llm(text)

    def _detect_by_keywords(self, text: str) -> Optional[str]:
        """
        Match emotion via keyword scoring.

        Args:
            text: User input text.

        Returns:
            Emotion identifier or None if no keywords matched.
        """
        text_lower = text.lower()

        scores = {}
        for emotion_id, emotion_info in EMOTIONS.items():
            score = sum(1 for kw in emotion_info["keywords"] if kw in text_lower)
            if score > 0:
                scores[emotion_id] = score

        if scores:
            return max(scores, key=scores.get)

        return None

    def _detect_by_llm(self, text: str) -> str:
        """
        Detect emotion via LLM call.

        Args:
            text: User input text.

        Returns:
            Emotion identifier (defaults to "calm" on failure).
        """
        prompt = f"""Identify the emotion in the following text. Return ONLY the emotion label, nothing else.

Emotion types:
- happy: joy, excitement, elation
- calm: neutral, normal, relaxed
- anxious: worry, stress, nervousness
- sad: sadness, grief, loneliness
- angry: anger, frustration, irritation
- confused: confusion, uncertainty, indecision

Text: {text}

Emotion label:"""

        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=10
            )

            emotion = response.choices[0].message.content.strip().lower()

            if emotion in EMOTIONS:
                return emotion

            return "calm"

        except Exception:
            logger.warning("Emotion detection via LLM failed, defaulting to 'calm'", exc_info=True)
            return "calm"

    def get_style(self, emotion: str) -> str:
        """
        Get the response style for a given emotion.

        Args:
            emotion: Emotion identifier.

        Returns:
            Response style description.
        """
        if emotion in EMOTIONS:
            return EMOTIONS[emotion]["style"]
        return "casual chat"

    def get_emotion_name(self, emotion: str) -> str:
        """
        Get the display name for a given emotion.

        Args:
            emotion: Emotion identifier.

        Returns:
            Emotion display name.
        """
        if emotion in EMOTIONS:
            return EMOTIONS[emotion]["name"]
        return "calm"
