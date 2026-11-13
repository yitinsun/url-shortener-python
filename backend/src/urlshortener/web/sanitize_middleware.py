"""Reject HTML in longUrl. LegalPathMiddleware stays outside this middleware."""

import json

from starlette.requests import Request

from urlshortener.web.errors import SanitizationError
from urlshortener.web.html_sanitizer import looks_unsafe


class SanitizeMiddleware:
    """ASGI middleware for POST /api/v1/shorten only."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope.get("method") != "POST" or scope.get("path") != "/api/v1/shorten":
            await self.app(scope, receive, send)
            return
        body = await _read_body(receive)
        if body is None:
            return
        replay = _replay(body)
        long_url = _long_url(body)
        if long_url is not None and looks_unsafe(long_url):
            # User middleware sits outside ExceptionMiddleware, so invoke the
            # registered handler. That handler still owns the 400 JSON body.
            exc = SanitizationError("longUrl failed HTML sanitization")
            handler = scope["app"].exception_handlers[SanitizationError]
            response = await handler(Request(scope), exc)
            await response(scope, replay, send)
            return
        await self.app(scope, replay, send)


def _long_url(body: bytes) -> str | None:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    value = payload.get("longUrl")
    if not isinstance(value, str):
        return None
    return value


async def _read_body(receive) -> bytes | None:
    chunks: list[bytes] = []
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            return None
        chunks.append(message.get("body", b""))
        if not message.get("more_body", False):
            return b"".join(chunks)


def _replay(body: bytes):
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return receive
