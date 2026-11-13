"""UTC timestamps stored as naive datetimes."""

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None, microsecond=0)
