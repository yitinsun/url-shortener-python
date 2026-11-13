from pathlib import Path

from fastapi.testclient import TestClient

from urlshortener.main import create_app
from urlshortener.settings import Settings
from urlshortener.web.html_sanitizer import looks_unsafe

CLEAN = "https://example.com/path"
SCRIPT = "https://example.com/path?q=<script>alert(1)</script>"
IMAGE = "https://example.com/path?q=<img src=x>"


def test_plain_url_is_safe():
    assert looks_unsafe(CLEAN) is False
    assert looks_unsafe("https://example.com/script") is False
    assert looks_unsafe(None) is False


def test_script_and_img_are_unsafe():
    assert looks_unsafe("<script>alert(1)</script>") is True
    assert looks_unsafe(SCRIPT) is True
    assert looks_unsafe("<img src=x>") is True
    assert looks_unsafe(IMAGE) is True


def test_pyproject_has_beautifulsoup_and_no_auth_library():
    text = Path(__file__).resolve().parents[2].joinpath("pyproject.toml").read_text(encoding="utf-8").lower()
    assert "beautifulsoup4" in text
    assert "lxml" not in text
    for banned in ("pyjwt", "python-jose", "authlib", "fastapi-users"):
        assert banned not in text


def test_html_in_long_url_is_400_json_without_a_token():
    app = create_app(Settings(app_env="test", app_base_url="http://localhost:8080"))
    with TestClient(app) as client:
        for long_url in (SCRIPT, IMAGE, "<b>hello</b>"):
            response = client.post("/api/v1/shorten", json={"longUrl": long_url})
            assert response.status_code == 400
            body = response.json()
            assert body["status"] == 400
            assert body["error"] == "Bad Request"
            assert body["shortCode"] is None
            message = body["message"].lower()
            assert "html" in message or "sanitization" in message
            assert "www-authenticate" not in {name.lower() for name in response.headers}


def test_clean_post_stays_public_and_illegal_paths_stay_html():
    app = create_app(Settings(app_env="test", app_base_url="http://localhost:8080"))
    with TestClient(app) as client:
        created = client.post("/api/v1/shorten", json={"longUrl": CLEAN})
        assert created.status_code == 201
        assert created.json()["shortCode"]
        blocked = client.post("/nope", json={"longUrl": SCRIPT})
        assert blocked.status_code == 404
        assert "text/html" in blocked.headers["content-type"]
        assert "Link not found" in blocked.text
        invalid = client.post(
            "/api/v1/shorten",
            content=b"not-json",
            headers={"content-type": "application/json"},
        )
        assert invalid.status_code == 400
        assert invalid.json()["shortCode"] is None
        number = client.post("/api/v1/shorten", json={"longUrl": 1})
        assert number.status_code == 400
        assert "sanitization" not in number.json()["message"].lower()
