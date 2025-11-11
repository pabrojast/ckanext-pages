# encoding: utf-8
"""
Tests for Data Stories database models.
"""

import pytest
from datetime import datetime

from ckan import model
from ckan.tests import factories, helpers

from ckanext.pages.data_stories.db.models import (
    DataStory,
    DataStorySection,
    DataStoryDataset,
    DataStoryContributor,
    DataStoryComment,
    DataStoryRevision,
)
from ckanext.pages.data_stories.db.utils import init_tables, make_uuid


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryModel:
    """Tests for DataStory model."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_create_story(self):
        """Test creating a basic story."""
        user = factories.User()

        story = DataStory()
        story.id = make_uuid()
        story.title = 'Test Story'
        story.slug = 'test-story'
        story.author_id = user['id']
        story.status = 'draft'

        model.Session.add(story)
        model.Session.commit()

        # Retrieve and verify
        retrieved = model.Session.query(DataStory).filter_by(slug='test-story').first()
        assert retrieved is not None
        assert retrieved.title == 'Test Story'
        assert retrieved.author_id == user['id']
        assert retrieved.status == 'draft'

    def test_story_relationships(self):
        """Test story relationships to sections, datasets, etc."""
        user = factories.User()

        # Create story
        story = DataStory()
        story.id = make_uuid()
        story.title = 'Story with Relationships'
        story.slug = 'story-relationships'
        story.author_id = user['id']
        story.status = 'draft'
        model.Session.add(story)
        model.Session.commit()

        # Add section
        section = DataStorySection()
        section.id = make_uuid()
        section.story_id = story.id
        section.section_type = 'introduction'
        section.title = 'Introduction'
        section.content = 'Test content'
        section.order_index = 0
        model.Session.add(section)
        model.Session.commit()

        # Verify relationship
        assert len(story.sections) == 1
        assert story.sections[0].title == 'Introduction'

    def test_story_slug_uniqueness(self):
        """Test that slugs must be unique."""
        user = factories.User()

        # Create first story
        story1 = DataStory()
        story1.id = make_uuid()
        story1.title = 'Test Story 1'
        story1.slug = 'unique-slug'
        story1.author_id = user['id']
        model.Session.add(story1)
        model.Session.commit()

        # Try to create second story with same slug
        story2 = DataStory()
        story2.id = make_uuid()
        story2.title = 'Test Story 2'
        story2.slug = 'unique-slug'
        story2.author_id = user['id']
        model.Session.add(story2)

        # Should raise IntegrityError
        with pytest.raises(Exception):
            model.Session.commit()

        model.Session.rollback()

    def test_story_status_default(self):
        """Test that default status is 'draft'."""
        user = factories.User()

        story = DataStory()
        story.id = make_uuid()
        story.title = 'Draft Story'
        story.slug = 'draft-story'
        story.author_id = user['id']
        # Don't set status explicitly

        model.Session.add(story)
        model.Session.commit()

        assert story.status == 'draft'


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStorySectionModel:
    """Tests for DataStorySection model."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_create_section(self):
        """Test creating a section."""
        user = factories.User()

        # Create story first
        story = DataStory()
        story.id = make_uuid()
        story.title = 'Test Story'
        story.slug = 'test-story-section'
        story.author_id = user['id']
        model.Session.add(story)
        model.Session.commit()

        # Create section
        section = DataStorySection()
        section.id = make_uuid()
        section.story_id = story.id
        section.section_type = 'methodology'
        section.title = 'Methodology'
        section.content = '## Methods\n\nWe used...'
        section.order_index = 0

        model.Session.add(section)
        model.Session.commit()

        # Retrieve and verify
        retrieved = model.Session.query(DataStorySection).filter_by(
            story_id=story.id
        ).first()
        assert retrieved is not None
        assert retrieved.section_type == 'methodology'
        assert retrieved.title == 'Methodology'

    def test_section_ordering(self):
        """Test section ordering."""
        user = factories.User()

        # Create story
        story = DataStory()
        story.id = make_uuid()
        story.title = 'Ordered Story'
        story.slug = 'ordered-story'
        story.author_id = user['id']
        model.Session.add(story)
        model.Session.commit()

        # Create sections in reverse order
        for i, section_type in enumerate(['conclusions', 'results', 'introduction']):
            section = DataStorySection()
            section.id = make_uuid()
            section.story_id = story.id
            section.section_type = section_type
            section.title = section_type.title()
            section.order_index = i
            model.Session.add(section)

        model.Session.commit()

        # Verify ordering
        sections = model.Session.query(DataStorySection).filter_by(
            story_id=story.id
        ).order_by(DataStorySection.order_index).all()

        assert len(sections) == 3
        assert sections[0].section_type == 'conclusions'
        assert sections[1].section_type == 'results'
        assert sections[2].section_type == 'introduction'

    def test_section_terria_config(self):
        """Test storing Terria configuration as JSON."""
        user = factories.User()

        # Create story
        story = DataStory()
        story.id = make_uuid()
        story.title = 'Terria Story'
        story.slug = 'terria-story'
        story.author_id = user['id']
        model.Session.add(story)
        model.Session.commit()

        # Create section with Terria config
        section = DataStorySection()
        section.id = make_uuid()
        section.story_id = story.id
        section.section_type = 'spatial_analysis'
        section.title = 'Spatial Analysis'
        section.terria_config = {
            'initSources': [
                {
                    'type': 'wms',
                    'url': 'https://example.com/wms',
                    'name': 'Test Layer'
                }
            ]
        }

        model.Session.add(section)
        model.Session.commit()

        # Retrieve and verify JSON
        retrieved = model.Session.query(DataStorySection).filter_by(id=section.id).first()
        assert retrieved.terria_config is not None
        assert 'initSources' in retrieved.terria_config
        assert len(retrieved.terria_config['initSources']) == 1


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryDatasetModel:
    """Tests for DataStoryDataset model."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_link_dataset(self):
        """Test linking a dataset to a story."""
        user = factories.User()
        dataset = factories.Dataset()

        # Create story
        story = DataStory()
        story.id = make_uuid()
        story.title = 'Story with Dataset'
        story.slug = 'story-dataset'
        story.author_id = user['id']
        model.Session.add(story)
        model.Session.commit()

        # Link dataset
        link = DataStoryDataset()
        link.id = make_uuid()
        link.story_id = story.id
        link.dataset_id = dataset['id']
        link.relationship_type = 'primary'

        model.Session.add(link)
        model.Session.commit()

        # Verify link
        retrieved = model.Session.query(DataStoryDataset).filter_by(
            story_id=story.id
        ).first()
        assert retrieved is not None
        assert retrieved.dataset_id == dataset['id']
        assert retrieved.relationship_type == 'primary'

    def test_dataset_uniqueness(self):
        """Test that a dataset can only be linked once per story."""
        user = factories.User()
        dataset = factories.Dataset()

        # Create story
        story = DataStory()
        story.id = make_uuid()
        story.title = 'Unique Dataset Story'
        story.slug = 'unique-dataset'
        story.author_id = user['id']
        model.Session.add(story)
        model.Session.commit()

        # Link dataset
        link1 = DataStoryDataset()
        link1.id = make_uuid()
        link1.story_id = story.id
        link1.dataset_id = dataset['id']
        link1.relationship_type = 'primary'
        model.Session.add(link1)
        model.Session.commit()

        # Try to link same dataset again
        link2 = DataStoryDataset()
        link2.id = make_uuid()
        link2.story_id = story.id
        link2.dataset_id = dataset['id']
        link2.relationship_type = 'supporting'
        model.Session.add(link2)

        # Should raise IntegrityError
        with pytest.raises(Exception):
            model.Session.commit()

        model.Session.rollback()


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryContributorModel:
    """Tests for DataStoryContributor model."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_add_contributor(self):
        """Test adding a contributor to a story."""
        author = factories.User()
        contributor = factories.User()

        # Create story
        story = DataStory()
        story.id = make_uuid()
        story.title = 'Collaborative Story'
        story.slug = 'collaborative'
        story.author_id = author['id']
        model.Session.add(story)
        model.Session.commit()

        # Add contributor
        contrib = DataStoryContributor()
        contrib.id = make_uuid()
        contrib.story_id = story.id
        contrib.user_id = contributor['id']
        contrib.role = 'co-author'

        model.Session.add(contrib)
        model.Session.commit()

        # Verify
        retrieved = model.Session.query(DataStoryContributor).filter_by(
            story_id=story.id
        ).first()
        assert retrieved is not None
        assert retrieved.user_id == contributor['id']
        assert retrieved.role == 'co-author'

    def test_external_contributor(self):
        """Test adding an external contributor without CKAN user."""
        author = factories.User()

        # Create story
        story = DataStory()
        story.id = make_uuid()
        story.title = 'External Contributor Story'
        story.slug = 'external-contrib'
        story.author_id = author['id']
        model.Session.add(story)
        model.Session.commit()

        # Add external contributor
        contrib = DataStoryContributor()
        contrib.id = make_uuid()
        contrib.story_id = story.id
        contrib.name = 'Jane Doe'
        contrib.email = 'jane@example.com'
        contrib.affiliation = 'University of Example'
        contrib.orcid = '0000-0002-1825-0097'
        contrib.role = 'data-provider'

        model.Session.add(contrib)
        model.Session.commit()

        # Verify
        retrieved = model.Session.query(DataStoryContributor).filter_by(
            story_id=story.id
        ).first()
        assert retrieved is not None
        assert retrieved.name == 'Jane Doe'
        assert retrieved.orcid == '0000-0002-1825-0097'


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryCommentModel:
    """Tests for DataStoryComment model."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_add_comment(self):
        """Test adding a comment to a story."""
        author = factories.User()
        reviewer = factories.User()

        # Create story
        story = DataStory()
        story.id = make_uuid()
        story.title = 'Story with Comments'
        story.slug = 'commented-story'
        story.author_id = author['id']
        model.Session.add(story)
        model.Session.commit()

        # Add comment
        comment = DataStoryComment()
        comment.id = make_uuid()
        comment.story_id = story.id
        comment.user_id = reviewer['id']
        comment.comment_text = 'Please clarify the methodology.'
        comment.comment_type = 'suggestion'

        model.Session.add(comment)
        model.Session.commit()

        # Verify
        retrieved = model.Session.query(DataStoryComment).filter_by(
            story_id=story.id
        ).first()
        assert retrieved is not None
        assert retrieved.comment_text == 'Please clarify the methodology.'
        assert retrieved.comment_type == 'suggestion'

    def test_threaded_comments(self):
        """Test threaded comments (replies)."""
        author = factories.User()
        reviewer = factories.User()

        # Create story
        story = DataStory()
        story.id = make_uuid()
        story.title = 'Threaded Story'
        story.slug = 'threaded'
        story.author_id = author['id']
        model.Session.add(story)
        model.Session.commit()

        # Add parent comment
        parent = DataStoryComment()
        parent.id = make_uuid()
        parent.story_id = story.id
        parent.user_id = reviewer['id']
        parent.comment_text = 'Main comment'
        model.Session.add(parent)
        model.Session.commit()

        # Add reply
        reply = DataStoryComment()
        reply.id = make_uuid()
        reply.story_id = story.id
        reply.user_id = author['id']
        reply.comment_text = 'Reply to comment'
        reply.parent_id = parent.id
        model.Session.add(reply)
        model.Session.commit()

        # Verify relationship
        parent_retrieved = model.Session.query(DataStoryComment).filter_by(
            id=parent.id
        ).first()
        assert len(parent_retrieved.replies) == 1
        assert parent_retrieved.replies[0].comment_text == 'Reply to comment'


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryRevisionModel:
    """Tests for DataStoryRevision model."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_create_revision(self):
        """Test creating a revision snapshot."""
        author = factories.User()

        # Create story
        story = DataStory()
        story.id = make_uuid()
        story.title = 'Versioned Story'
        story.slug = 'versioned'
        story.author_id = author['id']
        model.Session.add(story)
        model.Session.commit()

        # Create revision
        revision = DataStoryRevision()
        revision.id = make_uuid()
        revision.story_id = story.id
        revision.version = 1
        revision.snapshot = {
            'title': story.title,
            'status': story.status,
            'author_id': story.author_id,
        }
        revision.created_by = author['id']

        model.Session.add(revision)
        model.Session.commit()

        # Verify
        retrieved = model.Session.query(DataStoryRevision).filter_by(
            story_id=story.id
        ).first()
        assert retrieved is not None
        assert retrieved.version == 1
        assert 'title' in retrieved.snapshot
        assert retrieved.snapshot['title'] == 'Versioned Story'

    def test_multiple_revisions(self):
        """Test creating multiple revisions."""
        author = factories.User()

        # Create story
        story = DataStory()
        story.id = make_uuid()
        story.title = 'Multi-version Story'
        story.slug = 'multi-version'
        story.author_id = author['id']
        model.Session.add(story)
        model.Session.commit()

        # Create multiple revisions
        for version in range(1, 4):
            revision = DataStoryRevision()
            revision.id = make_uuid()
            revision.story_id = story.id
            revision.version = version
            revision.snapshot = {'version': version}
            revision.created_by = author['id']
            model.Session.add(revision)

        model.Session.commit()

        # Verify
        revisions = model.Session.query(DataStoryRevision).filter_by(
            story_id=story.id
        ).order_by(DataStoryRevision.version).all()

        assert len(revisions) == 3
        assert revisions[0].version == 1
        assert revisions[2].version == 3
