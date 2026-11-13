"""JSON error bodies for the create API."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, TimeoutError as SqlTimeoutError

from urlshortener.service.url_shortener import ResourceNotFoundError, UrlValidationError
from urlshortener.web.dto import ErrorResponse
from urlshortener.web.pages import not_found_page

class SanitizationError(Exception):
    """HTML in longUrl. Mapped to the existing 400 JSON body."""


_TITLES = {400: "Bad Request", 503: "Service Unavailable"}


def error_payload(status: int, message: str) -> dict:
    body = ErrorResponse(status=status, error=_TITLES[status], message=message, short_code=None)
    return body.model_dump(by_alias=True)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(UrlValidationError)
    async def validation_error(_request: Request, exc: UrlValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content=error_payload(400, str(exc)))

    @app.exception_handler(SanitizationError)
    async def sanitization_error(_request: Request, exc: SanitizationError) -> JSONResponse:
        return JSONResponse(status_code=400, content=error_payload(400, str(exc)))

    @app.exception_handler(RequestValidationError)
    async def request_validation(_request: Request, exc: RequestValidationError) -> JSONResponse:
        parts = []
        for item in exc.errors():
            location = ".".join(str(piece) for piece in item.get("loc", []) if piece != "body")
            detail = item.get("msg", "Invalid request")
            parts.append(f"{location}: {detail}" if location else str(detail))
        message = "; ".join(parts) or "Invalid request"
        return JSONResponse(status_code=400, content=error_payload(400, message))

    @app.exception_handler(ResourceNotFoundError)
    async def missing(_request: Request, _exc: ResourceNotFoundError):
        from fastapi.responses import HTMLResponse

        return HTMLResponse(not_found_page(_request.url.path), status_code=404)

    @app.exception_handler(OperationalError)
    async def database_down(_request: Request, _exc: OperationalError) -> JSONResponse:
        return JSONResponse(status_code=503, content=error_payload(503, "The database is unavailable"))

    @app.exception_handler(SqlTimeoutError)
    async def database_timeout(_request: Request, _exc: SqlTimeoutError) -> JSONResponse:
        return JSONResponse(status_code=503, content=error_payload(503, "The database is unavailable"))
