"""Database engines. MySQL DDL is schema.sql. Tests use SQLite."""

from pathlib import Path

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, event, inspect
from sqlalchemy.engine import Connection, Engine, URL
from sqlalchemy.pool import StaticPool

from urlshortener.models.url_mapping import Base
from urlshortener.settings import Settings

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
REQUIRED_COLUMNS = {"id", "long_url", "short_code", "created_at", "expires_at"}
TEST_ID_START = 56800235


def split_sql(script: str) -> list[str]:
    return [part.strip() for part in script.split(";") if part.strip()]


def is_already_exists(exc: BaseException) -> bool:
    origin = getattr(exc, "orig", exc)
    args = getattr(origin, "args", ())
    if args and args[0] in (1007, 1050):
        return True
    return "already exists" in str(exc).lower()


def mysql_url(settings: Settings, database: str | None) -> URL:
    return URL.create(
        "mysql+pymysql",
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database=database,
        query={"charset": "utf8mb4"},
    )


def _set_utc(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("SET time_zone = '+00:00'")
    cursor.close()


def execute_static(connection: Connection, statement: str) -> None:
    try:
        connection.exec_driver_sql(statement)
    except Exception as exc:
        if not is_already_exists(exc):
            raise


def apply_dev_schema(settings: Settings) -> Engine:
    script = SCHEMA_PATH.read_text(encoding="utf-8")
    statements = split_sql(script)
    server = create_engine(mysql_url(settings, database="mysql"), pool_pre_ping=True)
    database = create_engine(mysql_url(settings, database=settings.db_name), pool_pre_ping=True)
    event.listen(database, "connect", _set_utc)
    with server.begin() as server_connection:
        execute_static(server_connection, statements[0])
    with database.begin() as database_connection:
        for statement in statements[1:]:
            execute_static(database_connection, statement)
    server.dispose()
    return database


def assert_prod_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("url_mappings"):
        raise RuntimeError("url_mappings is missing")
    names = {column["name"] for column in inspector.get_columns("url_mappings")}
    if not REQUIRED_COLUMNS <= names:
        raise RuntimeError("url_mappings does not match SYSTEM_DESIGN.md")


def sqlite_test_engine() -> Engine:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sequence = Table(
        "sqlite_sequence",
        MetaData(),
        Column("name", String, primary_key=True),
        Column("seq", Integer),
    )
    with engine.begin() as connection:
        connection.execute(sequence.delete().where(sequence.c.name == "url_mappings"))
        connection.execute(sequence.insert().values(name="url_mappings", seq=TEST_ID_START - 1))
    return engine


def build_engine(settings: Settings) -> Engine:
    if settings.app_env == "test":
        return sqlite_test_engine()
    if settings.app_env == "prod":
        # PyMySQL uses TLS when the server offers it, and continues without TLS otherwise.
        engine = create_engine(mysql_url(settings, database=settings.db_name), pool_pre_ping=True)
        event.listen(engine, "connect", _set_utc)
        assert_prod_schema(engine)
        return engine
    return apply_dev_schema(settings)
