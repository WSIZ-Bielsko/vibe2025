import pytest
from fastapi.testclient import TestClient
from vibe2025.main import app
from vibe2025.cache import forex_cache

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    forex_cache.clear()
    yield
    forex_cache.clear()


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_convert_valid():
    """Test valid currency conversion."""
    response = client.get("/convert?pair=EURUSD&volume=100")
    assert response.status_code == 200
    assert "result" in response.json()
    assert isinstance(response.json()["result"], float)


def test_convert_uses_cache():
    """Test that subsequent requests use cache."""
    # First request - should fetch from API
    response1 = client.get("/convert?pair=EURUSD&volume=100")
    assert response1.status_code == 200

    # Second request - should use cache
    response2 = client.get("/convert?pair=EURUSD&volume=100")
    assert response2.status_code == 200
    assert response1.json()["result"] == response2.json()["result"]


def test_convert_no_cache():
    """Test bypassing cache with no_cache parameter."""
    response = client.get("/convert?pair=EURUSD&volume=100&no_cache=true")
    assert response.status_code == 200
    assert "result" in response.json()


def test_cache_stats():
    """Test cache statistics endpoint."""
    response = client.get("/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert "size" in data
    assert "maxsize" in data
    assert "ttl_seconds" in data


def test_cache_clear():
    """Test cache clearing endpoint."""
    # Make a request to populate cache
    client.get("/convert?pair=EURUSD&volume=100")

    # Clear cache
    response = client.post("/cache/clear")
    assert response.status_code == 200

    # Verify cache is empty
    stats = client.get("/cache/stats").json()
    assert stats["size"] == 0


def test_convert_invalid_pair():
    """Test invalid currency pair length."""
    response = client.get("/convert?pair=EUR&volume=100")
    assert response.status_code == 422


def test_convert_negative_volume():
    """Test negative volume."""
    response = client.get("/convert?pair=EURUSD&volume=-100")
    assert response.status_code == 422


def test_convert_missing_params():
    """Test missing required parameters."""
    response = client.get("/convert")
    assert response.status_code == 422
