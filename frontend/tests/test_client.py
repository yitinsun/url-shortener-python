import httpx
import pytest
from starlette.testclient import TestClient

from urlshortener_web.app import app
from urlshortener_web.shorten import format_expires

LONG_URL = "https://example.com/docs"
EXPIRES = "2028-11-11T22:14:01Z"
CREATED = {
    "longUrl": LONG_URL,
    "shortUrl": "http://localhost:8080/short/3QkkP",
    "shortCode": "3QkkP",
    "expiresAt": EXPIRES,
}


class FakeResponse:
    def __init__(self, status_code, payload=None, media="application/json"):
        self.status_code = status_code
        self._payload = payload
        self.headers = {"content-type": media}

    def json(self):
        if not isinstance(self._payload, dict):
            raise ValueError("not json")
        return self._payload


class FakeClient:
    calls = []
    response = None
    error = None

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, json):
        self.calls.append((url, json))
        if self.error:
            raise self.error
        return self.response


@pytest.fixture
def client(monkeypatch):
    FakeClient.calls = []
    FakeClient.response = FakeResponse(201, CREATED)
    FakeClient.error = None
    monkeypatch.setattr("urlshortener_web.shorten.httpx.Client", FakeClient)
    return TestClient(app)


def test_blank_lifetime_omits_ttl(client):
    response = client.post("/", data={"longUrl": LONG_URL, "ttlInDays": ""})
    assert response.status_code == 200
    url, body = FakeClient.calls[0]
    assert url.endswith("/api/v1/shorten")
    assert body == {"longUrl": LONG_URL}
    assert "ttlInDays" not in body


def test_lifetime_365_is_sent(client):
    client.post("/", data={"longUrl": LONG_URL, "ttlInDays": "365"})
    assert FakeClient.calls[0][1] == {"longUrl": LONG_URL, "ttlInDays": 365}


@pytest.mark.parametrize(
    "form",
    [
        {"longUrl": "", "ttlInDays": ""},
        {"longUrl": "example.com/docs", "ttlInDays": ""},
        {"longUrl": "https://example.com/" + ("a" * 2040), "ttlInDays": ""},
        {"longUrl": LONG_URL, "ttlInDays": "0"},
    ],
)
def test_local_validation_skips_httpx_and_shows_an_error(client, form):
    response = client.post("/", data=form)
    assert FakeClient.calls == []
    assert response.status_code == 200
    assert 'class="error"' in response.text


def test_created_link_is_shown(client):
    response = client.post("/", data={"longUrl": LONG_URL, "ttlInDays": ""})
    text = response.text
    assert "Short link ready" in text
    assert CREATED["shortUrl"] in text
    assert CREATED["shortCode"] in text
    assert format_expires(EXPIRES) in text
    assert f'data-short-url="{CREATED["shortUrl"]}"' in text
    assert f'href="{CREATED["shortUrl"]}"' in text


def test_second_create_still_says_ready(client):
    first = client.post("/", data={"longUrl": LONG_URL})
    second = client.post("/", data={"longUrl": LONG_URL})
    assert "Short link ready" in first.text
    assert "Short link ready" in second.text


def test_api_400_keeps_the_typed_url(client):
    FakeClient.response = FakeResponse(
        400,
        {"status": 400, "error": "Bad Request", "message": "longUrl must not target this service", "shortCode": None},
    )
    response = client.post("/", data={"longUrl": "http://localhost:8080/self", "ttlInDays": ""})
    assert "longUrl must not target this service" in response.text
    assert 'value="http://localhost:8080/self"' in response.text
    assert "Short link ready" not in response.text


def test_api_503_shows_the_message(client):
    FakeClient.response = FakeResponse(
        503,
        {"status": 503, "error": "Service Unavailable", "message": "The database is unavailable", "shortCode": None},
    )
    response = client.post("/", data={"longUrl": LONG_URL})
    assert "The database is unavailable" in response.text


def test_httpx_error_is_a_reachable_sentence(client):
    FakeClient.error = httpx.ConnectError("down")
    response = client.post("/", data={"longUrl": LONG_URL})
    assert "The link service could not be reached." in response.text
    assert "<html" not in response.text.split('class="error"')[-1][:80]


def test_html_body_is_not_rendered(client):
    FakeClient.response = FakeResponse(404, None, media="text/html; charset=utf-8")
    response = client.post("/", data={"longUrl": LONG_URL})
    assert "The link service could not be reached." in response.text
    assert "Whitelabel" not in response.text


def test_first_paint_uses_the_python_pictures(client):
    response = client.get("/")
    assert response.status_code == 200
    for alt in (
        "Stone table with an open sketchbook, a pencil, and a ceramic cup",
        "Hands lowering a rolled blue sheet into a ceramic bowl",
        "Five dotted stones in a row on blue paper",
        "Open window looking onto a garden path",
    ):
        assert f'alt="{alt}"' in response.text
    assert "Short link ready" not in response.text
    assert response.status_code == 200


def test_pictures_and_fonts_are_local_files(client):
    for path in (
        "/static/assets/hero-desk.webp",
        "/static/assets/step-paste.webp",
        "/static/assets/step-code.webp",
        "/static/assets/step-open.webp",
        "/static/fonts/fraunces.woff2",
        "/static/fonts/source-sans-3.woff2",
        "/static/styles.css",
        "/static/app.js",
    ):
        asset = client.get(path)
        assert asset.status_code == 200, path
        assert asset.content


def test_unknown_client_route_is_a_quiet_page(client):
    response = client.get("/no-such")
    assert response.status_code == 404
    assert "Short" in response.text
    assert 'href="/"' in response.text
    assert "<img" not in response.text
    assert "Link not found" not in response.text
