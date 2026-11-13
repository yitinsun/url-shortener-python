"""HTTP routes for create and redirect."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session, sessionmaker

from urlshortener.repositories.url_mapping_repository import UrlMappingRepository
from urlshortener.service.url_shortener import UrlShortenerService
from urlshortener.settings import Settings
from urlshortener.web.dto import ErrorResponse, ShortenRequest, ShortenResponse


def format_expires(value: datetime) -> str:
    if value.tzinfo is None:
        aware = value.replace(tzinfo=UTC)
    else:
        aware = value.astimezone(UTC)
    return aware.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_session(request: Request):
    factory: sessionmaker = request.app.state.session_factory
    session = factory()
    try:
        yield session
    finally:
        session.close()


def build_router() -> APIRouter:
    router = APIRouter()

    @router.post(
        "/api/v1/shorten",
        status_code=201,
        response_model=ShortenResponse,
        responses={
            400: {"model": ErrorResponse, "description": "Invalid body"},
            503: {"model": ErrorResponse, "description": "Database unavailable"},
        },
    )
    def shorten(
        body: ShortenRequest,
        request: Request,
        session: Session = Depends(get_session),
    ) -> JSONResponse:
        settings: Settings = request.app.state.settings
        service = UrlShortenerService(UrlMappingRepository(session), settings)
        row = service.create(body.long_url, body.ttl_in_days)
        payload = ShortenResponse(
            long_url=row.long_url,
            short_url=f"{settings.base_url}/short/{row.short_code}",
            short_code=row.short_code,
            expires_at=format_expires(row.expires_at),
        )
        return JSONResponse(status_code=201, content=payload.model_dump(by_alias=True))

    @router.get("/short/{short_code}", include_in_schema=False)
    def redirect_short(short_code: str, request: Request, session: Session = Depends(get_session)):
        settings: Settings = request.app.state.settings
        service = UrlShortenerService(UrlMappingRepository(session), settings)
        row = service.resolve(short_code)
        return RedirectResponse(url=row.long_url, status_code=302)

    return router
