# Solacia 🤖💬

<p align="center">
  <img src="assets/banner.png" alt="Solacia Banner" width="600">
</p>

> An agentic AI companion that reads the room, not just the prompt.
> Silent emotion detection, adaptive empathy, mood journaling. OpenAI-compatible.

[![CI](https://github.com/iweb3insight/solacia/actions/workflows/ci.yml/badge.svg)](https://github.com/iweb3insight/solacia/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Features

- **Human-like conversations** — warm, natural, no AI vibes
- **Emotion detection** — silently detects 6 emotions (happy, sad, anxious, angry, confused, calm), adapts response style
- **Prompt diversity** — multiple style variations per emotion to avoid repetitive responses
- **Mood diary** — automatically tracks emotional patterns over time
- **OpenAI-compatible API** — works with Chatbox, NextChat, and other AI clients
- **Session memory** — remembers context within a conversation

## Quick Start

### Option 1: pip

```bash
git clone https://github.com/iweb3insight/solacia.git
cd solacia
cp .env.example .env        # Edit: add your DeepSeek API key
pip install -e ".[dev]"
python -m solacia
```

### Option 2: Docker

```bash
git clone https://github.com/iweb3insight/solacia.git
cd solacia
cp .env.example .env        # Edit: add your DeepSeek API key
docker compose up
```

Server starts at `http://localhost:8001`. API docs at `http://localhost:8001/docs`.

## Usage

### Chat with curl

```bash
# Non-streaming
curl -X POST http://localhost:8001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"solacia","messages":[{"role":"user","content":"I had a rough day..."}]}'

# Streaming
curl -X POST http://localhost:8001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"solacia","messages":[{"role":"user","content":"I had a rough day..."}],"stream":true}'
```

### Use with Chatbox

1. Download [Chatbox](https://chatboxai.app/)
2. Settings → API:
   - **API URL**: `http://localhost:8001/v1`
   - **API Key**: anything (e.g. `sk-test`)
   - **Model**: `solacia`
3. Start chatting!

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Chatbox /  │────▶│  FastAPI Server   │────▶│  DeepSeek   │
│  Any Client │◀────│  (OpenAI compat)  │◀────│  LLM API    │
└─────────────┘     └──────────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
              ┌─────▼─────┐ ┌────▼────┐
              │  Emotion   │ │  Mood   │
              │  Detector  │ │  Diary  │
              │ (keywords  │ │(SQLite) │
              │  + LLM)    │ │         │
              └───────────┘ └─────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Chat (OpenAI-compatible, streaming supported) |
| `/v1/models` | GET | List available models |
| `/v1/diary` | POST/GET | Create / list mood diary entries |
| `/v1/diary/{id}` | GET | Get a specific diary entry |
| `/v1/diary/stats/emotions` | GET | Emotion statistics |
| `/health` | GET | Health check |

Full API docs: `http://localhost:8001/docs` (Swagger UI)

## Testing

```bash
make test
```

## Project Structure

```
solacia/
├── src/solacia/
│   ├── __init__.py
│   ├── __main__.py          # python -m solacia
│   ├── config.py             # Settings from .env
│   ├── server.py             # FastAPI app
│   ├── agent/
│   │   ├── conversation.py   # Chat engine
│   │   ├── emotion.py        # Emotion detection
│   │   └── prompts.py        # Prompt templates
│   ├── api/
│   │   └── routes.py         # API endpoints
│   └── memory/
│       └── diary.py          # Mood diary (SQLite)
├── tests/                    # pytest tests
├── docs/                     # Documentation
├── pyproject.toml            # Package config
├── Dockerfile
└── docker-compose.yml
```

## License

MIT License — see [LICENSE](LICENSE) for details.
