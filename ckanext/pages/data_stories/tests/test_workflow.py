# encoding: utf-8
"""
Tests for Data Stories workflow state machine.
"""

import pytest

from ckan import model
from ckan.tests import factories, helpers

from ckanext.pages.data_stories.db.utils import init_tables
from ckanext.pages.data_stories.db.models import DataStory
from ckanext.pages.data_stories.logic.workflow import (
    StoryWorkflow,
    can_transition,
    get_allowed_transitions,
    transition_state,
)


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestStoryWorkflow:
    """Tests for story workflow state machine."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_workflow_initial_state(self):
        """Test that new stories start in draft state."""
        user = factories.User()

        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='New Story',
        )

        assert story['status'] == 'draft'

    def test_transition_draft_to_submitted(self):
        """Test transitioning from draft to submitted."""
        user = factories.User()

        # Create complete story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story',
        )

        # Add required sections
        for section_type in ['introduction', 'data_sources', 'methodology',
                            'spatial_analysis', 'conclusions']:
            helpers.call_action(
                'data_story_section_create',
                context={'user': user['name']},
                story_id=story['id'],
                section_type=section_type,
                content='Content',
            )

        # Transition to submitted
        updated = helpers.call_action(
            'data_story_submit',
            context={'user': user['name']},
            id=story['id'],
        )

        assert updated['status'] == 'submitted'

    def test_cannot_skip_states(self):
        """Test that states cannot be skipped."""
        user = factories.User()

        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story',
        )

        # Try to go directly from draft to published (should fail)
        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()

        can_skip = can_transition(story_obj, 'published')
        assert can_skip is False

    def test_get_allowed_transitions_from_draft(self):
        """Test getting allowed transitions from draft state."""
        user = factories.User()

        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Draft Story',
        )

        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()
        allowed = get_allowed_transitions(story_obj)

        assert 'submitted' in allowed
        assert 'published' not in allowed

    def test_get_allowed_transitions_from_submitted(self):
        """Test allowed transitions from submitted state."""
        user = factories.User()

        # Create and submit story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story',
        )

        # Add sections and submit
        for section_type in ['introduction', 'data_sources', 'methodology',
                            'spatial_analysis', 'conclusions']:
            helpers.call_action(
                'data_story_section_create',
                context={'user': user['name']},
                story_id=story['id'],
                section_type=section_type,
                content='Content',
            )

        helpers.call_action(
            'data_story_submit',
            context={'user': user['name']},
            id=story['id'],
        )

        # Check allowed transitions
        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()
        allowed = get_allowed_transitions(story_obj)

        assert 'under_review' in allowed
        assert 'draft' in allowed  # Can be rejected back to draft

    def test_workflow_from_draft_to_published(self):
        """Test complete workflow from draft to published."""
        author = factories.User()
        reviewer = factories.Sysadmin()

        # 1. Create draft story
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Complete Workflow Story',
        )
        assert story['status'] == 'draft'

        # Add required sections
        for section_type in ['introduction', 'data_sources', 'methodology',
                            'spatial_analysis', 'conclusions']:
            helpers.call_action(
                'data_story_section_create',
                context={'user': author['name']},
                story_id=story['id'],
                section_type=section_type,
                content='Content',
            )

        # 2. Submit for review
        story = helpers.call_action(
            'data_story_submit',
            context={'user': author['name']},
            id=story['id'],
        )
        assert story['status'] == 'submitted'

        # 3. Start review
        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()
        transition_state(story_obj, 'under_review', {'user': reviewer['id']})
        model.Session.commit()

        story = helpers.call_action('data_story_show', id=story['id'])
        assert story['status'] == 'under_review'

        # 4. Approve and publish
        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()
        transition_state(story_obj, 'published', {'user': reviewer['id']})
        model.Session.commit()

        story = helpers.call_action('data_story_show', id=story['id'])
        assert story['status'] == 'published'

    def test_reject_story_back_to_draft(self):
        """Test rejecting a submitted story back to draft."""
        author = factories.User()
        reviewer = factories.Sysadmin()

        # Create and submit story
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Story to Reject',
        )

        for section_type in ['introduction', 'data_sources', 'methodology',
                            'spatial_analysis', 'conclusions']:
            helpers.call_action(
                'data_story_section_create',
                context={'user': author['name']},
                story_id=story['id'],
                section_type=section_type,
                content='Content',
            )

        story = helpers.call_action(
            'data_story_submit',
            context={'user': author['name']},
            id=story['id'],
        )

        # Reject back to draft
        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()
        transition_state(story_obj, 'draft', {'user': reviewer['id']})
        model.Session.commit()

        story = helpers.call_action('data_story_show', id=story['id'])
        assert story['status'] == 'draft'

    def test_archive_published_story(self):
        """Test archiving a published story."""
        user = factories.Sysadmin()

        # Create and manually publish story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story to Archive',
        )

        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()
        story_obj.status = 'published'
        model.Session.commit()

        # Archive story
        updated = helpers.call_action(
            'data_story_archive',
            context={'user': user['name']},
            id=story['id'],
        )

        assert updated['status'] == 'archived'

    def test_cannot_modify_archived_story(self):
        """Test that archived stories cannot be modified."""
        user = factories.Sysadmin()

        # Create and archive story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Archived Story',
        )

        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()
        story_obj.status = 'archived'
        model.Session.commit()

        # Try to update (should fail)
        from ckan.plugins import toolkit
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                'data_story_update',
                context={'user': user['name']},
                id=story['id'],
                title='Cannot Update',
            )


class TestWorkflowUtilityFunctions:
    """Tests for workflow utility functions."""

    def test_can_transition_valid(self):
        """Test checking valid transitions."""
        # Create a mock story object
        class MockStory:
            status = 'draft'

        story = MockStory()

        # Draft can go to submitted
        assert can_transition(story, 'submitted') is True

        # Draft cannot go to published
        assert can_transition(story, 'published') is False

    def test_can_transition_invalid_state(self):
        """Test checking transition to invalid state."""
        class MockStory:
            status = 'draft'

        story = MockStory()

        # Cannot transition to non-existent state
        assert can_transition(story, 'invalid_state') is False

    def test_get_allowed_transitions_returns_list(self):
        """Test that get_allowed_transitions returns a list."""
        class MockStory:
            status = 'draft'

        story = MockStory()
        allowed = get_allowed_transitions(story)

        assert isinstance(allowed, list)
        assert len(allowed) > 0

    def test_workflow_states_are_valid(self):
        """Test that all workflow states are defined."""
        workflow = StoryWorkflow()

        required_states = ['draft', 'submitted', 'under_review', 'published', 'archived']

        for state in required_states:
            assert state in workflow.STATES


class TestWorkflowPermissions:
    """Tests for workflow-related permissions."""

    @pytest.mark.usefixtures('clean_db', 'with_plugins')
    def test_only_author_can_submit(self):
        """Test that only story author can submit."""
        init_tables(model.meta.engine)

        author = factories.User()
        other_user = factories.User()

        # Create complete story
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Story',
        )

        for section_type in ['introduction', 'data_sources', 'methodology',
                            'spatial_analysis', 'conclusions']:
            helpers.call_action(
                'data_story_section_create',
                context={'user': author['name']},
                story_id=story['id'],
                section_type=section_type,
                content='Content',
            )

        # Author can submit
        updated = helpers.call_action(
            'data_story_submit',
            context={'user': author['name']},
            id=story['id'],
        )
        assert updated['status'] == 'submitted'

        # Reset to draft for second test
        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()
        story_obj.status = 'draft'
        model.Session.commit()

        # Other user cannot submit
        from ckan.plugins import toolkit
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_submit',
                context={'user': other_user['name']},
                id=story['id'],
            )

    @pytest.mark.usefixtures('clean_db', 'with_plugins')
    def test_sysadmin_can_approve(self):
        """Test that sysadmin can approve stories."""
        init_tables(model.meta.engine)

        author = factories.User()
        sysadmin = factories.Sysadmin()

        # Create and submit story
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Story',
        )

        for section_type in ['introduction', 'data_sources', 'methodology',
                            'spatial_analysis', 'conclusions']:
            helpers.call_action(
                'data_story_section_create',
                context={'user': author['name']},
                story_id=story['id'],
                section_type=section_type,
                content='Content',
            )

        helpers.call_action(
            'data_story_submit',
            context={'user': author['name']},
            id=story['id'],
        )

        # Sysadmin can approve
        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()
        story_obj.status = 'under_review'
        model.Session.commit()

        updated = helpers.call_action(
            'data_story_approve',
            context={'user': sysadmin['name']},
            id=story['id'],
        )

        assert updated['status'] == 'published'


class TestWorkflowTimestamps:
    """Tests for workflow-related timestamps."""

    @pytest.mark.usefixtures('clean_db', 'with_plugins')
    def test_submission_date_set_on_submit(self):
        """Test that submission_date is set when submitting."""
        init_tables(model.meta.engine)

        user = factories.User()

        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story',
        )

        for section_type in ['introduction', 'data_sources', 'methodology',
                            'spatial_analysis', 'conclusions']:
            helpers.call_action(
                'data_story_section_create',
                context={'user': user['name']},
                story_id=story['id'],
                section_type=section_type,
                content='Content',
            )

        # Before submit
        assert story.get('submission_date') is None

        # After submit
        updated = helpers.call_action(
            'data_story_submit',
            context={'user': user['name']},
            id=story['id'],
        )

        assert updated['submission_date'] is not None

    @pytest.mark.usefixtures('clean_db', 'with_plugins')
    def test_published_date_set_on_publish(self):
        """Test that published_at is set when publishing."""
        init_tables(model.meta.engine)

        sysadmin = factories.Sysadmin()

        story = helpers.call_action(
            'data_story_create',
            context={'user': sysadmin['name']},
            title='Story',
        )

        # Manually set to under_review
        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()
        story_obj.status = 'under_review'
        model.Session.commit()

        # Approve
        updated = helpers.call_action(
            'data_story_approve',
            context={'user': sysadmin['name']},
            id=story['id'],
        )

        assert updated['published_at'] is not None
