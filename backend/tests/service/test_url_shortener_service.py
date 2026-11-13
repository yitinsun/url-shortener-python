from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from urlshortener.clock import utcnow
from urlshortener.service.url_shortener import (
    ResourceNotFoundError,
    UrlShortenerService,
    UrlValidationError,
)
from urlshortener.settings import Settings


def _service(repository=None):
    settings = Settings(app_env="test", app_base_url="http://localhost:8080")
    return UrlShortenerService(repository or MagicMock(), settings)


def test_missing_short_code_raises():
    repository = MagicMock()
    repository.find_by_short_code.return_value = None
    with pytest.raises(ResourceNotFoundError):
        _service(repository).resolve("missing")


def test_expired_mapping_raises():
    repository = MagicMock()
    repository.find_by_short_code.return_value = SimpleNamespace(expires_at=datetime(2000, 1, 1))
    with pytest.raises(ResourceNotFoundError):
        _service(repository).resolve("expired")


def test_idempotent_create_returns_the_active_row_without_insert():
    repository = MagicMock()
    existing = SimpleNamespace(short_code="abc12", long_url="https://example.com/same")
    repository.find_active_by_long_url.return_value = existing
    created = _service(repository).create("https://example.com/same", 15)
    assert created is existing
    repository.insert.assert_not_called()


def test_omitted_ttl_is_730_days():
    repository = MagicMock()
    repository.find_active_by_long_url.return_value = None
    before = utcnow()
    _service(repository).create("https://example.com/ttl", None)
    expires_at = repository.insert.call_args.args[1]
    after = utcnow()
    assert before + timedelta(days=730) <= expires_at <= after + timedelta(days=730)


def test_self_loop_is_rejected():
    with pytest.raises(UrlValidationError):
        _service().create("http://LOCALHOST:8080/own", None)


def test_oversize_url_is_rejected():
    with pytest.raises(UrlValidationError):
        _service().create("https://example.com/" + ("a" * 2048), None)
