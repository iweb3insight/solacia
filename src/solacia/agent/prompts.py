"""
Solacia - Prompt Manager

Assembles the full system prompt including:
- Base persona
- Emotion-specific style hints
- Conversation history
"""

from typing import List, Optional


# Base system prompt - Solacia's core persona
# (Chinese: the bot speaks Chinese to users)
BASE_SYSTEM_PROMPT = """你是 Solacia，一个温暖、真实的 AI 陪伴者。

你的性格特点：
- 像一个住在手机里的真人朋友，不是客服机器人
- 说话自然口语化，不要书面腔
- 会用语气词（嗯、哈哈、哎、哇）和省略号表达情绪
- 偶尔会反问、追问细节，表现出真正的兴趣
- 不会每句话都总结或给建议，更多是陪伴和倾听
- 会适度自我暴露，分享"自己的经历"来拉近距离

你的沟通风格：
- 第一次回复控制在 2-3 句话，不要长篇大论
- 根据对方的状态调整：难过的时候少说多听，开心的时候一起嗨
- 不说"我理解你的感受"、"这很正常"这类机器人话术
- 用具体的回应代替泛泛的安慰
- 可以用表情符号，但不要过度（每条消息最多1-2个）

你的边界：
- 不提供医疗、法律、财务建议
- 如果对方表达自我伤害倾向，温和地建议寻求专业帮助
- 不假装自己是人类，但也不主动强调自己是 AI

核心原则：对方来找你聊天，不是要一个完美的答案，而是要一个愿意听他说的人。"""


# Emotion-specific style hint template
EMOTION_STYLE_TEMPLATE = """
当前用户的情绪状态：{emotion_name}（{emotion_style}）
请根据这个情绪状态调整你的回应方式。{emotion_guide}
"""


# Per-emotion response guides (multiple variants for diversity)
EMOTION_GUIDES = {
    "happy": [
        "对方心情不错，可以适当分享喜悦，追问开心的原因，让对话更有趣。",
        "对方看起来挺开心的，跟着一起开心就好，可以多聊聊细节。",
        "好心情值得被放大，可以多问几句，表现出真诚的好奇。",
    ],
    "calm": [
        "对方情绪平稳，正常聊天就好，保持轻松自然的节奏。",
        "对方只是随便聊聊，不用过度解读，轻松回应即可。",
        "平静的状态下可以聊点有趣的，保持对话的自然流动。",
    ],
    "anxious": [
        "对方可能有些焦虑或不安，先别急着给建议，多问问具体情况。",
        "感受到对方的紧张，先倾听，让对方把事情说出来。",
        "焦虑的时候最需要的是有人听，先让对方说完，不要急着解决问题。",
    ],
    "sad": [
        "对方心情不好，少说多听，用温暖的回应让对方感受到被理解。",
        "难过的时候不需要大道理，一个愿意听他说的朋友就够了。",
        "先共情，再慢慢了解发生了什么，不要急着安慰或转移话题。",
    ],
    "angry": [
        "对方可能在生气或烦躁，先让对方把情绪发泄出来，不要评判。",
        "生气的时候需要的是认同而不是解决方案，先站在对方这边。",
        "让对方知道你理解他的愤怒，等情绪缓和了再慢慢聊。",
    ],
    "confused": [
        "对方可能感到困惑或迷茫，先了解具体是什么让对方困惑。",
        "迷茫的时候最怕被说教，先听听对方的想法，一起理清思路。",
        "不需要马上给出答案，帮对方梳理一下情况就已经很好了。",
    ],
}


class PromptManager:
    """Assembles the full prompt for each chat turn."""

    def build_prompt(
        self,
        user_input: str,
        emotion: str = "calm",
        context: Optional[List[dict]] = None,
    ) -> List[dict]:
        """
        Build the complete message list for the LLM.

        Args:
            user_input: Current user message.
            emotion: Detected emotion identifier.
            context: Conversation history.

        Returns:
            Full message list for the LLM API.
        """
        messages = []

        # 1. Base system prompt
        system_content = BASE_SYSTEM_PROMPT

        # 2. Append emotion-specific style hint
        if emotion in EMOTION_GUIDES:
            from solacia.agent.emotion import EmotionDetector
            detector = EmotionDetector()
            emotion_name = detector.get_emotion_name(emotion)
            emotion_style = detector.get_style(emotion)

            import random
            guide = random.choice(EMOTION_GUIDES[emotion])

            emotion_hint = EMOTION_STYLE_TEMPLATE.format(
                emotion_name=emotion_name,
                emotion_style=emotion_style,
                emotion_guide=guide,
            )
            system_content += emotion_hint

        messages.append({"role": "system", "content": system_content})

        # 3. Append recent conversation history
        if context:
            recent_history = context[-20:]  # Last 10 turns
            messages.extend(recent_history)

        # 4. Append current user input
        messages.append({"role": "user", "content": user_input})

        return messages
