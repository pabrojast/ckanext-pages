"""PostgreSQL regressions for startup while a database backup is running."""
import os
import uuid

import pytest
from sqlalchemy import create_engine, event, inspect, text

from ckanext.pages.featured_viewers.db.utils import _add_column_if_not_exists


@pytest.fixture
def database():
    url = os.environ.get('PAGES_SCHEMA_TEST_URL')
    if not url:
        pytest.skip('Set PAGES_SCHEMA_TEST_URL to an isolated PostgreSQL database')
    engine = create_engine(url, connect_args={'options': '-c statement_timeout=1000'})
    table = 'pages_schema_' + uuid.uuid4().hex
    with engine.begin() as conn:
        conn.execute(text(f'CREATE TABLE {table} (initiative VARCHAR(100))'))
    try:
        yield engine, table
    finally:
        with engine.begin() as conn:
            conn.execute(text(f'DROP TABLE {table}'))
        engine.dispose()


def test_existing_column_does_not_request_exclusive_lock_during_backup(database):
    engine, table = database
    statements = []

    @event.listens_for(engine, 'before_cursor_execute')
    def record(_conn, _cursor, statement, _params, _context, _many):
        statements.append(statement)

    # pg_dump holds ACCESS SHARE locks for the life of its snapshot.
    with engine.connect() as backup:
        transaction = backup.begin()
        backup.execute(text(f'LOCK TABLE {table} IN ACCESS SHARE MODE'))
        try:
            _add_column_if_not_exists(engine, table, 'initiative', 'VARCHAR(100)')
        finally:
            transaction.rollback()
    assert not any(sql.lstrip().upper().startswith('ALTER TABLE') for sql in statements)


def test_missing_column_is_committed_and_second_start_is_safe(database):
    engine, table = database
    _add_column_if_not_exists(engine, table, 'map_height', 'INTEGER')
    assert 'map_height' in {column['name'] for column in inspect(engine).get_columns(table)}
    _add_column_if_not_exists(engine, table, 'map_height', 'INTEGER')
