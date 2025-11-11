"""
Business logic for Data Stories

Provides validation, schemas, and workflow management.
"""

from ckanext.pages.data_stories.logic.validation import (
    validate_story_completeness,
    validate_terria_config,
    validate_dataset_link,
    validate_slug,
)

from ckanext.pages.data_stories.logic.schema import (
    data_story_schema,
    data_story_section_schema,
    data_story_dataset_schema,
    data_story_contributor_schema,
    data_story_comment_schema,
)

from ckanext.pages.data_stories.logic.workflow import (
    StoryWorkflow,
    can_transition,
    transition_state,
)

__all__ = [
    # Validation
    'validate_story_completeness',
    'validate_terria_config',
    'validate_dataset_link',
    'validate_slug',
    # Schemas
    'data_story_schema',
    'data_story_section_schema',
    'data_story_dataset_schema',
    'data_story_contributor_schema',
    'data_story_comment_schema',
    # Workflow
    'StoryWorkflow',
    'can_transition',
    'transition_state',
]
