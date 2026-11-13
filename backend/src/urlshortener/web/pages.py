"""HTML shown for a missing short link and for any URL outside the allowlist."""

import html


def not_found_page(path: str) -> str:
    safe_path = html.escape(path, quote=True)
    return (
        "<!DOCTYPE html>"
        '<html lang="en"><head><meta charset="utf-8"><title>Link not found</title></head>'
        '<body style="background:#ffffff;color:#111111;font-family:sans-serif">'
        "<h1>Link not found</h1>"
        "<p>This address is not an active short link.</p>"
        f"<p>Path: {safe_path}</p>"
        "<p>Legal paths: "
        '<a href="/api/v1/shorten">POST /api/v1/shorten</a>, '
        '<a href="/docs">/docs</a>, '
        '<a href="/short/{code}">/short/{code}</a>.'
        "</p></body></html>"
    )
