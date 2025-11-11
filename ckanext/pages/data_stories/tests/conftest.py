# encoding: utf-8
"""
Pytest configuration and fixtures for Data Stories tests.
"""

import pytest

from ckan import model
from ckan.tests import factories


@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    """Clean database before each test."""
    reset_db()
    migrate_db_for('pages')


@pytest.fixture
def with_plugins():
    """Load required plugins for tests."""
    # Plugins will be loaded from test.ini
    pass


@pytest.fixture
def sample_story(clean_db):
    """Create a sample story for testing."""
    user = factories.User()

    from ckan.tests import helpers

    story = helpers.call_action(
        'data_story_create',
        context={'user': user['name']},
        title='Sample Story',
        abstract='A sample story for testing',
        research_question='Test question?',
    )

    return story, user


@pytest.fixture
def complete_story(clean_db):
    """Create a complete story with all required sections."""
    user = factories.User()

    from ckan.tests import helpers

    story = helpers.call_action(
        'data_story_create',
        context={'user': user['name']},
        title='Complete Story',
    )

    # Add all required sections
    sections = []
    for section_type in ['introduction', 'data_sources', 'methodology',
                        'spatial_analysis', 'conclusions']:
        section = helpers.call_action(
            'data_story_section_create',
            context={'user': user['name']},
            story_id=story['id'],
            section_type=section_type,
            title=section_type.replace('_', ' ').title(),
            content=f'Content for {section_type} section.',
        )
        sections.append(section)

    return story, sections, user


@pytest.fixture
def story_with_dataset(clean_db):
    """Create a story with a linked dataset."""
    user = factories.User()
    dataset = factories.Dataset(user=user)

    from ckan.tests import helpers

    story = helpers.call_action(
        'data_story_create',
        context={'user': user['name']},
        title='Story with Dataset',
    )

    link = helpers.call_action(
        'data_story_dataset_link',
        context={'user': user['name']},
        story_id=story['id'],
        dataset_id=dataset['id'],
        relationship_type='primary',
    )

    return story, dataset, link, user


@pytest.fixture
def story_with_contributors(clean_db):
    """Create a story with contributors."""
    author = factories.User()
    contributor = factories.User()

    from ckan.tests import helpers

    story = helpers.call_action(
        'data_story_create',
        context={'user': author['name']},
        title='Collaborative Story',
    )

    contrib = helpers.call_action(
        'data_story_contributor_add',
        context={'user': author['name']},
        story_id=story['id'],
        user_id=contributor['id'],
        role='co-author',
    )

    return story, author, contributor, contrib


@pytest.fixture
def organization_story(clean_db):
    """Create a story within an organization."""
    org = factories.Organization()
    user = factories.User()

    from ckan.tests import helpers

    # Add user to org
    helpers.call_action(
        'member_create',
        id=org['id'],
        object=user['id'],
        object_type='user',
        capacity='editor',
    )

    story = helpers.call_action(
        'data_story_create',
        context={'user': user['name']},
        title='Organization Story',
        organization_id=org['id'],
    )

    return story, org, user
