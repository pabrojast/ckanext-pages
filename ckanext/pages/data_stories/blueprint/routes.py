"""
Flask routes for Data Stories web interface.

Provides URL routes and view functions for the data stories web UI.
"""

import html
import json
import logging
import re

from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
import ckan.plugins.toolkit as tk
from ckan.common import g
from ckan import model

log = logging.getLogger(__name__)

# Create blueprint
data_stories_blueprint = Blueprint(
    'data_stories',
    __name__,
    url_prefix='/data-stories'
)

# Pattern to extract section fields from form data
_SECTION_FIELD_RE = re.compile(r'^sections\[(\d+)\]\[([^\]]+)\]$')


def _is_org_admin_any(user_obj):
    """Return True when user is admin in at least one active organization."""
    if not user_obj:
        return False

    membership = model.Session.query(model.Member.id).join(
        model.Group, model.Member.group_id == model.Group.id
    ).filter(
        model.Member.table_name == 'user',
        model.Member.table_id == user_obj.id,
        model.Member.capacity == 'admin',
        model.Member.state == 'active',
        model.Group.type == 'organization',
        model.Group.state == 'active'
    ).first()

    return bool(membership)


def _can_review_stories(user_obj):
    """Return True for sysadmins and organization admins."""
    if not user_obj:
        return False

    if getattr(user_obj, 'sysadmin', False):
        return True

    return _is_org_admin_any(user_obj)


# ============================================================================
# List and Discovery Routes
# ============================================================================

@data_stories_blueprint.route('/')
@data_stories_blueprint.route('/list')
def index():
    """
    List all published data stories.

    URL: /data-stories or /data-stories/list
    """
    log.info("[DATA_STORIES_ROUTE] Listing stories")

    context = _get_context()

    # Get parameters from query string
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    sort = request.args.get('sort', 'recent')
    status_filter = request.args.get('status')
    org_filter = request.args.get('organization')
    q = request.args.get('q', '')

    # Calculate offset
    offset = (page - 1) * limit

    # Build data_dict
    data_dict = {
        'limit': limit,
        'offset': offset,
        'sort': sort,
        'q': q,
    }

    # Add filters if provided
    # Default to 'published' status for public list, unless explicitly filtered
    if status_filter:
        data_dict['status'] = status_filter
    else:
        # Only show published stories by default in the public list
        data_dict['status'] = 'published'

    if org_filter:
        data_dict['organization_id'] = org_filter

    # Get stories - use ignore_auth for public listing of published stories
    # This allows anonymous users to see the list page
    list_context = dict(context)
    if not status_filter or status_filter == 'published':
        list_context['ignore_auth'] = True

    try:
        result = tk.get_action('data_story_list')(list_context, data_dict)
        stories = result['stories']
        total_count = result['count']
        facets = result.get('facets', {})
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to view stories'))
    except Exception as e:
        log.error(f"Error listing stories: {str(e)}")
        model.Session.rollback()
        stories = []
        total_count = 0
        facets = {}

    # Get user's draft stories if logged in and viewing published stories
    user_drafts = []
    if g.userobj and (not status_filter or status_filter == 'published'):
        try:
            drafts_result = tk.get_action('data_story_list')(context, {
                'status': 'draft',
                'author_id': g.userobj.id,
                'limit': 50,
            })
            user_drafts = drafts_result.get('stories', [])
        except Exception as e:
            log.warning(f"Error getting user drafts: {str(e)}")
            model.Session.rollback()

    # Calculate pagination
    total_pages = (total_count + limit - 1) // limit

    # Get featured stories if on first page
    featured_stories = []
    if page == 1:
        try:
            featured_result = tk.get_action('data_story_list')(context, {
                'is_featured': True,
                'status': 'published',
                'limit': 3,
            })
            featured_stories = featured_result['stories']
        except Exception as e:
            log.error(f"Error getting featured stories: {str(e)}")
            model.Session.rollback()

    # Get pending review count for reviewers (sysadmins and org admins)
    pending_count = 0
    can_review = _can_review_stories(g.userobj)
    if can_review:
        try:
            # Count submitted stories
            submitted_result = tk.get_action('data_story_list')(context, {
                'status': 'submitted',
                'limit': 0,
            })
            # Count under_review stories
            review_result = tk.get_action('data_story_list')(context, {
                'status': 'under_review',
                'limit': 0,
            })
            pending_count = submitted_result.get('count', 0) + review_result.get('count', 0)
        except Exception as e:
            log.warning(f"Error getting pending count: {str(e)}")
            model.Session.rollback()

    # Prepare template variables
    extra_vars = {
        'stories': stories,
        'featured_stories': featured_stories,
        'user_drafts': user_drafts,
        'total_count': total_count,
        'page': page,
        'total_pages': total_pages,
        'limit': limit,
        'sort': sort,
        'status_filter': status_filter,
        'org_filter': org_filter,
        'q': q,
        'facets': facets,
        'pending_count': pending_count,
        'can_review': can_review,
    }

    return render_template('data_stories/list.html', **extra_vars)


@data_stories_blueprint.route('/pending-review')
def pending_review():
    """
    List stories pending review (submitted or under_review).

    URL: /data-stories/pending-review
    """
    log.info("[DATA_STORIES_ROUTE] Listing stories pending review")

    context = _get_context()

    # Must be logged in
    if not g.userobj:
        flash(tk._('Please log in to view pending stories'), 'error')
        return redirect(url_for('user.login'))

    # Check if user has review permissions (sysadmins or org admins)
    if not _can_review_stories(g.userobj):
        flash(tk._('You do not have permission to review stories'), 'error')
        return redirect(url_for('data_stories.index'))

    # Get parameters
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    status_filter = request.args.get('status', 'all')

    # Calculate offset
    offset = (page - 1) * limit

    # Build base data_dict for listing stories
    base_data_dict = {
        'sort': 'recent',
    }

    # Get stories
    stories = []
    total_count = 0

    try:
        if status_filter in ['submitted', 'under_review']:
            data_dict = dict(base_data_dict)
            data_dict['status'] = status_filter
            data_dict['limit'] = limit
            data_dict['offset'] = offset
            result = tk.get_action('data_story_list')(context, data_dict)
            stories = result['stories']
            total_count = result['count']
        else:
            # Get both submitted and under_review without pagination, then page in-memory
            result_submitted = tk.get_action('data_story_list')(context, {
                **base_data_dict,
                'status': 'submitted'
            })
            result_review = tk.get_action('data_story_list')(context, {
                **base_data_dict,
                'status': 'under_review'
            })
            all_stories = result_submitted['stories'] + result_review['stories']
            total_count = result_submitted['count'] + result_review['count']

            # Sort by created_at descending
            all_stories.sort(key=lambda x: x.get('created_at', ''), reverse=True)

            # Apply pagination manually
            stories = all_stories[offset:offset + limit]

    except Exception as e:
        log.error(f"Error listing pending stories: {str(e)}")
        model.Session.rollback()
        stories = []
        total_count = 0

    # Calculate pagination
    total_pages = (total_count + limit - 1) // limit

    extra_vars = {
        'stories': stories,
        'total_count': total_count,
        'page': page,
        'total_pages': total_pages,
        'status_filter': status_filter,
    }

    return render_template('data_stories/pending_review.html', **extra_vars)


@data_stories_blueprint.route('/my-stories')
def my_stories():
    """
    List current user's data stories.

    URL: /data-stories/my-stories
    """
    log.info("[DATA_STORIES_ROUTE] Listing user's stories")

    context = _get_context()

    # Must be logged in
    if not g.userobj:
        flash(tk._('Please log in to view your stories'), 'error')
        return redirect(url_for('user.login'))

    # Get parameters
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    status_filter = request.args.get('status', 'all')

    # Calculate offset
    offset = (page - 1) * limit

    # Build data_dict
    data_dict = {
        'author_id': g.userobj.id,
        'limit': limit,
        'offset': offset,
        'sort': 'recent',
    }

    # Add status filter if not 'all'
    if status_filter != 'all':
        data_dict['status'] = status_filter

    # Get stories
    try:
        result = tk.get_action('data_story_list')(context, data_dict)
        stories = result['stories']
        total_count = result['count']
    except Exception as e:
        log.error(f"Error listing user stories: {str(e)}")
        model.Session.rollback()
        stories = []
        total_count = 0

    # Calculate pagination
    total_pages = (total_count + limit - 1) // limit

    extra_vars = {
        'stories': stories,
        'total_count': total_count,
        'page': page,
        'total_pages': total_pages,
        'status_filter': status_filter,
    }

    return render_template('data_stories/my_stories.html', **extra_vars)


# ============================================================================
# Create and Edit Routes
# ============================================================================

@data_stories_blueprint.route('/new', methods=['GET', 'POST'])
def create():
    """
    Create a new data story.

    URL: /data-stories/new
    """
    log.info("[DATA_STORIES_ROUTE] Creating new story")

    context = _get_context()

    # Must be logged in
    if not g.userobj:
        flash(tk._('Please log in to create a story'), 'error')
        return redirect(url_for('user.login'))

    # Check authorization
    try:
        tk.check_access('data_story_create', context, {})
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to create stories'))

    if request.method == 'POST':
        # Get form data
        data_dict = _extract_story_form_data(request.form)
        sections_data = _extract_sections_form_data(request.form)
        datasets_data = data_dict.get('datasets_data') or []
        draft_story_context = _build_story_context({**data_dict, 'sections': sections_data})

        try:
            # Create story
            story = tk.get_action('data_story_create')(context, data_dict)

        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary

            extra_vars = {
                'story': draft_story_context,
                'data': data_dict,
                'errors': errors,
                'error_summary': error_summary,
                'is_new': True,
                'datasets_data_json': json.dumps(data_dict.get('datasets_data') or []),
            }

            return render_template('data_stories/edit.html', **extra_vars)

        except Exception as e:
            log.error(f"Error creating story: {str(e)}")
            flash(tk._('Error creating story: {}').format(str(e)), 'error')

            extra_vars = {
                'story': draft_story_context,
                'data': data_dict,
                'errors': {},
                'error_summary': {},
                'is_new': True,
                'datasets_data_json': json.dumps(data_dict.get('datasets_data') or []),
            }

            return render_template('data_stories/edit.html', **extra_vars)

        # Persist sections captured in the form (if any)
        try:
            _sync_story_sections(context, story['id'], sections_data)
            _sync_story_datasets(context, story['id'], datasets_data)
        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary

            story_context = _build_story_context({**story, 'sections': sections_data})
            extra_vars = {
                'story': story_context,
                'data': {**data_dict, 'slug': story.get('slug')},
                'errors': errors,
                'error_summary': error_summary,
                'is_new': False,
                'datasets_data_json': json.dumps(datasets_data or []),
            }

            return render_template('data_stories/edit.html', **extra_vars)
        except Exception as e:
            log.error(f"Error creating sections for story {story.get('id')}: {str(e)}")
            flash(tk._('Story created but sections could not be saved: {}').format(str(e)), 'error')

            story_context = _build_story_context({**story, 'sections': sections_data})
            extra_vars = {
                'story': story_context,
                'data': {**data_dict, 'slug': story.get('slug')},
                'errors': {},
                'error_summary': {},
                'is_new': False,
                'datasets_data_json': json.dumps(datasets_data or []),
            }

            return render_template('data_stories/edit.html', **extra_vars)

        flash(tk._('Story created successfully'), 'success')

        # Redirect to story page
        return redirect(url_for('data_stories.show', slug=story['slug']))

    # GET request - show form
    story_data = _build_story_context({})
    extra_vars = {
        'story': story_data,
        'data': {},
        'errors': {},
        'error_summary': {},
        'is_new': True,
        'datasets_data_json': json.dumps([]),
    }

    return render_template('data_stories/edit.html', **extra_vars)


# ============================================================================
# Import Routes (Sysadmin only)
# ============================================================================

@data_stories_blueprint.route('/import', methods=['GET', 'POST'])
def import_story():
    """
    Import a data story from JSON file.

    URL: /data-stories/import

    Only sysadmins can import stories.
    """
    log.info("[DATA_STORIES_ROUTE] Import story page")

    context = _get_context()

    # Must be logged in
    if not g.userobj:
        flash(tk._('Please log in to import stories'), 'error')
        return redirect(url_for('user.login'))

    # Check if user is sysadmin
    if not getattr(g.userobj, 'sysadmin', False):
        tk.abort(403, tk._('Only administrators can import stories'))

    if request.method == 'POST':
        # Handle file upload
        uploaded_file = request.files.get('import_file')

        if not uploaded_file or uploaded_file.filename == '':
            flash(tk._('Please select a file to import'), 'error')
            return render_template('data_stories/import.html')

        # Check file extension
        if not uploaded_file.filename.endswith('.json'):
            flash(tk._('Please upload a JSON file'), 'error')
            return render_template('data_stories/import.html')

        try:
            # Read and parse JSON
            file_content = uploaded_file.read().decode('utf-8')
            export_data = json.loads(file_content)

            # Get import options
            slug_conflict = request.form.get('slug_conflict', 'rename')
            organization_id = request.form.get('organization_id') or None
            target_status = request.form.get('status', 'draft')

            # Import story
            result = tk.get_action('data_story_import')(context, {
                'data': export_data,
                'slug_conflict': slug_conflict,
                'organization_id': organization_id,
                'status': target_status,
            })

            import_info = result.get('import_info', {})
            flash(tk._('Story imported successfully! Imported {} sections.').format(
                import_info.get('sections_imported', 0)
            ), 'success')

            return redirect(url_for('data_stories.show', slug=result['slug']))

        except json.JSONDecodeError as e:
            flash(tk._('Invalid JSON file: {}').format(str(e)), 'error')
            return render_template('data_stories/import.html')
        except tk.ValidationError as e:
            error_msg = '; '.join([f"{k}: {v}" for k, v in e.error_dict.items()])
            flash(tk._('Validation error: {}').format(error_msg), 'error')
            return render_template('data_stories/import.html')
        except Exception as e:
            log.error(f"Error importing story: {str(e)}")
            flash(tk._('Error importing story: {}').format(str(e)), 'error')
            return render_template('data_stories/import.html')

    # GET request - show import form
    return render_template('data_stories/import.html')


# ============================================================================
# View Routes
# ============================================================================

@data_stories_blueprint.route('/<slug>')
def show(slug):
    """
    View a single data story.

    URL: /data-stories/<slug>

    IMPORTANT: This route must come AFTER all specific routes like /new
    and /import to avoid matching them as slugs.
    """
    log.info(f"[DATA_STORIES_ROUTE] Showing story: {slug}")

    context = _get_context()

    try:
        # Get story - use ignore_auth to fetch, then check access manually
        # This allows published stories to be viewed by anonymous users
        show_context = dict(context)
        show_context['ignore_auth'] = True
        
        story = tk.get_action('data_story_show')(show_context, {
            'slug': slug,
            'include_sections': True,
            'include_datasets': True,
            'include_contributors': True,
        })

        # Check if user can view this story
        # Published stories are viewable by anyone
        if story.get('status') != 'published' and not story.get('is_public'):
            # For non-published stories, check authorization
            try:
                tk.check_access('data_story_show', context, {'id': story['id']})
            except tk.NotAuthorized:
                tk.abort(403, tk._('Not authorized to view this story'))

        # Record view (ignore auth for this)
        try:
            tk.get_action('data_story_record_view')(
                {'ignore_auth': True},
                {'id': story['id']}
            )
        except Exception as e:
            log.warning(f"Failed to record view: {str(e)}")
            model.Session.rollback()

    except tk.ObjectNotFound:
        tk.abort(404, tk._('Story not found'))
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to view this story'))
    except Exception as e:
        log.error(f"Error showing story: {str(e)}")
        model.Session.rollback()
        tk.abort(500, tk._('Error loading story'))

    # Get comments if user is authorized
    comments = []
    try:
        comments = tk.get_action('data_story_comment_list')(context, {
            'story_id': story['id'],
        })
    except Exception as e:
        log.warning(f"Could not load comments: {str(e)}")
        model.Session.rollback()

    extra_vars = {
        'story': story,
        'comments': comments,
    }

    return render_template('data_stories/show.html', **extra_vars)


@data_stories_blueprint.route('/<slug>/edit', methods=['GET', 'POST'])
def edit(slug):
    """
    Edit an existing data story.

    URL: /data-stories/<slug>/edit
    """
    log.info(f"[DATA_STORIES_ROUTE] Editing story: {slug}")

    context = _get_context()

    # Must be logged in
    if not g.userobj:
        flash(tk._('Please log in to edit stories'), 'error')
        return redirect(url_for('user.login'))

    # Get story
    try:
        story = tk.get_action('data_story_show')(context, {
            'slug': slug,
            'include_sections': True,
            'include_datasets': True,
        })
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Story not found'))
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to view this story'))

    # Check edit permission
    try:
        tk.check_access('data_story_update', context, {'id': story['id']})
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to edit this story'))

    if request.method == 'POST':
        # Get form data
        data_dict = _extract_story_form_data(request.form)
        data_dict['id'] = story['id']
        sections_data = _extract_sections_form_data(request.form)
        datasets_data = data_dict.get('datasets_data') or []
        story_context = _build_story_context({**story, **data_dict, 'sections': sections_data})

        try:
            # Store original status to check if it changed
            original_status = story.get('status')
            
            # Update story
            updated_story = tk.get_action('data_story_update')(context, data_dict)
            _sync_story_sections(
                context,
                story['id'],
                sections_data,
                existing_sections=story.get('sections', [])
            )
            _sync_story_datasets(context, story['id'], datasets_data)
            log.info("[DATA_STORIES_ROUTE] Sync completed, preparing redirect")

            # Check if story was resubmitted for review
            new_status = updated_story.get('status')
            if original_status == 'published' and new_status == 'submitted':
                flash(tk._('Story updated and resubmitted for review. It will be reviewed before being published again.'), 'info')
            else:
                flash(tk._('Story updated successfully'), 'success')
            log.info("[DATA_STORIES_ROUTE] Flash message set")

            # Redirect to view page
            redirect_url = url_for('data_stories.show', slug=updated_story['slug'])
            log.info(f"[DATA_STORIES_ROUTE] Redirecting to: {redirect_url}")
            return redirect(redirect_url)

        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary

            extra_vars = {
                'story': story_context,
                'data': data_dict,
                'errors': errors,
                'error_summary': error_summary,
                'is_new': False,
                'datasets_data_json': json.dumps(datasets_data or _build_datasets_form_data(story)),
            }

            return render_template('data_stories/edit.html', **extra_vars)

        except Exception as e:
            log.error(f"Error updating story: {str(e)}")
            flash(tk._('Error updating story: {}').format(str(e)), 'error')

            extra_vars = {
                'story': story_context,
                'data': data_dict,
                'errors': {},
                'error_summary': {},
                'is_new': False,
                'datasets_data_json': json.dumps(datasets_data or _build_datasets_form_data(story)),
            }

            return render_template('data_stories/edit.html', **extra_vars)

    # GET request - show form
    # Debug: Log sections data being passed to template
    if story.get('sections'):
        for idx, section in enumerate(story['sections']):
            log.debug(f"[EDIT_GET] Section {idx} blocks_metadata type: {type(section.get('blocks_metadata'))}")

        # Direct database verification
        from ckanext.pages.data_stories.db.models import DataStorySection
        from ckan import model as ckan_model
        db_sections = ckan_model.Session.query(DataStorySection).filter(
            DataStorySection.story_id == story['id']
        ).all()
        for db_section in db_sections:
            log.debug(f"[EDIT_GET_DB] Section {db_section.id} DB blocks_metadata type: {type(db_section.blocks_metadata)}")

    extra_vars = {
        'story': story,
        'data': story,
        'errors': {},
        'error_summary': {},
        'is_new': False,
        'datasets_data_json': json.dumps(_build_datasets_form_data(story)),
    }

    return render_template('data_stories/edit.html', **extra_vars)


@data_stories_blueprint.route('/<slug>/delete', methods=['POST'])
def delete(slug):
    """
    Delete a data story.

    URL: /data-stories/<slug>/delete (POST)
    """
    log.info(f"[DATA_STORIES_ROUTE] Deleting story: {slug}")

    context = _get_context()

    # Must be logged in
    if not g.userobj:
        tk.abort(403, tk._('Must be logged in'))

    # Get story
    try:
        story = tk.get_action('data_story_show')(context, {'slug': slug})
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Story not found'))

    # Delete story
    try:
        tk.get_action('data_story_delete')(context, {'id': story['id']})
        flash(tk._('Story deleted successfully'), 'success')
        return redirect(url_for('data_stories.index'))

    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to delete this story'))
    except Exception as e:
        log.error(f"Error deleting story: {str(e)}")
        flash(tk._('Error deleting story: {}').format(str(e)), 'error')
        return redirect(url_for('data_stories.show', slug=slug))


# ============================================================================
# Workflow Routes
# ============================================================================

@data_stories_blueprint.route('/<slug>/submit', methods=['POST'])
def submit(slug):
    """
    Submit a story for review.

    URL: /data-stories/<slug>/submit (POST)
    """
    log.info(f"[DATA_STORIES_ROUTE] Submitting story: {slug}")

    context = _get_context()

    # Get story
    try:
        story = tk.get_action('data_story_show')(context, {'slug': slug})
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Story not found'))

    # Submit story
    try:
        tk.get_action('data_story_submit')(context, {
            'id': story['id'],
            'submission_notes': request.form.get('submission_notes', ''),
        })

        flash(tk._('Story submitted for review'), 'success')

    except tk.ValidationError as e:
        flash(tk._('Cannot submit story: {}').format('; '.join(e.error_summary.values())), 'error')
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to submit this story'))
    except Exception as e:
        log.error(f"Error submitting story: {str(e)}")
        flash(tk._('Error submitting story: {}').format(str(e)), 'error')

    return redirect(url_for('data_stories.show', slug=slug))


@data_stories_blueprint.route('/<slug>/publish', methods=['POST'])
def publish(slug):
    """
    Publish a story directly (skip review workflow).

    URL: /data-stories/<slug>/publish (POST)
    """
    log.info(f"[DATA_STORIES_ROUTE] Publishing story: {slug}")

    context = _get_context()

    # Get story
    try:
        story = tk.get_action('data_story_show')(context, {'slug': slug})
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Story not found'))

    # Publish story
    try:
        tk.get_action('data_story_approve')(context, {
            'id': story['id'],
            'approval_notes': 'Direct publication by author',
        })

        flash(tk._('Story published successfully'), 'success')

    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to publish this story'))
    except Exception as e:
        log.error(f"Error publishing story: {str(e)}")
        flash(tk._('Error publishing story: {}').format(str(e)), 'error')

    return redirect(url_for('data_stories.show', slug=slug))


@data_stories_blueprint.route('/<slug>/review', methods=['GET', 'POST'])
def review(slug):
    """
    Review a submitted story.

    URL: /data-stories/<slug>/review
    """
    log.info(f"[DATA_STORIES_ROUTE] Reviewing story: {slug}")

    context = _get_context()

    # Get story
    try:
        story = tk.get_action('data_story_show')(context, {
            'slug': slug,
            'include_sections': True,
        })
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Story not found'))

    # Check review permission
    try:
        tk.check_access('data_story_review', context, {'id': story['id']})
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to review this story'))

    # Get comments
    comments = []
    try:
        comments = tk.get_action('data_story_comment_list')(context, {
            'story_id': story['id'],
        })
    except Exception as e:
        log.warning(f"Could not load comments: {str(e)}")
        model.Session.rollback()

    if request.method == 'POST':
        action = request.form.get('action')

        try:
            if action == 'start_review':
                # Transition to under_review
                tk.get_action('data_story_review')(context, {'id': story['id']})
                flash(tk._('Review started'), 'success')

            elif action == 'approve':
                # Approve and publish
                tk.get_action('data_story_approve')(context, {
                    'id': story['id'],
                    'approval_notes': request.form.get('approval_notes', ''),
                })
                flash(tk._('Story approved and published'), 'success')
                return redirect(url_for('data_stories.show', slug=slug))

            elif action == 'request_changes':
                # Request changes
                required_changes = request.form.get('required_changes')
                if not required_changes:
                    flash(tk._('Please specify required changes'), 'error')
                else:
                    tk.get_action('data_story_request_changes')(context, {
                        'id': story['id'],
                        'required_changes': required_changes,
                    })
                    flash(tk._('Changes requested'), 'success')

        except tk.NotAuthorized:
            tk.abort(403, tk._('Not authorized'))
        except Exception as e:
            log.error(f"Error in review action: {str(e)}")
            flash(tk._('Error: {}').format(str(e)), 'error')

        # Reload story
        story = tk.get_action('data_story_show')(context, {
            'slug': slug,
            'include_sections': True,
        })

    extra_vars = {
        'story': story,
        'comments': comments,
    }

    return render_template('data_stories/review.html', **extra_vars)


# ============================================================================
# Section Management Routes (AJAX)
# ============================================================================

@data_stories_blueprint.route('/<slug>/sections/create', methods=['POST'])
def create_section(slug):
    """
    Create a new section (AJAX endpoint).

    URL: /data-stories/<slug>/sections/create (POST)
    """
    log.info(f"[DATA_STORIES_ROUTE] Creating section for story: {slug}")

    context = _get_context()

    # Get story
    try:
        story = tk.get_action('data_story_show')(context, {'slug': slug})
    except tk.ObjectNotFound:
        return {'success': False, 'error': 'Story not found'}, 404

    # Extract section data
    data_dict = {
        'story_id': story['id'],
        'section_type': request.form.get('section_type'),
        'title': request.form.get('title'),
        'content': request.form.get('content', ''),
        'order_index': request.form.get('order_index'),
    }

    # Create section
    try:
        section = tk.get_action('data_story_section_create')(context, data_dict)

        if request.is_json or request.headers.get('Accept') == 'application/json':
            return {'success': True, 'section': section}
        else:
            flash(tk._('Section created'), 'success')
            return redirect(url_for('data_stories.edit', slug=slug))

    except tk.ValidationError as e:
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return {'success': False, 'errors': e.error_dict}, 400
        else:
            flash(tk._('Error creating section'), 'error')
            return redirect(url_for('data_stories.edit', slug=slug))
    except Exception as e:
        log.error(f"Error creating section: {str(e)}")
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return {'success': False, 'error': str(e)}, 500
        else:
            flash(tk._('Error: {}').format(str(e)), 'error')
            return redirect(url_for('data_stories.edit', slug=slug))


# ============================================================================
# Comment Routes
# ============================================================================

@data_stories_blueprint.route('/<slug>/comments', methods=['POST'])
def create_comment(slug):
    """
    Create a comment on a story.
    
    URL: /data-stories/<slug>/comments (POST)
    
    Form data:
        - content: Comment text (required)
        - section_id: Section ID if commenting on a section (optional)
        - parent_comment_id: Parent comment for threading (optional)
        - comment_type: Type of comment (comment, suggestion, required_change)
    """
    log.info(f"[DATA_STORIES_ROUTE] Creating comment for story: {slug}")
    
    context = _get_context()
    
    # Get story
    try:
        story = tk.get_action('data_story_show')(context, {'slug': slug})
    except tk.ObjectNotFound:
        flash(tk._('Story not found'), 'error')
        return redirect(url_for('data_stories.index'))
    
    # Extract comment data
    content = request.form.get('content', '').strip()
    
    if not content:
        flash(tk._('Comment cannot be empty'), 'error')
        return redirect(url_for('data_stories.show', slug=slug))
    
    data_dict = {
        'story_id': story['id'],
        'content': content,
        'section_id': request.form.get('section_id'),
        'parent_comment_id': request.form.get('parent_comment_id'),
        'comment_type': request.form.get('comment_type', 'comment')
    }
    
    # Create comment
    try:
        comment = tk.get_action('data_story_comment_create')(context, data_dict)
        flash(tk._('Comment added successfully'), 'success')
        log.info(f"[DATA_STORIES_ROUTE] Comment created: {comment['id']}")
        
    except tk.NotAuthorized:
        flash(tk._('You are not authorized to comment'), 'error')
    except tk.ValidationError as e:
        error_msg = ' '.join([str(v) for v in e.error_dict.values()])
        flash(tk._('Error: {}').format(error_msg), 'error')
    except Exception as e:
        log.error(f"Error creating comment: {str(e)}")
        flash(tk._('Error adding comment'), 'error')
    
    # Redirect back to story
    return redirect(url_for('data_stories.show', slug=slug) + '#comments')


# ============================================================================
# Export Routes (Sysadmin only)
# ============================================================================

@data_stories_blueprint.route('/<slug>/export')
def export_story(slug):
    """
    Export a data story as JSON file.

    URL: /data-stories/<slug>/export

    Only sysadmins can export stories.
    """
    log.info(f"[DATA_STORIES_ROUTE] Exporting story: {slug}")

    context = _get_context()

    # Must be logged in
    if not g.userobj:
        flash(tk._('Please log in to export stories'), 'error')
        return redirect(url_for('user.login'))

    # Check if user is sysadmin
    if not getattr(g.userobj, 'sysadmin', False):
        tk.abort(403, tk._('Only administrators can export stories'))

    try:
        # Get story first to get the slug for filename
        story = tk.get_action('data_story_show')(context, {'slug': slug})

        # Export story
        export_data = tk.get_action('data_story_export')(context, {
            'slug': slug,
            'include_metadata': True,
        })

        # Convert to JSON
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)

        # Create response with JSON file download
        filename = f"data-story-{story['slug']}.json"
        response = Response(
            json_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/json; charset=utf-8',
            }
        )

        return response

    except tk.ObjectNotFound:
        tk.abort(404, tk._('Story not found'))
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to export this story'))
    except Exception as e:
        log.error(f"Error exporting story: {str(e)}")
        flash(tk._('Error exporting story: {}').format(str(e)), 'error')
        return redirect(url_for('data_stories.show', slug=slug))


# ============================================================================
# Helper Functions
# ============================================================================

def _get_context():
    """Get CKAN context for current request."""
    return {
        'user': g.user,
        'auth_user_obj': g.userobj,
    }


def _extract_story_form_data(form):
    """Extract story data from form submission."""
    countries_raw = form.get('countries')
    log.info(f"[EXTRACT_FORM] countries raw from form: {countries_raw!r}")
    countries_parsed = _parse_json_field(countries_raw, default_empty_list=True)
    log.info(f"[EXTRACT_FORM] countries parsed: {countries_parsed!r}")
    
    partners_raw = form.get('partners')
    log.info(f"[EXTRACT_FORM] partners raw from form: {partners_raw!r}")
    partners_parsed = _parse_json_field(partners_raw, default_empty_list=True)
    log.info(f"[EXTRACT_FORM] partners parsed: {partners_parsed!r}")
    
    uploaded_images_raw = form.get('uploaded_images')
    uploaded_images_parsed = _parse_json_field(uploaded_images_raw, default_empty_list=True)
    log.info(f"[EXTRACT_FORM] uploaded_images: {len(uploaded_images_parsed) if uploaded_images_parsed else 0} images")
    
    return {
        'title': form.get('title', '').strip(),
        'slug': form.get('slug', '').strip(),
        'abstract': form.get('abstract', '').strip(),
        'research_question': form.get('research_question', '').strip(),
        'study_area': form.get('study_area', '').strip(),
        'paper_doi': form.get('paper_doi', '').strip(),
        'paper_citation': form.get('paper_citation', '').strip(),
        'organization_id': form.get('organization_id', '').strip() or None,
        'project_type': form.get('project_type', '').strip() or None,
        'partners': partners_parsed,
        'countries': countries_parsed,
        'uploaded_images': uploaded_images_parsed,
        'datasets_data': _parse_json_field(form.get('datasets_data')),
    }


def _build_story_context(data):
    """Build a story-like dict for templates, ensuring expected keys exist."""
    data = data or {}
    return {
        'id': data.get('id'),
        'title': data.get('title', ''),
        'slug': data.get('slug', ''),
        'abstract': data.get('abstract', ''),
        'research_question': data.get('research_question', ''),
        'study_area': data.get('study_area', ''),
        'paper_doi': data.get('paper_doi', ''),
        'paper_citation': data.get('paper_citation', ''),
        'countries': data.get('countries', []),
        'partners': data.get('partners', []),
        'project_type': data.get('project_type', ''),
        'uploaded_images': data.get('uploaded_images', []),
        'organization_id': data.get('organization_id'),
        'sections': data.get('sections', []),
        'datasets_data': data.get('datasets_data'),
    }


def _extract_sections_form_data(form):
    """
    Extract section data from the submitted form.

    Returns a list of section dicts preserving the form order.
    Empty sections (no type, title, or content) are ignored.
    """
    # Debug: Log form keys containing 'blocks_metadata' (length only to avoid performance issues)
    for key in form:
        if 'blocks_metadata' in key:
            val = form.get(key)
            log.debug(f"[EXTRACT_SECTIONS] Form key '{key}' len={len(val) if val else 0}")

    sections = {}

    for key in form:
        match = _SECTION_FIELD_RE.match(key)
        if not match:
            continue

        index = int(match.group(1))
        field_name = match.group(2)

        if index not in sections:
            sections[index] = {}

        sections[index][field_name] = form.get(key)

    section_list = []
    for index in sorted(sections.keys()):
        raw = sections[index]

        raw_blocks = raw.get('blocks_metadata')
        parsed_blocks = _parse_json_field(raw_blocks)
        if parsed_blocks is None:
            parsed_blocks = _reconstruct_blocks_metadata(raw)
            if parsed_blocks:
                log.info(f"[EXTRACT_SECTIONS] Section {index} reconstructed blocks_metadata from content/terria")
        log.debug(f"[EXTRACT_SECTIONS] Section {index} raw blocks_metadata: {type(raw_blocks)} len={len(raw_blocks) if raw_blocks else 0}")
        log.debug(f"[EXTRACT_SECTIONS] Section {index} parsed blocks_metadata type: {type(parsed_blocks)}")

        section = {
            'id': (raw.get('id') or '').strip() or None,
            'title': (raw.get('title') or '').strip(),
            'section_type': (raw.get('section_type') or '').strip(),
            'content': raw.get('content') or '',
            'order_index': _coerce_int(raw.get('order_index'), index),
            'image_url': (raw.get('image_url') or '').strip(),
            'video_url': (raw.get('video_url') or '').strip(),
            'terria_share_link': (raw.get('terria_share_link') or '').strip(),
            'terria_config': _parse_json_field(raw.get('terria_config')),
            'blocks_metadata': parsed_blocks,
            'is_visible': _parse_bool(raw.get('is_visible', True)),
        }

        # Skip blank sections so they don't trigger validation errors
        if not any([
            section['section_type'],
            section['title'],
            section['content'],
            section['terria_share_link'],
            section['image_url'],
            section['video_url'],
            section['terria_config'],
        ]):
            continue

        section_list.append(section)

    return section_list


def _sync_story_sections(context, story_id, sections_data, existing_sections=None):
    """
    Create, update, or delete sections to match the submitted form data.

    Args:
        context: CKAN context dict
        story_id: ID of the story the sections belong to
        sections_data: Sections extracted from the form
        existing_sections: Current sections (dicts) for comparison
    """
    existing_sections = existing_sections or []
    existing_map = {
        s.get('id'): s for s in existing_sections
        if s.get('id')
    }
    processed_ids = set()

    for idx, section in enumerate(sections_data):
        blocks_meta = section.get('blocks_metadata')
        log.debug(f"[SYNC_SECTIONS] Section {idx} blocks_metadata type: {type(blocks_meta)}")

        payload = {
            'story_id': story_id,
            'section_type': section.get('section_type'),
            'title': section.get('title'),
            'content': section.get('content', ''),
            'order_index': section.get('order_index', idx),
            'image_url': section.get('image_url'),
            'video_url': section.get('video_url'),
            'terria_config': section.get('terria_config'),
            'terria_share_link': section.get('terria_share_link'),
            'blocks_metadata': blocks_meta,
            'is_visible': section.get('is_visible', True),
        }

        section_id = section.get('id')
        if section_id and section_id in existing_map:
            payload['id'] = section_id
            updated = tk.get_action('data_story_section_update')(context, payload)
            processed_ids.add(updated['id'])
        else:
            created = tk.get_action('data_story_section_create')(context, payload)
            processed_ids.add(created['id'])

    # Delete removed sections
    for existing_id in existing_map.keys():
        if existing_id not in processed_ids:
            tk.get_action('data_story_section_delete')(context, {'id': existing_id})


def _sync_story_datasets(context, story_id, datasets_data):
    """
    Link/unlink datasets based on the submitted dataset list.
    """
    datasets_data = datasets_data or []

    desired_ids = []
    for entry in datasets_data:
        if isinstance(entry, str):
            desired_ids.append(entry)
        elif isinstance(entry, dict):
            ds_id = entry.get('id') or entry.get('dataset_id') or entry.get('name')
            if ds_id:
                desired_ids.append(ds_id)

    # Remove duplicates while preserving order
    seen = set()
    desired_ids = [d for d in desired_ids if not (d in seen or seen.add(d))]

    # Query existing links directly from DB to avoid expensive package_show calls
    from ckanext.pages.data_stories.db.models import DataStoryDataset
    existing_db_links = DataStoryDataset.all(story_id=story_id)
    existing_ids = {link.dataset_id for link in existing_db_links if link.dataset_id}

    # Link new datasets
    for ds_id in desired_ids:
        if ds_id not in existing_ids:
            try:
                tk.get_action('data_story_link_dataset')(context, {
                    'story_id': story_id,
                    'dataset_id': ds_id,
                    'relationship_type': 'primary',
                })
            except Exception as e:
                log.error(f"[SYNC_DATASETS] Could not link dataset {ds_id}: {str(e)}")

    # Unlink removed datasets
    for ds_id in existing_ids:
        if ds_id not in desired_ids:
            try:
                tk.get_action('data_story_unlink_dataset')(context, {
                    'story_id': story_id,
                    'dataset_id': ds_id,
                })
            except Exception as e:
                log.error(f"[SYNC_DATASETS] Could not unlink dataset {ds_id}: {str(e)}")


def _coerce_int(value, default=0):
    """Convert incoming value to int, returning default on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_json_field(raw_value, default_empty_list=False):
    """Parse JSON stored in form fields, returning None when unset/invalid.
    
    Args:
        raw_value: The raw value from the form field
        default_empty_list: If True, return [] instead of None for empty/null values
    """
    if not raw_value:
        return [] if default_empty_list else None

    if isinstance(raw_value, (dict, list)):
        return raw_value

    # Handle string values
    if isinstance(raw_value, str):
        raw_value = html.unescape(raw_value).strip()
        if not raw_value or raw_value == 'null':
            return [] if default_empty_list else None
        
        # Handle empty array string - return actual empty list
        if raw_value == '[]':
            return []

        try:
            parsed = json.loads(raw_value)
            # Handle double-encoded JSON (string containing JSON string)
            if isinstance(parsed, str):
                parsed = json.loads(parsed)
            return parsed
        except (TypeError, ValueError, json.JSONDecodeError):
            return [] if default_empty_list else None

    return [] if default_empty_list else None


def _strip_html_tags(value: str) -> str:
    """Remove HTML tags from a string."""
    if not value:
        return ''
    return re.sub(r'<[^>]+>', '', value)


def _extract_terria_tabs_from_content(content: str) -> list:
    """
    Try to recover Terria tabs info from rendered HTML content.

    Returns a list of {title, url} dicts when Terria embed markup is present.
    """
    if not content or 'terria-tabs-display' not in content:
        return []

    # Map tab index -> title
    titles = {}
    for idx, title_html in re.findall(
        r'<li[^>]*data-tab="(\d+)"[^>]*>(.*?)</li>', content, flags=re.S
    ):
        titles[idx] = _strip_html_tags(title_html).strip()

    tabs = []
    for idx, url in re.findall(
        r'<div[^>]*class="[^"]*terria-tab-display[^"]*"[^>]*data-tab="(\d+)"[^>]*>'
        r'.*?<iframe[^>]*src="([^"]+)"[^>]*>.*?</iframe>.*?</div>',
        content,
        flags=re.S,
    ):
        title = titles.get(idx) or f"Map {len(tabs) + 1}"
        tabs.append({'title': title, 'url': url})

    return tabs


def _strip_terria_markup(content: str) -> str:
    """Remove the Terria embed markup from a HTML string."""
    if not content:
        return ''
    return re.sub(
        r'<div[^>]*class="[^"]*terria-tabs-display[^"]*"[^>]*>.*?</div>',
        '',
        content,
        flags=re.S,
    ).strip()


def _reconstruct_blocks_metadata(raw_section: dict) -> list:
    """
    Build a minimal blocks_metadata structure when the incoming form did not
    contain valid JSON (e.g., legacy stories or parsing failures).
    """
    content = (raw_section.get('content') or '').strip()
    terria_link = (raw_section.get('terria_share_link') or '').strip()
    blocks = []

    terria_tabs = _extract_terria_tabs_from_content(content)
    if terria_tabs:
        cleaned_content = _strip_terria_markup(content)
        if cleaned_content:
            blocks.append({'type': 'text', 'content': cleaned_content})
        blocks.append({'type': 'terria', 'tabs': terria_tabs})
    elif content:
        blocks.append({'type': 'text', 'content': content})

    if terria_link and not any(block.get('type') == 'terria' for block in blocks):
        blocks.append({'type': 'terria', 'tabs': [{'title': 'Map 1', 'url': terria_link}]})

    return blocks or None


def _parse_bool(value):
    """Normalize truthy/falsey form values to boolean."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False

    return str(value).lower() not in ('false', '0', 'off', '')


def _get_extra_value(extras, key):
    """Helper to pull a value from CKAN extras list."""
    if not extras:
        return None
    for item in extras:
        if item.get('key') == key:
            return item.get('value')
    return None


def _build_datasets_form_data(story):
    """Prepare dataset info for the edit form hidden field."""
    datasets = story.get('datasets') if story else []
    result = []

    for link in datasets:
        dataset = link.get('dataset') or {}
        extras = dataset.get('extras')
        doi = (
            dataset.get('doi')
            or dataset.get('dataset_doi')
            or _get_extra_value(extras, 'doi')
            or _get_extra_value(extras, 'dataset_doi')
        )
        doi_status = (
            dataset.get('doi_status')
            or _get_extra_value(extras, 'doi_status')
            or _get_extra_value(extras, 'doi_state')
        )
        citation = dataset.get('citation') or _get_extra_value(extras, 'citation')
        authors_text = _get_extra_value(extras, 'authors') or dataset.get('author') or dataset.get('maintainer')

        result.append({
            'id': dataset.get('id') or link.get('dataset_id'),
            'name': dataset.get('name'),
            'title': dataset.get('title'),
            'doi': doi,
            'doi_status': doi_status,
            'citation': citation,
            'authors': authors_text,
        })

    return result
