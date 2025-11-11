"""
Dataset linking actions for data stories.

Handles linking and unlinking CKAN datasets to stories.
"""

import datetime
import logging

from ckan import model
import ckan.plugins.toolkit as tk

from ckanext.pages.data_stories.db.models import DataStory, DataStoryDataset
from ckanext.pages.data_stories.db.utils import make_uuid, table_dictize, dictize_datasets
from ckanext.pages.data_stories.logic.validation import validate_dataset_link

log = logging.getLogger(__name__)


def data_story_link_dataset(context, data_dict):
    """
    Link a dataset to a data story.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - story_id: Story ID (required)
            - dataset_id: CKAN package ID (required)
            - relationship_type: Type of relationship (optional)
            - description: Description of relationship (optional)
            - order_index: Display order (optional)

    Returns:
        Dict with dataset link data

    Raises:
        NotFound: If story or dataset doesn't exist
        NotAuthorized: If user lacks permission
        ValidationError: If validation fails
    """
    log.info("[DATA_STORY_LINK_DATASET] Linking dataset")

    # Check authorization
    tk.check_access('data_story_link_dataset', context, data_dict)

    # Get parameters
    story_id = data_dict.get('story_id')
    dataset_id = data_dict.get('dataset_id')

    if not story_id:
        raise tk.ValidationError({'story_id': ['Story ID is required']})

    if not dataset_id:
        raise tk.ValidationError({'dataset_id': ['Dataset ID is required']})

    # Validate story exists
    story = DataStory.get(id=story_id)
    if not story:
        raise tk.ObjectNotFound(f"Story not found: {story_id}")

    # Validate dataset can be linked
    is_valid, error_msg = validate_dataset_link(dataset_id, story_id, context)
    if not is_valid:
        raise tk.ValidationError({'dataset_id': [error_msg]})

    # Auto-calculate order_index if not provided
    order_index = data_dict.get('order_index')
    if order_index is None:
        existing_links = DataStoryDataset.all(story_id=story_id)
        if existing_links:
            max_order = max(link.order_index or 0 for link in existing_links)
            order_index = max_order + 1
        else:
            order_index = 0

    # Create link
    link = DataStoryDataset()
    link.id = make_uuid()
    link.story_id = story_id
    link.dataset_id = dataset_id
    link.relationship_type = data_dict.get('relationship_type', 'primary')
    link.description = data_dict.get('description', '')
    link.order_index = order_index
    link.created_at = datetime.datetime.utcnow()

    # Save
    link.save()
    session = context.get('session', model.Session)
    session.add(link)

    # Update story timestamp
    story.updated_at = datetime.datetime.utcnow()
    session.add(story)

    session.commit()

    log.info(f"[DATA_STORY_LINK_DATASET] Linked dataset {dataset_id} to story {story_id}")

    # Convert to dict
    link_dict = table_dictize(link, context)

    # Add dataset info
    try:
        dataset = tk.get_action('package_show')(context, {'id': dataset_id})
        link_dict['dataset'] = dataset
    except Exception as e:
        log.error(f"Error fetching dataset info: {str(e)}")

    return link_dict


def data_story_unlink_dataset(context, data_dict):
    """
    Unlink a dataset from a data story.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - story_id: Story ID (required)
            - dataset_id: CKAN package ID (required)

    Returns:
        Dict with success status

    Raises:
        NotFound: If link doesn't exist
        NotAuthorized: If user lacks permission
    """
    log.info("[DATA_STORY_UNLINK_DATASET] Unlinking dataset")

    # Check authorization
    tk.check_access('data_story_unlink_dataset', context, data_dict)

    # Get parameters
    story_id = data_dict.get('story_id')
    dataset_id = data_dict.get('dataset_id')

    if not story_id:
        raise tk.ValidationError({'story_id': ['Story ID is required']})

    if not dataset_id:
        raise tk.ValidationError({'dataset_id': ['Dataset ID is required']})

    # Find link
    link = DataStoryDataset.get(story_id=story_id, dataset_id=dataset_id)

    if not link:
        raise tk.ObjectNotFound(f"Dataset link not found: story={story_id}, dataset={dataset_id}")

    # Delete link
    session = context.get('session', model.Session)
    session.delete(link)

    # Update story timestamp
    story = DataStory.get(id=story_id)
    if story:
        story.updated_at = datetime.datetime.utcnow()
        session.add(story)

    session.commit()

    log.info(f"[DATA_STORY_UNLINK_DATASET] Unlinked dataset {dataset_id} from story {story_id}")

    return {'success': True, 'unlinked': True}


def data_story_datasets(context, data_dict):
    """
    List datasets linked to a story.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - story_id: Story ID (required)
            - relationship_type: Filter by relationship type (optional)

    Returns:
        List of dataset link dicts with full dataset info

    Raises:
        NotFound: If story doesn't exist
        NotAuthorized: If user lacks permission
    """
    log.info("[DATA_STORY_DATASETS] Listing linked datasets")

    # Check authorization
    tk.check_access('data_story_datasets', context, data_dict)

    # Get story
    story_id = data_dict.get('story_id')
    if not story_id:
        raise tk.ValidationError({'story_id': ['Story ID is required']})

    story = DataStory.get(id=story_id)
    if not story:
        raise tk.ObjectNotFound(f"Story not found: {story_id}")

    # Build query
    query = model.Session.query(DataStoryDataset).autoflush(False)
    query = query.filter(DataStoryDataset.story_id == story_id)

    # Filter by relationship type if provided
    relationship_type = data_dict.get('relationship_type')
    if relationship_type:
        query = query.filter(DataStoryDataset.relationship_type == relationship_type)

    # Order by order_index
    query = query.order_by(DataStoryDataset.order_index)

    # Execute
    links = query.all()

    # Convert to dicts and add dataset info
    dataset_list = []

    for link in links:
        link_dict = table_dictize(link, context)

        # Get full dataset info
        try:
            dataset = tk.get_action('package_show')(context, {'id': link.dataset_id})
            link_dict['dataset'] = dataset
        except Exception as e:
            log.error(f"Error fetching dataset {link.dataset_id}: {str(e)}")
            link_dict['dataset'] = {'id': link.dataset_id, 'title': 'Unknown', 'error': str(e)}

        dataset_list.append(link_dict)

    log.info(f"[DATA_STORY_DATASETS] Returned {len(dataset_list)} linked datasets")

    return dataset_list
