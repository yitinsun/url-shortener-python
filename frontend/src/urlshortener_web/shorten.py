"""Validate a create form and POST /api/v1/shorten. This module owns that path."""

import os
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

import httpx

NETWORK = "The link service could not be reached."
UNAVAILABLE = "The link service is unavailable. Try again in a moment."


@dataclass(frozen=True)
class ShortenResult:
    long_url: str
    ttl_text: str
    error: str | None = None
    short_url: str | None = None
    short_code: str | None = None
    expires_at: str | None = None
    expires_label: str | None = None


def api_origin() -> str:
    return os.environ.get("API_ORIGIN", "http://localhost:8080").rstrip("/")


def create_link(long_url: str, ttl_text: str) -> ShortenResult:
    cleaned, ttl, error = _validate(long_url, ttl_text)
    if error:
        return ShortenResult(long_url=long_url, ttl_text=ttl_text, error=error)
    body: dict = {"longUrl": cleaned}
    if ttl is not None:
        body["ttlInDays"] = ttl
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{api_origin()}/api/v1/shorten", json=body)
    except httpx.HTTPError:
        return ShortenResult(long_url=cleaned, ttl_text=ttl_text, error=NETWORK)
    payload = _json_object(response)
    if payload is None:
        return ShortenResult(long_url=cleaned, ttl_text=ttl_text, error=NETWORK)
    if response.status_code == 201:
        expires_at = str(payload.get("expiresAt") or "")
        return ShortenResult(
            long_url=str(payload.get("longUrl") or cleaned),
            ttl_text=ttl_text,
            short_url=str(payload.get("shortUrl") or ""),
            short_code=str(payload.get("shortCode") or ""),
            expires_at=expires_at,
            expires_label=format_expires(expires_at),
        )
    message = payload.get("message")
    if response.status_code == 503:
        text = message if isinstance(message, str) and message else UNAVAILABLE
        return ShortenResult(long_url=cleaned, ttl_text=ttl_text, error=text)
    if response.status_code == 400 and isinstance(message, str) and message:
        return ShortenResult(long_url=cleaned, ttl_text=ttl_text, error=message)
    return ShortenResult(long_url=cleaned, ttl_text=ttl_text, error=NETWORK)


def format_expires(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return value
    return parsed.strftime("%d %b %Y, %H:%M:%S UTC")


def _validate(long_url: str, ttl_text: str) -> tuple[str, int | None, str | None]:
    cleaned = long_url.strip()
    if cleaned == "":
        return cleaned, None, "Long URL is required."
    if len(cleaned) > 2048:
        return cleaned, None, "Long URL must be at most 2048 characters."
    parsed = urlparse(cleaned)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return cleaned, None, "Long URL must start with http:// or https://."
    ttl_raw = ttl_text.strip()
    if ttl_raw == "":
        return cleaned, None, None
    if not ttl_raw.isdigit() or not 1 <= int(ttl_raw) <= 3650:
        return cleaned, None, "Lifetime must be a whole number of days from 1 to 3650."
    return cleaned, int(ttl_raw), None


def _json_object(response: httpx.Response) -> dict | None:
    media = response.headers.get("content-type", "")
    if "text/html" in media or "application/json" not in media:
        return None
    try:
        payload = response.json()
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload
