"""Startup DDL persists on SQLAlchemy 1.4 legacy and future connections."""
import os
import uuid

import pytest
from sqlalchemy import create_engine, inspect, text

from ckan import model
from ckanext.pages import db_init
from ckanext.pages.data_stories.db import utils as stories
from ckanext.pages.featured_viewers.db.utils import _add_column_if_not_exists


@pytest.fixture(params=[False, True], ids=['legacy', 'future'])
def database(request):
    url = os.environ.get('PAGES_SCHEMA_TEST_URL')
    if not url:
        pytest.skip('Set PAGES_SCHEMA_TEST_URL to an isolated PostgreSQL database')
    schema = 'pages_startup_' + uuid.uuid4().hex
    admin = create_engine(url)
    with admin.begin() as conn:
        conn.execute(text('CREATE SCHEMA ' + schema))
    engine = create_engine(url, future=request.param,
                           connect_args={'options': '-csearch_path=' + schema})
    try:
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as conn:
            conn.execute(text('DROP SCHEMA ' + schema + ' CASCADE'))
        admin.dispose()


@pytest.mark.parametrize('legacy_revisions', [False, True])
def test_pages_creation_and_columns_persist(database, monkeypatch, legacy_revisions):
    monkeypatch.setattr(model.meta, 'engine', database)
    db_init.create_pages_table()
    if legacy_revisions:
        with database.begin() as conn:
            conn.execute(text('ALTER TABLE ckanext_pages DROP COLUMN revisions'))
    db_init.ensure_all_columns_exist()
    columns = {column['name'] for column in inspect(database).get_columns('ckanext_pages')}
    assert {'revisions', 'submission_status', 'reviewed_by', 'featured'} <= columns
    db_init.create_pages_table()
    db_init.ensure_all_columns_exist()


@pytest.mark.parametrize('column', [
    'blocks_metadata', 'countries', 'paper_doi', 'paper_citation', 'uploaded_images',
    'partners', 'project_type', 'display_mode',
])
def test_story_columns_persist_and_repeat_safely(database, column):
    table = 'data_story_sections' if column == 'blocks_metadata' else 'data_stories'
    with database.begin() as conn:
        conn.execute(text('CREATE TABLE ' + table + ' (id TEXT PRIMARY KEY)'))
    ensure = getattr(stories, '_ensure_' + column + '_column')
    ensure(database)
    assert column in {item['name'] for item in inspect(database).get_columns(table)}
    ensure(database)


def test_featured_viewer_column_persists_with_both_connection_modes(database):
    with database.begin() as conn:
        conn.execute(text('CREATE TABLE featured_viewers (id TEXT PRIMARY KEY)'))
    _add_column_if_not_exists(database, 'featured_viewers', 'map_height', 'INTEGER')
    assert 'map_height' in {item['name'] for item in inspect(database).get_columns('featured_viewers')}
    _add_column_if_not_exists(database, 'featured_viewers', 'map_height', 'INTEGER')
