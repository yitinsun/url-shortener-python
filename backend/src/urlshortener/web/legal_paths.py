"""Allowlist fence. Illegal URLs never reach the router."""

import re

from urlshortener.web.pages import not_found_page

_SHORT_CODE = re.compile(r"^/short/[0-9A-Za-z]{1,10}$")
_DOC_PATHS = {"/docs", "/openapi.json"}


def is_legal(method: str, path: str, *, docs_enabled: bool) -> bool:
    method = method.upper()
    if method == "POST" and path == "/api/v1/shorten":
        return True
    if method == "GET" and _SHORT_CODE.fullmatch(path):
        return True
    if docs_enabled and method == "GET" and path in _DOC_PATHS:
        return True
    return False


class LegalPathMiddleware:
    """ASGI middleware registered outside routing."""

    def __init__(self, app, docs_enabled: bool = False) -> None:
        self.app = app
        self.docs_enabled = docs_enabled

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path") or "/"
        if is_legal(scope.get("method", ""), path, docs_enabled=self.docs_enabled):
            await self.app(scope, receive, send)
            return
        body = not_found_page(path).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 404,
                "headers": [
                    (b"content-type", b"text/html; charset=utf-8"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
