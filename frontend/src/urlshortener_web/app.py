"""Starlette UI. Importing this module does not call the API."""

from pathlib import Path
from urllib.parse import parse_qs

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from urlshortener_web.shorten import ShortenResult, api_origin, create_link

ROOT = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(ROOT / "templates"))


def _fields(body: bytes) -> tuple[str, str]:
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return "", ""
    parsed = parse_qs(text, keep_blank_values=True)
    long_url = parsed.get("longUrl", [""])[0]
    ttl_text = parsed.get("ttlInDays", [""])[0]
    return long_url, ttl_text


def _page(request: Request, result: ShortenResult):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "long_url": result.long_url,
            "ttl_text": result.ttl_text,
            "error": result.error,
            "result": result if result.short_url else None,
        },
    )


async def home(request: Request):
    if request.method == "GET":
        return _page(request, ShortenResult(long_url="", ttl_text=""))
    long_url, ttl_text = _fields(await request.body())
    return _page(request, create_link(long_url, ttl_text))


async def missing(request: Request):
    return templates.TemplateResponse(request, "not_found.html", {}, status_code=404)


async def proxy_api(request: Request) -> Response:
    url = api_origin() + request.url.path
    if request.url.query:
        url = f"{url}?{request.url.query}"
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            upstream = await client.request(request.method, url, content=await request.body(), headers=headers)
    except httpx.HTTPError:
        return Response("The link service could not be reached.", status_code=502)
    media = upstream.headers.get("content-type")
    return Response(content=upstream.content, status_code=upstream.status_code, media_type=media)


def create_app() -> Starlette:
    return Starlette(
        routes=[
            Mount("/static", app=StaticFiles(directory=str(ROOT / "static")), name="static"),
            Route("/api/{path:path}", proxy_api, methods=["GET", "POST", "PUT", "PATCH", "DELETE"]),
            Route("/", home, methods=["GET", "POST"]),
            Route("/{path:path}", missing),
        ]
    )


app = create_app()
