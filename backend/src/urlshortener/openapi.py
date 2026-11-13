"""OpenAPI metadata. Documentation only; it does not change the API."""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from urlshortener.settings import Settings

TITLE = "URL Shortener API"
VERSION = "0.1.0"


def build_openapi(app: FastAPI, settings: Settings) -> dict:
    schema = get_openapi(
        title=TITLE,
        version=VERSION,
        routes=app.routes,
        description="Create a short code from a long HTTP(S) URL and redirect that code.",
    )
    schema["servers"] = [{"url": settings.base_url}]
    schema.pop("security", None)
    components = schema.get("components")
    if isinstance(components, dict):
        components.pop("securitySchemes", None)
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict):
                operation.get("responses", {}).pop("422", None)
    return schema


def install_openapi(app: FastAPI, settings: Settings) -> None:
    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        app.openapi_schema = build_openapi(app, settings)
        return app.openapi_schema

    app.openapi = custom_openapi
