import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from sqlalchemy.orm import sessionmaker

from urlshortener.clock import utcnow
from urlshortener.db.session import sqlite_test_engine
from urlshortener.models.url_mapping import UrlMapping
from urlshortener.repositories.url_mapping_repository import UrlMappingRepository
from urlshortener.schedule.cleanup import cleanup_loop, run_cleanup


def test_cleanup_passes_cutoff_as_a_bind_parameter():
    cutoff = datetime(2019, 5, 4, 3, 2, 1)
    session = MagicMock()
    session.scalars.return_value.all.return_value = []
    run_cleanup(session, cutoff, batch_size=25)
    statement, params = session.scalars.call_args.args
    compiled = str(statement.compile(compile_kwargs={"literal_binds": False}))
    assert "2019" not in compiled
    assert params["cutoff"] == cutoff
    assert params["limit"] == 25


def test_cleanup_deletes_expired_rows_in_batches():
    engine = sqlite_test_engine()
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = factory()
    repository = UrlMappingRepository(session)
    fresh = repository.insert("https://example.com/fresh", utcnow() + timedelta(days=5))
    stale = repository.insert("https://example.com/stale", utcnow() + timedelta(days=5))
    fresh_id = fresh.id
    stale_id = stale.id
    stale.expires_at = datetime(2000, 1, 1)
    session.commit()
    removed = run_cleanup(session, utcnow(), batch_size=1)
    session.close()
    check = factory()
    assert removed == 1
    assert check.get(UrlMapping, fresh_id) is not None
    assert check.get(UrlMapping, stale_id) is None
    check.close()
    engine.dispose()


def test_cleanup_loop_stops_when_asked():
    stop = asyncio.Event()
    stop.set()
    asyncio.run(cleanup_loop(stop, MagicMock(), interval_seconds=3600))


def test_cleanup_loop_purges_after_the_wait(monkeypatch):
    stop = asyncio.Event()

    async def fake_wait(awaitable, timeout):
        awaitable.close()
        raise TimeoutError

    def purge(_factory):
        stop.set()
        return 0

    monkeypatch.setattr("urlshortener.schedule.cleanup.asyncio.wait_for", fake_wait)
    monkeypatch.setattr("urlshortener.schedule.cleanup.purge_expired", purge)
    asyncio.run(cleanup_loop(stop, object(), interval_seconds=3600))
