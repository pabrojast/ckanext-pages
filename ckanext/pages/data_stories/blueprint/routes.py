"""
Flask routes for Data Stories web interface.

Provides URL routes and view functions for the data stories web UI.
"""

import json
import logging
import re

from flask import Blueprint, render_template, request, redirect, url_for, flash
import ckan.plugins.toolkit as tk
from ckan.common import g

log = logging.getLogger(__name__)

# Create blueprint
data_stories_blueprint = Blueprint(
    'data_stories',
    __name__,
    url_prefix='/data-stories'
)

# Pattern to extract section fields from form data
_SECTION_FIELD_RE = re.compile(r'^sections\[(\d+)\]\[([^\]]+)\]$')


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

    # Get stories
    try:
        result = tk.get_action('data_story_list')(context, data_dict)
        stories = result['stories']
        total_count = result['count']
        facets = result.get('facets', {})
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to view stories'))
    except Exception as e:
        log.error(f"Error listing stories: {str(e)}")
        stories = []
        total_count = 0
        facets = {}

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

    # Prepare template variables
    extra_vars = {
        'stories': stories,
        'featured_stories': featured_stories,
        'total_count': total_count,
        'page': page,
        'total_pages': total_pages,
        'limit': limit,
        'sort': sort,
        'status_filter': status_filter,
        'org_filter': org_filter,
        'q': q,
        'facets': facets,
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

    # Check if user has review permissions
    try:
        # Try to check if user is a reviewer (will fail if not authorized)
        tk.check_access('sysadmin', context, {})
        is_reviewer = True
    except tk.NotAuthorized:
        is_reviewer = False

    if not is_reviewer:
        # Check if user is org admin for any org
        from ckan import model
        user_obj = g.userobj
        user_orgs = model.Session.query(model.Member).filter(
            model.Member.table_name == 'user',
            model.Member.table_id == user_obj.id,
            model.Member.capacity == 'admin',
            model.Member.state == 'active'
        ).all()

        if not user_orgs:
            flash(tk._('You do not have permission to review stories'), 'error')
            return redirect(url_for('data_stories.index'))

    # Get parameters
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    status_filter = request.args.get('status', 'all')

    # Calculate offset
    offset = (page - 1) * limit

    # Build data_dict for submitted stories
    data_dict_submitted = {
        'limit': limit,
        'offset': offset,
        'sort': 'recent',
    }

    # Filter by status
    if status_filter == 'submitted':
        data_dict_submitted['status'] = 'submitted'
    elif status_filter == 'under_review':
        data_dict_submitted['status'] = 'under_review'
    elif status_filter == 'all':
        # We'll need to combine both statuses
        pass

    # Get stories
    stories = []
    total_count = 0

    try:
        if status_filter in ['submitted', 'under_review']:
            result = tk.get_action('data_story_list')(context, data_dict_submitted)
            stories = result['stories']
            total_count = result['count']
        else:
            # Get both submitted and under_review
            result_submitted = tk.get_action('data_story_list')(context, {
                **data_dict_submitted,
                'status': 'submitted'
            })
            result_review = tk.get_action('data_story_list')(context, {
                **data_dict_submitted,
                'status': 'under_review'
            })
            stories = result_submitted['stories'] + result_review['stories']
            total_count = result_submitted['count'] + result_review['count']

            # Sort by created_at descending
            stories.sort(key=lambda x: x.get('created_at', ''), reverse=True)

            # Apply pagination manually
            stories = stories[offset:offset + limit]

    except Exception as e:
        log.error(f"Error listing pending stories: {str(e)}")
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
            }

            return render_template('data_stories/edit.html', **extra_vars)

        # Persist sections captured in the form (if any)
        try:
            _sync_story_sections(context, story['id'], sections_data)
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
    }

    return render_template('data_stories/edit.html', **extra_vars)


# ============================================================================
# View Routes
# ============================================================================

@data_stories_blueprint.route('/<slug>')
def show(slug):
    """
    View a single data story.

    URL: /data-stories/<slug>

    IMPORTANT: This route must come AFTER all specific routes like /new
    to avoid matching them as slugs.
    """
    log.info(f"[DATA_STORIES_ROUTE] Showing story: {slug}")

    context = _get_context()

    try:
        # Get story
        story = tk.get_action('data_story_show')(context, {
            'slug': slug,
            'include_sections': True,
            'include_datasets': True,
            'include_contributors': True,
        })

        # Record view (ignore auth for this)
        try:
            tk.get_action('data_story_record_view')(
                {'ignore_auth': True},
                {'id': story['id']}
            )
        except Exception as e:
            log.warning(f"Failed to record view: {str(e)}")

    except tk.ObjectNotFound:
        tk.abort(404, tk._('Story not found'))
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to view this story'))
    except Exception as e:
        log.error(f"Error showing story: {str(e)}")
        tk.abort(500, tk._('Error loading story'))

    # Get comments if user is authorized
    comments = []
    try:
        comments = tk.get_action('data_story_comment_list')(context, {
            'story_id': story['id'],
        })
    except Exception as e:
        log.warning(f"Could not load comments: {str(e)}")

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
        story_context = _build_story_context({**story, **data_dict, 'sections': sections_data})

        try:
            # Update story
            updated_story = tk.get_action('data_story_update')(context, data_dict)
            _sync_story_sections(
                context,
                story['id'],
                sections_data,
                existing_sections=story.get('sections', [])
            )

            flash(tk._('Story updated successfully'), 'success')

            # Redirect to view page
            return redirect(url_for('data_stories.show', slug=updated_story['slug']))

        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary

            extra_vars = {
                'story': story_context,
                'data': data_dict,
                'errors': errors,
                'error_summary': error_summary,
                'is_new': False,
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
            }

            return render_template('data_stories/edit.html', **extra_vars)

    # GET request - show form
    extra_vars = {
        'story': story,
        'data': story,
        'errors': {},
        'error_summary': {},
        'is_new': False,
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
        return redirect(url_for('data_stories.my_stories'))

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
    return {
        'title': form.get('title', '').strip(),
        'slug': form.get('slug', '').strip(),
        'abstract': form.get('abstract', '').strip(),
        'research_question': form.get('research_question', '').strip(),
        'study_area': form.get('study_area', '').strip(),
        'organization_id': form.get('organization_id', '').strip() or None,
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
        'organization_id': data.get('organization_id'),
        'sections': data.get('sections', []),
    }


def _extract_sections_form_data(form):
    """
    Extract section data from the submitted form.

    Returns a list of section dicts preserving the form order.
    Empty sections (no type, title, or content) are ignored.
    """
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


def _coerce_int(value, default=0):
    """Convert incoming value to int, returning default on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_json_field(raw_value):
    """Parse JSON stored in form fields, returning None when unset/invalid."""
    if not raw_value:
        return None

    if isinstance(raw_value, (dict, list)):
        return raw_value

    try:
        return json.loads(raw_value)
    except (TypeError, ValueError):
        return None


def _parse_bool(value):
    """Normalize truthy/falsey form values to boolean."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False

    return str(value).lower() not in ('false', '0', 'off', '')
