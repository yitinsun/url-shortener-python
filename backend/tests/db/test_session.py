import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

from urlshortener.db.session import (
    SCHEMA_PATH,
    assert_prod_schema,
    is_already_exists,
    split_sql,
    sqlite_test_engine,
)
from urlshortener.models.url_mapping import UrlMapping
from urlshortener.repositories.url_mapping_repository import UrlMappingRepository
from sqlalchemy.orm import sessionmaker

from urlshortener.clock import utcnow
from datetime import timedelta


def test_schema_file_sets_the_pivot_autoincrement():
    script = SCHEMA_PATH.read_text(encoding="utf-8")
    statements = split_sql(script)
    assert "utf8mb4" in statements[0]
    assert "AUTO_INCREMENT=56800235" in statements[1]
    assert "idx_long_url" in statements[1]


def test_already_exists_errors_are_recognized():
    class Exists(Exception):
        def __init__(self):
            super().__init__("table already exists")
            self.args = (1050, "table already exists")

    assert is_already_exists(Exists())
    assert not is_already_exists(RuntimeError("connection refused"))


def test_sqlite_ids_start_at_the_pivot():
    engine = sqlite_test_engine()
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    row = UrlMappingRepository(session).insert("https://example.com/first", utcnow() + timedelta(days=1))
    assert row.id == 56800235
    assert_prod_schema(engine)
    session.close()


def test_prod_schema_check_rejects_a_database_without_the_table():
    engine = create_engine("sqlite://")
    with pytest.raises(RuntimeError, match="url_mappings is missing"):
        assert_prod_schema(engine)


def test_prod_schema_check_rejects_a_table_missing_columns():
    engine = create_engine("sqlite://")
    table = Table("url_mappings", MetaData(), Column("id", Integer, primary_key=True), Column("long_url", String))
    table.create(engine)
    with pytest.raises(RuntimeError, match="does not match"):
        assert_prod_schema(engine)
    assert UrlMapping.__tablename__ == "url_mappings"
