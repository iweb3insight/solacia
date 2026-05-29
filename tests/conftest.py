"""
Solacia - Test Configuration
"""

import pytest
import sys
from pathlib import Path

# Add src/ to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


@pytest.fixture(scope="session")
def project_root():
    """Project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Test data directory."""
    return project_root / "tests" / "data"


@pytest.fixture(scope="session")
def sample_conversation():
    """Sample conversation data for testing."""
    return {
        "user_input": "今天心情不太好",
        "expected_emotion": "sad",
        "expected_response_style": "warm companionship"
    }
