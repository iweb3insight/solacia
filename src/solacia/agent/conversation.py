"""
Solacia - Conversation Engine

Manages chat flow, calls LLM, generates responses.
Session history is stored in memory (resets on restart).
"""

import logging
from typing import List

from openai import OpenAI, AsyncOpenAI

from solacia.config import settings
from solacia.agent.emotion import EmotionDetector
from solacia.agent.prompts import PromptManager

logger = logging.getLogger(__name__)


class ConversationEngine:
    """Manages conversation for a single user session."""

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.async_client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.emotion_detector = EmotionDetector()
        self.prompt_manager = PromptManager()
        self.history: List[dict] = []  # In-memory conversation history

    def chat(self, user_input: str) -> str:
        """
        Process user input and generate a response (sync).

        Args:
            user_input: User's message text.

        Returns:
            Assistant's reply text.
        """
        # Detect emotion
        emotion = self.emotion_detector.detect(user_input)

        # Build full prompt
        full_messages = self.prompt_manager.build_prompt(
            user_input=user_input,
            emotion=emotion,
            context=self.history,
        )

        # Call LLM
        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=full_messages,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            reply = response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            reply = "Sorry, I got distracted for a moment. Could you say that again?"

        # Save to in-memory history
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": reply})

        # Trim history to max length
        max_messages = settings.MAX_HISTORY_MESSAGES * 2  # user + assistant
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

        return reply

    async def achat(self, user_input: str) -> str:
        """
        Process user input and generate a response (async).

        Args:
            user_input: User's message text.

        Returns:
            Assistant's reply text.
        """
        emotion = self.emotion_detector.detect(user_input)

        full_messages = self.prompt_manager.build_prompt(
            user_input=user_input,
            emotion=emotion,
            context=self.history,
        )

        try:
            response = await self.async_client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=full_messages,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            reply = response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            reply = "Sorry, I got distracted for a moment. Could you say that again?"

        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": reply})

        max_messages = settings.MAX_HISTORY_MESSAGES * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

        return reply

    async def achat_stream(self, user_input: str):
        """
        Process user input and stream the response (async).

        Args:
            user_input: User's message text.

        Yields:
            Response text chunks.
        """
        emotion = self.emotion_detector.detect(user_input)

        full_messages = self.prompt_manager.build_prompt(
            user_input=user_input,
            emotion=emotion,
            context=self.history,
        )

        collected_chunks = []
        collected_content = []

        try:
            stream = await self.async_client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=full_messages,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                stream=True,
            )

            async for chunk in stream:
                collected_chunks.append(chunk)
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    collected_content.append(content)
                    yield content

        except Exception as e:
            logger.error(f"LLM streaming call failed: {e}")
            yield "Sorry, I got distracted for a moment. Could you say that again?"
            return

        # Save full response to history
        full_reply = "".join(collected_content)
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": full_reply})

        max_messages = settings.MAX_HISTORY_MESSAGES * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]
