"""Create and resolve short links."""

from datetime import timedelta
from urllib.parse import urlparse

from urlshortener.clock import utcnow
from urlshortener.repositories.url_mapping_repository import UrlMappingRepository
from urlshortener.settings import Settings

DEFAULT_TTL_DAYS = 730


class UrlValidationError(ValueError):
    """Rejected create request. Mapped to HTTP 400."""


class ResourceNotFoundError(Exception):
    """Missing or expired short code. Mapped to HTML 404."""


class UrlShortenerService:
    def __init__(self, repository: UrlMappingRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    def create(self, long_url: str, ttl_in_days: int | None):
        self._validate_url(long_url)
        ttl = self._validate_ttl(ttl_in_days)
        now = utcnow()
        existing = self.repository.find_active_by_long_url(long_url, now)
        if existing is not None:
            return existing
        expires_at = now + timedelta(days=ttl)
        return self.repository.insert(long_url, expires_at)

    def resolve(self, short_code: str):
        row = self.repository.find_by_short_code(short_code)
        if row is None or row.expires_at <= utcnow():
            raise ResourceNotFoundError(short_code)
        return row

    def _validate_url(self, long_url: str) -> None:
        if long_url is None or long_url == "":
            raise UrlValidationError("longUrl is required")
        if len(long_url) > 2048:
            raise UrlValidationError("longUrl must be at most 2048 characters")
        parsed = urlparse(long_url)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            raise UrlValidationError("longUrl must be an absolute http or https URL")
        base_host = urlparse(self.settings.base_url).hostname
        if base_host and parsed.hostname.lower() == base_host.lower():
            raise UrlValidationError("longUrl must not target this service")

    def _validate_ttl(self, ttl_in_days: int | None) -> int:
        if ttl_in_days is None:
            return DEFAULT_TTL_DAYS
        if isinstance(ttl_in_days, bool) or not isinstance(ttl_in_days, int):
            raise UrlValidationError("ttlInDays must be an integer from 1 to 3650")
        if not 1 <= ttl_in_days <= 3650:
            raise UrlValidationError("ttlInDays must be an integer from 1 to 3650")
        return ttl_in_days
