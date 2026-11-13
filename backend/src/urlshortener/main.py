"""FastAPI application."""

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from urlshortener.db.session import build_engine
from urlshortener.openapi import TITLE, VERSION, install_openapi
from urlshortener.schedule.cleanup import cleanup_loop
from urlshortener.settings import Settings
from urlshortener.web.errors import register_exception_handlers
from urlshortener.web.legal_paths import LegalPathMiddleware
from urlshortener.web.routes import build_router
from urlshortener.web.sanitize_middleware import SanitizeMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = build_engine(settings)
        app.state.engine = engine
        app.state.settings = settings
        app.state.session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        stop = asyncio.Event()
        task = asyncio.create_task(cleanup_loop(stop, app.state.session_factory))
        try:
            yield
        finally:
            stop.set()
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            engine.dispose()

    docs_on = bool(settings.docs_enabled)
    app = FastAPI(
        title=TITLE,
        version=VERSION,
        docs_url="/docs" if docs_on else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs_on else None,
        lifespan=lifespan,
    )
    register_exception_handlers(app)
    app.include_router(build_router())
    app.add_middleware(SanitizeMiddleware)
    app.add_middleware(LegalPathMiddleware, docs_enabled=docs_on)
    install_openapi(app, settings)
    return app


app = create_app()
