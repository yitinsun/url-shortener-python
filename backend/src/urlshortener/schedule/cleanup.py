"""Hourly batched delete of expired mappings."""

import asyncio
from datetime import datetime

from sqlalchemy import bindparam, delete, select
from sqlalchemy.orm import Session, sessionmaker

from urlshortener.clock import utcnow
from urlshortener.models.url_mapping import UrlMapping


def expired_id_select():
    return (
        select(UrlMapping.id)
        .where(UrlMapping.expires_at < bindparam("cutoff"))
        .limit(bindparam("limit"))
    )


def run_cleanup(session: Session, cutoff: datetime, batch_size: int = 1000) -> int:
    """Delete expired rows in batches. The cutoff is a bind parameter."""
    total = 0
    select_statement = expired_id_select()
    while True:
        ids = list(session.scalars(select_statement, {"cutoff": cutoff, "limit": batch_size}).all())
        if not ids:
            break
        session.execute(
            delete(UrlMapping).where(UrlMapping.id.in_(bindparam("ids", expanding=True))),
            {"ids": ids},
        )
        session.commit()
        total += len(ids)
        if len(ids) < batch_size:
            break
    return total


def purge_expired(session_factory: sessionmaker) -> int:
    session = session_factory()
    try:
        return run_cleanup(session, utcnow())
    finally:
        session.close()


async def cleanup_loop(
    stop: asyncio.Event,
    session_factory: sessionmaker,
    interval_seconds: int = 3600,
) -> None:
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval_seconds)
        except TimeoutError:
            purge_expired(session_factory)
