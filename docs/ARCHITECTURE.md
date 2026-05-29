# Architecture

## Overview

ToC Companion is a modular monolith with three core components:

1. **Conversation Engine** — manages chat flow, assembles prompts, calls LLM
2. **Emotion Detector** — two-tier detection (keywords → LLM fallback)
3. **Mood Diary** — SQLite-backed mood tracking and statistics

## Data Flow

```
User Input
    │
    ▼
Emotion Detection (keywords → LLM)
    │
    ▼
Prompt Assembly (base + emotion style + history)
    │
    ▼
LLM Call (DeepSeek / any OpenAI-compatible API)
    │
    ▼
Response + Save to History
```

## Key Design Decisions

- **Two-tier emotion detection**: Keywords for speed (<1ms), LLM for accuracy on ambiguous input
- **Session-only memory**: Chat history stored in memory, resets on restart
- **OpenAI-compatible API**: Drop-in replacement for Chatbox, NextChat, and other clients
- **SQLite for diary**: Zero-config, single-file persistence for mood tracking
- **Prompt diversity**: Multiple style variations per emotion to avoid repetition

## Tech Stack

- **Runtime**: Python 3.10+
- **Framework**: FastAPI
- **LLM**: DeepSeek API (OpenAI-compatible)
- **Database**: SQLite 3 (stdlib)
- **Testing**: pytest + httpx
