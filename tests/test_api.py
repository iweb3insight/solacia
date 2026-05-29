"""
Solacia - API Tests
"""

import pytest
from fastapi.testclient import TestClient

from solacia.agent.emotion import EMOTIONS, EmotionDetector
from solacia.server import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def emotion_detector():
    """Create an emotion detector instance."""
    return EmotionDetector()


# ==================== API Tests ====================


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_list_models(client):
    """Test model listing endpoint."""
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0
    assert data["data"][0]["id"] == "solacia"


def test_chat_completions(client):
    """Test chat completions endpoint."""
    request_data = {
        "model": "solacia",
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
    }

    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) > 0
    assert "message" in data["choices"][0]
    assert "content" in data["choices"][0]["message"]


# ==================== Emotion Detection Tests ====================


def test_emotion_keywords_happy(emotion_detector):
    """Test happy emotion keyword detection."""
    assert emotion_detector.detect("haha that's great") == "happy"
    assert emotion_detector.detect("I'm so happy right now") == "happy"
    assert emotion_detector.detect("awesome news") == "happy"


def test_emotion_keywords_sad(emotion_detector):
    """Test sad emotion keyword detection."""
    assert emotion_detector.detect("I feel so sad today") == "sad"
    assert emotion_detector.detect("it really hurts inside") == "sad"


def test_emotion_keywords_anxious(emotion_detector):
    """Test anxious emotion keyword detection."""
    assert emotion_detector.detect("I'm really nervous about this") == "anxious"
    assert emotion_detector.detect("the stress is overwhelming") == "anxious"
    assert emotion_detector.detect("I can't sleep at night") == "anxious"


def test_emotion_keywords_angry(emotion_detector):
    """Test angry emotion keyword detection."""
    assert emotion_detector.detect("I'm so angry right now") == "angry"
    assert emotion_detector.detect("this is so frustrating") == "angry"


def test_emotion_keywords_confused(emotion_detector):
    """Test confused emotion keyword detection."""
    assert emotion_detector.detect("I'm so confused about everything") == "confused"
    assert emotion_detector.detect("I have no idea what to do") == "confused"


def test_emotion_default_calm(emotion_detector):
    """Test default calm emotion for neutral input."""
    assert emotion_detector.detect("the weather is nice today") == "calm"


def test_emotion_get_style(emotion_detector):
    """Test getting emotion response style."""
    assert emotion_detector.get_style("happy") == "share the excitement"
    assert emotion_detector.get_style("sad") == "warm companionship"
    assert emotion_detector.get_style("anxious") == "gentle reassurance"


def test_emotion_get_name(emotion_detector):
    """Test getting emotion display name."""
    assert emotion_detector.get_emotion_name("happy") == "joyful"
    assert emotion_detector.get_emotion_name("sad") == "sad"


def test_emotions_dict():
    """Test emotion dictionary completeness."""
    expected_emotions = ["happy", "calm", "anxious", "sad", "angry", "confused"]
    for emotion in expected_emotions:
        assert emotion in EMOTIONS
        assert "name" in EMOTIONS[emotion]
        assert "style" in EMOTIONS[emotion]
        assert "keywords" in EMOTIONS[emotion]


# ==================== Diary API Tests ====================


def test_create_diary_entry(client):
    """Test creating a diary entry."""
    request_data = {
        "emotions": ["happy", "calm"],
        "summary": "Nice weather, good mood",
        "message_count": 10,
    }

    response = client.post("/v1/diary", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "created"


def test_get_diary_entries(client):
    """Test getting diary entry list."""
    # Create an entry first
    client.post("/v1/diary", json={"emotions": ["happy"], "summary": "test", "message_count": 5})

    # Get diary list
    response = client.get("/v1/diary")
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert len(data["entries"]) > 0


def test_get_diary_entry(client):
    """Test getting a single diary entry."""
    # Create an entry first
    create_response = client.post(
        "/v1/diary", json={"emotions": ["sad"], "summary": "A rough day", "message_count": 8}
    )
    entry_id = create_response.json()["id"]

    # Get that entry
    response = client.get(f"/v1/diary/{entry_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == entry_id
    assert "sad" in data["emotions"]


def test_get_diary_entry_not_found(client):
    """Test getting a non-existent diary entry."""
    response = client.get("/v1/diary/99999")
    assert response.status_code == 404


def test_get_emotion_stats(client):
    """Test getting emotion statistics."""
    # Create some diary entries
    client.post("/v1/diary", json={"emotions": ["happy", "calm"]})
    client.post("/v1/diary", json={"emotions": ["sad"]})
    client.post("/v1/diary", json={"emotions": ["happy"]})

    # Get emotion stats
    response = client.get("/v1/diary/stats/emotions?days=7")
    assert response.status_code == 200
    data = response.json()
    assert "emotions" in data
    assert data["days"] == 7
