from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from urlshortener.main import create_app
from urlshortener.models.url_mapping import UrlMapping
from urlshortener.repositories.url_mapping_repository import UrlMappingRepository
from urlshortener.settings import Settings

LONG_URL = "https://example.com/api-design/api-design-url-shortening-service/"


@pytest.fixture
def client():
    app = create_app(Settings(app_env="test", app_base_url="http://localhost:8080"))
    with TestClient(app) as test_client:
        yield test_client


def test_valid_https_url_returns_201(client):
    response = client.post("/api/v1/shorten", json={"longUrl": LONG_URL})
    assert response.status_code == 201
    body = response.json()
    assert body["longUrl"] == LONG_URL
    assert body["shortUrl"].startswith("http://localhost:8080/short/")
    assert 5 <= len(body["shortCode"]) <= 7
    assert body["expiresAt"].endswith("Z")


def test_second_post_returns_the_same_short_code(client):
    first = client.post("/api/v1/shorten", json={"longUrl": LONG_URL, "ttlInDays": 10})
    second = client.post("/api/v1/shorten", json={"longUrl": LONG_URL, "ttlInDays": 20})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["shortCode"] == second.json()["shortCode"]
    assert first.json()["expiresAt"] == second.json()["expiresAt"]


def test_invalid_url_returns_400_json(client):
    response = client.post("/api/v1/shorten", json={"longUrl": "not-a-valid-url"})
    assert response.status_code == 400
    body = response.json()
    assert body["status"] == 400
    assert body["message"]
    assert body["shortCode"] is None


def test_self_loop_returns_400(client):
    response = client.post("/api/v1/shorten", json={"longUrl": "http://localhost:8080/self"})
    assert response.status_code == 400
    assert response.json()["status"] == 400


def test_active_mapping_redirects_302(client):
    created = client.post("/api/v1/shorten", json={"longUrl": "https://example.com/go"})
    code = created.json()["shortCode"]
    response = client.get(f"/short/{code}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/go"


def test_unknown_code_is_friendly_html(client):
    response = client.get("/short/notreal", follow_redirects=False)
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "Link not found" in response.text
    assert '{"detail"' not in response.text


def test_expired_mapping_is_friendly_html(client):
    created = client.post("/api/v1/shorten", json={"longUrl": "https://example.com/old"})
    code = created.json()["shortCode"]
    session = client.app.state.session_factory()
    try:
        row = session.scalar(select(UrlMapping).where(UrlMapping.short_code == code))
        row.expires_at = datetime(2000, 1, 1)
        session.commit()
    finally:
        session.close()
    response = client.get(f"/short/{code}", follow_redirects=False)
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "Link not found" in response.text
    assert '{"detail"' not in response.text


def test_urls_that_share_a_255_character_prefix_stay_distinct(client):
    stem = "https://example.com/" + ("a" * 240)
    first = client.post("/api/v1/shorten", json={"longUrl": stem + "ONE"})
    second = client.post("/api/v1/shorten", json={"longUrl": stem + "TWO"})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["shortCode"] != second.json()["shortCode"]


def test_database_outage_returns_503(client, monkeypatch):
    def boom(*_args, **_kwargs):
        raise OperationalError("SELECT", {}, Exception("down"))

    monkeypatch.setattr(UrlMappingRepository, "find_active_by_long_url", boom)
    response = client.post("/api/v1/shorten", json={"longUrl": "https://example.com/down"})
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == 503
    assert body["message"]
    assert body["shortCode"] is None
