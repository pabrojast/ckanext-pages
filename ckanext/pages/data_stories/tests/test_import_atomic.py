"""Real PostgreSQL import transactions, isolated in a disposable schema.

Run with PAGES_IMPORT_TEST_URL and --noconftest; no CKAN clean_db fixture.
"""
import copy
import datetime
import os
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from ckan import model
from ckan.plugins import toolkit as tk
from ckanext.pages.data_stories.actions.import_export import (
    data_story_bulk_import, data_story_export, data_story_import,
)
from ckanext.pages.data_stories.auth import permissions
from ckanext.pages.data_stories.db.models import (
    DataStory, DataStoryContributor, DataStoryDataset, DataStoryRevision,
    DataStorySection,
)


@pytest.fixture
def database(monkeypatch):
    url = os.environ.get('PAGES_IMPORT_TEST_URL')
    if not url:
        pytest.skip('PAGES_IMPORT_TEST_URL must point to isolated PostgreSQL')
    schema = 'story_import_' + uuid.uuid4().hex
    admin_engine = create_engine(url)
    with admin_engine.begin() as conn:
        conn.execute(text('CREATE SCHEMA ' + schema))
    engine = create_engine(url, connect_args={'options': '-csearch_path=' + schema})
    model.init_model(engine)
    model.meta.metadata.create_all(engine)

    # Usar las reglas reales; solo reemplazar el registro global de plugins.
    def check_access(action, context, data):
        if not getattr(permissions, action)(context, data)['success']:
            raise tk.NotAuthorized('Sysadmin required')
        return True

    monkeypatch.setattr(tk, 'check_access', check_access)
    users = {
        name: model.User(name=name, sysadmin=name == 'admin')
        for name in ('admin', 'author', 'visitor')
    }
    model.Session.add_all(list(users.values()))
    model.Session.commit()
    yield users
    model.Session.remove()
    engine.dispose()
    with admin_engine.begin() as conn:
        conn.execute(text('DROP SCHEMA ' + schema + ' CASCADE'))
    admin_engine.dispose()


def payload(title='Original', slug='published-story'):
    return {'format_version': '1.0', 'story': {
        'title': title, 'slug': slug, 'status': 'published', 'display_mode': 'slides',
        'sections': [{'title': title + ' chapter', 'section_type': 'text',
                      'content': '<p>' + title + '</p>', 'order_index': 0,
                      'blocks_metadata': [{'type': 'text', 'content': title}]}],
        'contributors': [{'name': title + ' contributor'}],
    }}


def seeded_story(database):
    result = data_story_import({'user': 'admin'}, {
        'data': payload(), 'owner_user_id': database['author'].id,
        'preserve_status': True,
    })
    story = DataStory.get(id=result['id'])
    story.view_count = 42
    story.created_at = datetime.datetime(2024, 1, 1)
    story.published_at = datetime.datetime(2024, 2, 1)
    revision = DataStoryRevision(id=str(uuid.uuid4()), story_id=story.id,
                                 version=1, changed_by=database['author'].id,
                                 content_snapshot={'title': story.title})
    model.Session.add(revision)
    model.Session.commit()
    return result


def test_overwrite_keeps_url_identity_history_and_replaces_content(database):
    original = seeded_story(database)
    first_section = original['sections'][0]['id']
    for title in ('Updated', 'Updated again'):
        result = data_story_import({'user': 'admin'}, {
            'data': payload(title), 'slug_conflict': 'overwrite', 'preserve_status': True,
        })
        assert result['id'] == original['id']
        assert result['slug'] == original['slug']
        assert result['status'] == 'published' and result['is_public']
        assert result['author_id'] == database['author'].id
        assert result['view_count'] == 42
        assert result['created_at'].startswith('2024-01-01')
        assert result['published_at'].startswith('2024-02-01')
        assert len(DataStorySection.all(story_id=result['id'])) == 1
        assert len(DataStoryContributor.all(story_id=result['id'])) == 1
    assert result['version'] == 3
    assert DataStorySection.get(id=first_section) is None
    assert len(DataStoryRevision.all(story_id=result['id'])) == 1
    assert model.Session.query(DataStory).count() == 1
    exported = data_story_export({'user': 'admin'}, {'id': result['id']})
    expected_blocks = payload('Updated again')['story']['sections'][0]['blocks_metadata']
    assert exported['story']['sections'][0]['blocks_metadata'] == expected_blocks


def test_overwrite_replaces_dataset_links(database):
    original = seeded_story(database)
    package = model.Package(name='story-data', title='Story data')
    model.Session.add(package)
    model.Session.commit()
    data = payload('With dataset')
    data['story']['dataset_references'] = [{'dataset_name': package.name}]
    for _ in range(2):
        data_story_import({'user': 'admin'}, {
            'data': data, 'slug_conflict': 'overwrite', 'preserve_status': True,
        })
        assert len(DataStoryDataset.all(story_id=original['id'])) == 1
    data_story_import({'user': 'admin'}, {
        'data': payload('No dataset'), 'slug_conflict': 'overwrite',
    })
    assert DataStoryDataset.all(story_id=original['id']) == []


def test_failed_overwrite_leaves_published_story_and_children_unchanged(database):
    original = seeded_story(database)
    invalid = payload('Must roll back')
    invalid['story']['sections'][0]['section_type'] = None
    with pytest.raises(IntegrityError):
        data_story_import({'user': 'admin'}, {
            'data': invalid, 'slug_conflict': 'overwrite', 'preserve_status': True,
        })
    restored = DataStory.get(id=original['id'])
    assert restored.title == 'Original'
    assert restored.status == 'published' and restored.is_public
    assert restored.version == 1 and restored.view_count == 42
    assert DataStorySection.all(story_id=restored.id)[0].id == original['sections'][0]['id']
    assert DataStoryContributor.all(story_id=restored.id)[0].name == 'Original contributor'


@pytest.mark.parametrize('user', [None, 'author', 'visitor'])
def test_overwrite_requires_sysadmin_even_for_original_author(database, user):
    original = seeded_story(database)
    with pytest.raises(tk.NotAuthorized):
        data_story_import({'user': user}, {
            'data': payload('Unauthorized'), 'slug_conflict': 'overwrite',
        })
    assert DataStory.get(id=original['id']).title == 'Original'


def test_bulk_failed_overwrite_preserves_original_and_commits_other_stories(database):
    original = seeded_story(database)
    invalid = copy.deepcopy(payload('Invalid')['story'])
    invalid['sections'][0]['section_type'] = None
    stories = [payload('First', 'first')['story'], invalid,
               payload('Last', 'last')['story']]
    result = data_story_bulk_import({'user': 'admin'}, {
        'data': {'format_version': '1.0', 'stories': stories},
        'slug_conflict': 'overwrite', 'preserve_status': True,
    })
    assert result['total_imported'] == 2 and result['total_errors'] == 1
    assert DataStory.get(id=original['id']).title == 'Original'
    assert DataStory.get(slug='first').status == 'published'
    assert DataStory.get(slug='last').status == 'published'
    assert DataStorySection.all(story_id=original['id'])[0].id == original['sections'][0]['id']


def test_rename_and_error_conflicts_remain_available(database):
    original = seeded_story(database)
    renamed = data_story_import({'user': 'admin'}, {'data': payload('Copy')})
    assert renamed['id'] != original['id']
    assert renamed['slug'] == 'published-story-1'
    with pytest.raises(tk.ValidationError):
        data_story_import({'user': 'admin'}, {
            'data': payload('Must not replace'), 'slug_conflict': 'error',
        })
    assert DataStory.get(id=original['id']).title == 'Original'


def test_bulk_can_overwrite_same_slug_repeatedly(database):
    original = seeded_story(database)
    result = data_story_bulk_import({'user': 'admin'}, {
        'data': {'format_version': '1.0', 'stories': [
            payload('First revision')['story'], payload('Final revision')['story'],
        ]},
        'slug_conflict': 'overwrite', 'preserve_status': True,
    })
    assert result['total_imported'] == 2 and result['total_errors'] == 0
    assert all(item['id'] == original['id'] for item in result['imported'])
    story = DataStory.get(id=original['id'])
    assert story.title == 'Final revision' and story.version == 3
    assert len(DataStorySection.all(story_id=story.id)) == 1
