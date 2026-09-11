"""Migration integration tests with SQLite and a fake file uploader."""
import base64
import io
import json
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from click.testing import CliRunner
from PIL import Image
from sqlalchemy.orm import sessionmaker

from ckanext.pages.commands import rapid_response_images as migration


@pytest.fixture
def migration_db(monkeypatch):
    table = sa.Table('pages', sa.MetaData(),
                     sa.Column('id', sa.String, primary_key=True),
                     sa.Column('name', sa.String), sa.Column('page_type', sa.String),
                     sa.Column('content', sa.Text), sa.Column('extras', sa.Text),
                     sa.Column('revisions', sa.JSON), sa.Column('modified', sa.String))
    engine = sa.create_engine('sqlite://')
    table.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    monkeypatch.setattr(migration, 'Page', SimpleNamespace(
        __table__=table, id=table.c.id, name=table.c.name, page_type=table.c.page_type))
    monkeypatch.setattr(migration, 'model', SimpleNamespace(Session=session))
    monkeypatch.setattr(migration, 'tk', SimpleNamespace(config={'ckan.site_url': 'https://example.test'}))
    stream = io.BytesIO()
    Image.new('RGB', (2000, 1000), 'blue').save(stream, 'JPEG')
    uri = 'data:image/jpeg;base64,' + base64.b64encode(stream.getvalue()).decode()
    html = '<p class="ql-align-center"><img src="' + uri + '"></p>'
    row = dict(id='page-1', name='event', page_type='rapid-response', content=html,
               extras=json.dumps({'blocks': [{'type': 'text', 'content': html}]}),
               revisions={'r1': {'content': html, 'created': '2026-09-01', 'current': True}},
               modified='2026-09-11')
    session.execute(table.insert().values(**row))
    session.commit()
    uploads = []

    def upload(data, extension, mime):
        uploads.append(data)
        return 'https://example.test/assets/photo.' + extension

    monkeypatch.setattr(migration, 'upload_display', upload)
    monkeypatch.setattr(migration, 'verify_asset', lambda url, data: None)
    yield session, table, row, uploads
    session.close()
    engine.dispose()


def test_dry_run_has_no_file_or_database_writes(migration_db, tmp_path):
    _, _, before, uploads = migration_db
    result = CliRunner().invoke(migration.optimize_rapid_response_images, [])
    assert result.exit_code == 0, result.output
    assert migration.snapshot('page-1') == before
    assert not uploads
    assert not list(tmp_path.iterdir())


def test_conversion_deduplicates_preserves_metadata_and_is_idempotent(migration_db, tmp_path):
    _, _, before, uploads = migration_db
    args = ['--apply', '--backup-dir', str(tmp_path)]
    result = CliRunner().invoke(migration.optimize_rapid_response_images, args)
    assert result.exit_code == 0, result.output
    after = migration.snapshot('page-1')
    assert len(uploads) == 1
    assert 'data:image/' not in json.dumps(after)
    assert after['modified'] == before['modified']
    assert after['revisions']['r1']['created'] == before['revisions']['r1']['created']
    assert after['revisions']['r1']['current'] is True
    assert 'ql-align-center' in after['content']
    result = CliRunner().invoke(migration.optimize_rapid_response_images, args)
    assert result.exit_code == 0, result.output
    assert migration.snapshot('page-1') == after
    assert len(uploads) == 1


def test_restore_roundtrip_and_repeated_restore(migration_db, tmp_path):
    _, _, before, _ = migration_db
    runner = CliRunner()
    assert runner.invoke(migration.optimize_rapid_response_images,
                         ['--apply', '--backup-dir', str(tmp_path)]).exit_code == 0
    args = ['--apply', '--restore', str(tmp_path / 'manifest.json')]
    result = runner.invoke(migration.optimize_rapid_response_images, args)
    assert result.exit_code == 0, result.output
    assert migration.snapshot('page-1') == before
    assert runner.invoke(migration.optimize_rapid_response_images, args).exit_code == 0


def test_failed_upload_keeps_entire_record(migration_db, tmp_path, monkeypatch):
    _, _, before, _ = migration_db
    def fail(*args):
        raise IOError('Storage unavailable')
    monkeypatch.setattr(migration, 'upload_display', fail)
    result = CliRunner().invoke(migration.optimize_rapid_response_images,
                               ['--apply', '--backup-dir', str(tmp_path)])
    assert result.exit_code == 1
    assert migration.snapshot('page-1') == before
    assert (tmp_path / 'page-1.before.json.gz').is_file()


def test_concurrent_edit_prevents_conversion(migration_db, tmp_path, monkeypatch):
    session, table, before, _ = migration_db
    def upload(*args):
        session.execute(table.update().values(modified='new edit'))
        session.commit()
        return 'https://example.test/photo.jpg'
    monkeypatch.setattr(migration, 'upload_display', upload)
    result = CliRunner().invoke(migration.optimize_rapid_response_images,
                               ['--apply', '--backup-dir', str(tmp_path)])
    assert result.exit_code == 1
    current = migration.snapshot('page-1')
    assert current['modified'] == 'new edit'
    assert current['content'] == before['content']


def test_restore_refuses_to_overwrite_later_edits(migration_db, tmp_path):
    session, table, _, _ = migration_db
    runner = CliRunner()
    assert runner.invoke(migration.optimize_rapid_response_images,
                         ['--apply', '--backup-dir', str(tmp_path)]).exit_code == 0
    session.execute(table.update().values(content='<p>New content</p>'))
    session.commit()
    result = runner.invoke(migration.optimize_rapid_response_images,
                           ['--apply', '--restore', str(tmp_path / 'manifest.json')])
    assert result.exit_code == 1
    assert migration.snapshot('page-1')['content'] == '<p>New content</p>'


def test_restore_rejects_corrupt_backup(migration_db, tmp_path):
    runner = CliRunner()
    assert runner.invoke(migration.optimize_rapid_response_images,
                         ['--apply', '--backup-dir', str(tmp_path)]).exit_code == 0
    path = tmp_path / 'page-1.before.json.gz'
    backup = migration.read_json(path, True)
    backup['content'] = 'tampered'
    migration.atomic_json(path, backup, True)
    result = runner.invoke(migration.optimize_rapid_response_images,
                           ['--apply', '--restore', str(tmp_path / 'manifest.json')])
    assert result.exit_code == 1
    assert 'checksum mismatch' in result.output
