"""
Solacia - Emotion Detector

Silently detects user emotion using keyword matching (fast path)
and LLM fallback (slow path).
"""

from typing import Optional
from openai import OpenAI
from solacia.config import settings


# Emotion type definitions
# name/style are runtime data for the Chinese-speaking bot persona
EMOTIONS = {
    "happy": {
        "name": "开心",
        "style": "共享喜悦",
        "keywords": ["哈哈", "太好了", "开心", "高兴", "爽", "棒", "好耶", "嘻嘻"]
    },
    "calm": {
        "name": "平静",
        "style": "日常聊天",
        "keywords": ["嗯", "还好", "一般", "正常"]
    },
    "anxious": {
        "name": "焦虑",
        "style": "轻声安抚",
        "keywords": ["紧张", "担心", "焦虑", "睡不着", "压力", "害怕", "不安"]
    },
    "sad": {
        "name": "悲伤",
        "style": "温暖陪伴",
        "keywords": ["难受", "难过", "伤心", "哭", "委屈", "失落", "低落"]
    },
    "angry": {
        "name": "愤怒",
        "style": "倾听理解",
        "keywords": ["生气", "气死", "烦死", "讨厌", "烦", "操", "靠", "妈的"]
    },
    "confused": {
        "name": "困惑",
        "style": "耐心解释",
        "keywords": ["不知道", "迷茫", "怎么办", "搞不懂", "不理解"]
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
        prompt = f"""请识别以下文本的情绪，只返回情绪标识，不要返回其他内容。

情绪类型：
- happy: 开心、高兴、兴奋
- calm: 平静、正常、一般
- anxious: 焦虑、紧张、担心
- sad: 悲伤、难过、失落
- angry: 愤怒、生气、烦躁
- confused: 困惑、迷茫、不确定

文本：{text}

情绪标识："""

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
        return "日常聊天"

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
        return "平静"
