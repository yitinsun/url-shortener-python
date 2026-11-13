from fastapi.testclient import TestClient

from urlshortener.main import create_app
from urlshortener.settings import Settings
from urlshortener.web.pages import not_found_page


def _client(**overrides) -> TestClient:
    settings = Settings(app_env="test", app_base_url="http://localhost:8080", **overrides)
    return TestClient(create_app(settings))


def _assert_friendly_404(response, path: str) -> None:
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "<h1>Link not found</h1>" in response.text
    assert "Whitelabel" not in response.text
    assert '{"detail"' not in response.text
    assert html_escape(path) in response.text
    assert 'href="/api/v1/shorten"' in response.text
    assert 'href="/docs"' in response.text
    assert 'href="/short/{code}"' in response.text


def html_escape(path: str) -> str:
    return path.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


def test_not_found_page_escapes_markup():
    page = not_found_page('/a<b>&"c')
    assert "&lt;" in page
    assert "&amp;" in page
    assert "&quot;" in page
    assert "<b>" not in page


def test_active_code_still_redirects():
    with _client() as client:
        created = client.post("/api/v1/shorten", json={"longUrl": "https://example.com/legal"})
        assert created.status_code == 201
        code = created.json()["shortCode"]
        response = client.get(f"/short/{code}", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "https://example.com/legal"


def test_unknown_code_is_friendly_html():
    with _client() as client:
        response = client.get("/short/unknown", follow_redirects=False)
        _assert_friendly_404(response, "/short/unknown")


def test_illegal_paths_are_friendly_html():
    with _client() as client:
        for path in ("/b9K2x1", "/", "/nope", "/index.html", "/short/", "/metrics", "/actuator/health"):
            _assert_friendly_404(client.get(path), path)


def test_get_on_create_path_is_friendly_html():
    with _client() as client:
        _assert_friendly_404(client.get("/api/v1/shorten"), "/api/v1/shorten")


def test_valid_post_stays_json():
    with _client() as client:
        response = client.post("/api/v1/shorten", json={"longUrl": "https://example.com/still-json"})
        assert response.status_code == 201
        assert response.json()["shortCode"]


def test_openapi_stays_available_when_docs_are_enabled():
    with _client() as client:
        spec = client.get("/openapi.json")
        assert spec.status_code == 200
        assert "/api/v1/shorten" in spec.text
        assert "/{shortCode}" not in spec.text
        assert all(not path.startswith("/{") for path in spec.json()["paths"])


def test_docs_paths_are_illegal_when_docs_are_off():
    with _client(docs_enabled=False) as client:
        for path in ("/docs", "/openapi.json"):
            _assert_friendly_404(client.get(path), path)
