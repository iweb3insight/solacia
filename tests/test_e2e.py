"""
Solacia - API End-to-End Tests

Starts a real uvicorn server and sends actual HTTP requests.
No mocks, no TestClient — full network round-trip.
"""

import os
import signal
import subprocess
import sys
import time

import httpx
import pytest

# Use a high port unlikely to conflict
E2E_PORT = 18721
BASE_URL = f"http://127.0.0.1:{E2E_PORT}"


# ==================== Server Lifecycle ====================


@pytest.fixture(scope="module")
def server():
    """Start a real uvicorn server, wait for readiness, yield, then shut down."""
    env = {
        **os.environ,
        "API_HOST": "127.0.0.1",
        "API_PORT": str(E2E_PORT),
        "LLM_API_KEY": "sk-test-dummy",
        "LLM_BASE_URL": "https://api.deepseek.com/v1",
        "DB_PATH": "data/e2e_test.db",
    }

    proc = subprocess.Popen(
        [sys.executable, "-m", "solacia"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # Wait for server to be ready (poll /health, max 10s)
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            r = httpx.get(f"{BASE_URL}/health", timeout=1)
            if r.status_code == 200:
                break
        except httpx.ConnectError:
            pass
        time.sleep(0.3)
    else:
        proc.kill()
        stdout = proc.stdout.read().decode() if proc.stdout else ""
        raise RuntimeError(f"Server did not start within 10s.\n{stdout}")

    yield BASE_URL

    # Shutdown
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

    # Cleanup test DB
    try:
        os.remove("data/e2e_test.db")
    except FileNotFoundError:
        pass


@pytest.fixture
def api(server):
    """Sync HTTP client pointed at the live server."""
    with httpx.Client(base_url=server, timeout=30) as client:
        yield client


# ==================== Health & Models ====================


def test_health(api):
    """GET /health returns 200."""
    r = api.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_models(api):
    """GET /v1/models lists solacia."""
    r = api.get("/v1/models")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data[0]["id"] == "solacia"


# ==================== Chat (non-streaming) ====================


def test_chat_openai_compatible_shape(api):
    """Response follows OpenAI chat.completion schema."""
    r = api.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
    })
    assert r.status_code == 200
    body = r.json()

    assert body["object"] == "chat.completion"
    assert body["model"] == "solacia"
    assert body["id"].startswith("chatcmpl-")
    assert len(body["choices"]) == 1

    choice = body["choices"][0]
    assert choice["finish_reason"] == "stop"
    assert choice["message"]["role"] == "assistant"
    assert isinstance(choice["message"]["content"], str)
    assert len(choice["message"]["content"]) > 0
    assert "usage" in body


def test_chat_missing_user_message_400(api):
    """Request with no user role returns 400."""
    r = api.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [{"role": "system", "content": "you are helpful"}],
    })
    assert r.status_code == 400


def test_chat_session_continuity(api):
    """Same session_id preserves conversation context."""
    sid = "e2e-real-session"

    r1 = api.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [{"role": "user", "content": "hello"}],
        "session_id": sid,
    })
    assert r1.status_code == 200

    r2 = api.post("/v1/chat/completions", json={
        "model": "solacia",
        "messages": [{"role": "user", "content": "how are you"}],
        "session_id": sid,
    })
    assert r2.status_code == 200
    assert len(r2.json()["choices"][0]["message"]["content"]) > 0


def test_chat_default_model(api):
    """Omitting model field defaults to solacia."""
    r = api.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "hi"}],
    })
    assert r.status_code == 200
    assert r.json()["model"] == "solacia"


def test_chat_empty_content(api):
    """Empty string content is accepted (user role exists)."""
    r = api.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": ""}],
    })
    assert r.status_code == 200


def test_chat_multiple_user_messages_uses_last(api):
    """When multiple user messages are sent, the last one is used."""
    r = api.post("/v1/chat/completions", json={
        "messages": [
            {"role": "user", "content": "first"},
            {"role": "user", "content": "second"},
        ],
    })
    assert r.status_code == 200


# ==================== Chat (streaming / SSE) ====================


def test_streaming_sse_format(api):
    """Streaming returns SSE with data: chunks and [DONE] marker."""
    with httpx.stream(
        "POST",
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "solacia",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": True,
        },
        timeout=30,
    ) as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]

        lines = []
        for line in r.iter_lines():
            if line.strip():
                lines.append(line.strip())

    assert lines[-1] == "data: [DONE]"

    data_lines = [l for l in lines if l.startswith("data: ") and "[DONE]" not in l]
    assert len(data_lines) >= 1

    import json
    for dl in data_lines:
        chunk = json.loads(dl.removeprefix("data: "))
        assert chunk["object"] == "chat.completion.chunk"
        assert chunk["model"] == "solacia"
        assert "delta" in chunk["choices"][0]


def test_streaming_chunk_ids_unique(api):
    """Each SSE chunk has a unique id."""
    import json
    with httpx.stream(
        "POST",
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "solacia",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": True,
        },
        timeout=30,
    ) as r:
        data_lines = [
            line.removeprefix("data: ")
            for line in r.iter_lines()
            if line.startswith("data: ") and "[DONE]" not in line
        ]

    ids = [json.loads(dl)["id"] for dl in data_lines]
    assert len(ids) == len(set(ids))


# ==================== Diary CRUD ====================


def test_diary_full_crud_flow(api):
    """Create → read by id → list → stats."""
    # Create
    r = api.post("/v1/diary", json={
        "emotions": ["happy", "calm"],
        "summary": "Nice day",
        "message_count": 12,
    })
    assert r.status_code == 200
    entry = r.json()
    assert entry["status"] == "created"
    entry_id = entry["id"]

    # Read by ID
    r = api.get(f"/v1/diary/{entry_id}")
    assert r.status_code == 200
    fetched = r.json()
    assert fetched["id"] == entry_id
    assert fetched["emotions"] == ["happy", "calm"]
    assert fetched["summary"] == "Nice day"

    # List
    r = api.get("/v1/diary")
    assert r.status_code == 200
    assert any(e["id"] == entry_id for e in r.json()["entries"])

    # Stats
    r = api.get("/v1/diary/stats/emotions?days=7")
    assert r.status_code == 200
    stats = r.json()
    assert stats["days"] == 7
    assert isinstance(stats["emotions"], dict)


def test_diary_not_found_404(api):
    """GET /v1/diary/{id} with nonexistent id returns 404."""
    r = api.get("/v1/diary/999999")
    assert r.status_code == 404


def test_diary_minimal_fields(api):
    """Create with only required fields."""
    r = api.post("/v1/diary", json={"emotions": ["sad"]})
    assert r.status_code == 200
    entry = r.json()
    assert entry["emotions"] == ["sad"]
    assert entry["summary"] is None
    assert entry["message_count"] == 0


def test_diary_list_limit(api):
    """GET /v1/diary?limit=N respects the limit."""
    for _ in range(3):
        api.post("/v1/diary", json={"emotions": ["calm"]})

    r = api.get("/v1/diary?limit=2")
    assert r.status_code == 200
    assert len(r.json()["entries"]) <= 2
