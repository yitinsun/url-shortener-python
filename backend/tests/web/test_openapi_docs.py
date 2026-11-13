import pytest
from fastapi.testclient import TestClient

from urlshortener.main import create_app
from urlshortener.settings import Settings


@pytest.fixture
def client():
    app = create_app(Settings(app_env="test", app_base_url="http://localhost:8080"))
    with TestClient(app) as test_client:
        yield test_client


def test_dev_and_test_enable_docs_by_default():
    assert Settings(app_env="dev").docs_enabled is True
    assert Settings(app_env="test").docs_enabled is True


def test_prod_leaves_docs_off_unless_enabled():
    prod = Settings(app_env="prod", db_name="shortener_prod")
    assert prod.docs_enabled is False
    app = create_app(prod)
    assert app.docs_url is None
    assert app.openapi_url is None
    assert app.redoc_url is None

    enabled = create_app(Settings(app_env="prod", db_name="shortener_prod", docs_enabled=True))
    assert enabled.docs_url == "/docs"
    assert enabled.openapi_url == "/openapi.json"


def test_docs_and_openapi_schema(client):
    page = client.get("/docs")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert "URL Shortener API" in page.text

    spec = client.get("/openapi.json")
    assert spec.status_code == 200
    body = spec.json()
    assert body["openapi"].startswith("3.")
    assert body["info"]["title"] == "URL Shortener API"
    assert body["info"]["version"] == "0.1.0"
    assert body["servers"] == [{"url": "http://localhost:8080"}]
    assert "security" not in body
    post = body["paths"]["/api/v1/shorten"]["post"]
    assert "201" in post["responses"]
    assert "400" in post["responses"]
    assert "503" in post["responses"]
    assert "422" not in post["responses"]
    assert "longUrl" in spec.text
    assert not any(path.startswith("/short") for path in body["paths"])
