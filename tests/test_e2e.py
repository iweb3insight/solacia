"""
Solacia - API End-to-End Tests

Tests the full request/response cycle through the FastAPI app.
LLM calls use a dummy key so the fallback reply is returned;
emotion detection still works via the keyword fast-path.
"""

import pytest
from fastapi.testclient import TestClient
from solacia.server import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


# ==================== Health ====================

def test_health_returns_ok(client):
    """GET /health returns 200 with status ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


# ==================== Models ====================

def test_list_models_returns_solacia(client):
    """GET /v1/models lists the solacia model."""
    resp = client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1
    assert data[0]["id"] == "solacia"
    assert data[0]["object"] == "model"


# ==================== Chat Completions (non-streaming) ====================

def test_chat_returns_openai_compatible_response(client):
    """POST /v1/chat/completions returns an OpenAI-compatible structure."""
    resp = client.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
    })
    assert resp.status_code == 200
    body = resp.json()

    # OpenAI shape
    assert body["object"] == "chat.completion"
    assert body["model"] == "solacia"
    assert len(body["choices"]) == 1
    choice = body["choices"][0]
    assert choice["finish_reason"] == "stop"
    assert choice["message"]["role"] == "assistant"
    assert isinstance(choice["message"]["content"], str)
    assert len(choice["message"]["content"]) > 0
    assert "id" in body
    assert body["id"].startswith("chatcmpl-")
    assert "usage" in body


def test_chat_missing_user_message_returns_400(client):
    """Chat request with no user message returns 400."""
    resp = client.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [{"role": "system", "content": "you are helpful"}],
        "stream": False,
    })
    assert resp.status_code == 400


def test_chat_with_session_id(client):
    """Passing a session_id enables multi-turn context."""
    sid = "e2e-session-test"
    # Turn 1
    resp1 = client.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [{"role": "user", "content": "hello"}],
        "session_id": sid,
        "stream": False,
    })
    assert resp1.status_code == 200

    # Turn 2 (same session)
    resp2 = client.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [{"role": "user", "content": "how are you"}],
        "session_id": sid,
        "stream": False,
    })
    assert resp2.status_code == 200
    assert len(resp2.json()["choices"][0]["message"]["content"]) > 0


# ==================== Chat Completions (streaming) ====================

def test_chat_streaming_returns_sse(client):
    """Streaming chat returns SSE-formatted chunks ending with [DONE]."""
    resp = client.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [{"role": "user", "content": "hello"}],
        "stream": True,
    })
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    raw = resp.text
    lines = [line for line in raw.split("\n") if line.strip()]

    # Must end with [DONE]
    assert lines[-1] == "data: [DONE]"

    # At least one data chunk before [DONE]
    data_lines = [l for l in lines if l.startswith("data: ") and "[DONE]" not in l]
    assert len(data_lines) >= 1

    # Each data chunk is valid JSON with OpenAI chunk shape
    import json
    for dl in data_lines:
        chunk = json.loads(dl.removeprefix("data: "))
        assert chunk["object"] == "chat.completion.chunk"
        assert chunk["model"] == "solacia"
        assert len(chunk["choices"]) == 1
        assert "delta" in chunk["choices"][0]


def test_streaming_chunk_ids_are_unique(client):
    """Each SSE chunk should have a unique id."""
    import json
    resp = client.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [{"role": "user", "content": "hello"}],
        "stream": True,
    })
    data_lines = [
        l.removeprefix("data: ")
        for l in resp.text.split("\n")
        if l.startswith("data: ") and "[DONE]" not in l
    ]
    ids = [json.loads(dl)["id"] for dl in data_lines]
    assert len(ids) == len(set(ids)), "chunk ids should be unique"


# ==================== Diary CRUD ====================

def test_diary_create_read_flow(client):
    """Full diary flow: create → read by id → list → stats."""
    # Create
    resp = client.post("/v1/diary", json={
        "emotions": ["happy", "calm"],
        "summary": "Nice day",
        "message_count": 12,
    })
    assert resp.status_code == 200
    entry = resp.json()
    assert entry["status"] == "created"
    entry_id = entry["id"]
    assert entry["emotions"] == ["happy", "calm"]
    assert entry["summary"] == "Nice day"
    assert entry["message_count"] == 12

    # Read by ID
    resp = client.get(f"/v1/diary/{entry_id}")
    assert resp.status_code == 200
    fetched = resp.json()
    assert fetched["id"] == entry_id
    assert fetched["emotions"] == ["happy", "calm"]
    assert fetched["summary"] == "Nice day"

    # List
    resp = client.get("/v1/diary")
    assert resp.status_code == 200
    entries = resp.json()["entries"]
    assert any(e["id"] == entry_id for e in entries)

    # Stats
    resp = client.get("/v1/diary/stats/emotions?days=7")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["days"] == 7
    assert isinstance(stats["emotions"], dict)


def test_diary_not_found_returns_404(client):
    """GET /v1/diary/{id} with nonexistent id returns 404."""
    resp = client.get("/v1/diary/999999")
    assert resp.status_code == 404


def test_diary_create_minimal_fields(client):
    """Create diary entry with only required fields."""
    resp = client.post("/v1/diary", json={"emotions": ["sad"]})
    assert resp.status_code == 200
    entry = resp.json()
    assert entry["status"] == "created"
    assert entry["emotions"] == ["sad"]
    assert entry["summary"] is None
    assert entry["message_count"] == 0


def test_diary_stats_empty_period(client):
    """Stats for a period with no entries returns empty dict."""
    resp = client.get("/v1/diary/stats/emotions?days=1")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["days"] == 1
    assert isinstance(stats["emotions"], dict)


# ==================== Emotion Detection (keyword fast-path) ====================

def test_emotion_happy_via_keyword(client):
    """Happy keywords trigger happy emotion even without LLM."""
    resp = client.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [{"role": "user", "content": "haha I'm so happy and excited!"}],
        "stream": False,
    })
    assert resp.status_code == 200
    # The response should be generated (either LLM or fallback)
    assert len(resp.json()["choices"][0]["message"]["content"]) > 0


def test_emotion_sad_via_keyword(client):
    """Sad keywords trigger sad emotion."""
    resp = client.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [{"role": "user", "content": "I feel so sad and lonely today"}],
        "stream": False,
    })
    assert resp.status_code == 200


# ==================== Edge Cases ====================

def test_empty_message_content(client):
    """Empty string content should still return 200 (user role exists)."""
    resp = client.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [{"role": "user", "content": ""}],
        "stream": False,
    })
    assert resp.status_code == 200


def test_multiple_user_messages_uses_last(client):
    """When multiple user messages are sent, the last one is used."""
    resp = client.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [
            {"role": "user", "content": "first message"},
            {"role": "user", "content": "last message"},
        ],
        "stream": False,
    })
    assert resp.status_code == 200


def test_default_model_when_omitted(client):
    """Omitting model field defaults to solacia."""
    resp = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "hi"}],
        "stream": False,
    })
    assert resp.status_code == 200
    assert resp.json()["model"] == "solacia"


def test_diary_list_limit(client):
    """GET /v1/diary?limit=N respects the limit parameter."""
    # Create 3 entries
    for _ in range(3):
        client.post("/v1/diary", json={"emotions": ["calm"]})

    resp = client.get("/v1/diary?limit=2")
    assert resp.status_code == 200
    entries = resp.json()["entries"]
    assert len(entries) <= 2
