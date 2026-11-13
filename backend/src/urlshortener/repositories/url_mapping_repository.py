"""Parameterized access to url_mappings."""

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from urlshortener.clock import utcnow
from urlshortener.encoding.base62 import encode
from urlshortener.models.url_mapping import UrlMapping


class UrlMappingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_by_short_code(self, short_code: str) -> UrlMapping | None:
        return self.session.scalar(select(UrlMapping).where(UrlMapping.short_code == short_code))

    def find_active_by_long_url(self, long_url: str, now) -> UrlMapping | None:
        """Prefix lookup, then a full-string compare so tails past 255 characters stay distinct."""
        prefix = long_url[:255]
        rows = self.session.scalars(
            select(UrlMapping).where(
                UrlMapping.long_url.startswith(prefix),
                UrlMapping.expires_at > now,
            )
        ).all()
        for row in rows:
            if row.long_url == long_url:
                return row
        return None

    def insert(self, long_url: str, expires_at) -> UrlMapping:
        row = UrlMapping(
            long_url=long_url,
            short_code=secrets.token_hex(5),
            created_at=utcnow(),
            expires_at=expires_at,
        )
        self.session.add(row)
        try:
            self.session.flush()
            row.short_code = encode(row.id)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return row
