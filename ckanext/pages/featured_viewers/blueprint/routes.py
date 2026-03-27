"""
Flask routes for Featured Viewers web interface.
"""

import json
import logging
import urllib.parse

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import ckan.plugins.toolkit as tk
from ckan.common import g
from ckan import model

log = logging.getLogger(__name__)

featured_viewers_blueprint = Blueprint(
    'featured_viewers',
    __name__,
    url_prefix='/featured-viewers'
)


def _get_context():
    """Build CKAN context for action calls."""
    return {
        'model': model,
        'session': model.Session,
        'user': g.user,
        'auth_user_obj': g.userobj,
    }


# ============================================================================
# List Route
# ============================================================================

@featured_viewers_blueprint.route('/')
@featured_viewers_blueprint.route('/list')
def index():
    """List all published featured viewers."""
    context = _get_context()

    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 18))
    sort = request.args.get('sort', 'order')
    category_filter = request.args.get('category', '')
    initiative_filter = request.args.get('initiative', '')
    q = request.args.get('q', '')

    offset = (page - 1) * limit

    data_dict = {
        'limit': limit,
        'offset': offset,
        'sort': sort,
        'q': q,
        'status': 'published',
    }

    if category_filter:
        data_dict['category'] = category_filter
    if initiative_filter:
        data_dict['initiative'] = initiative_filter

    # Use ignore_auth for public listing
    list_context = dict(context)
    list_context['ignore_auth'] = True

    try:
        result = tk.get_action('featured_viewer_list')(list_context, data_dict)
        viewers = result['viewers']
        total_count = result['count']
        facets = result.get('facets', {})
    except Exception as e:
        log.error(f"Error listing viewers: {str(e)}")
        model.Session.rollback()
        viewers = []
        total_count = 0
        facets = {}

    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0

    # Get featured viewers for hero section (page 1 only)
    featured_viewers = []
    if page == 1:
        try:
            featured_result = tk.get_action('featured_viewer_list')(list_context, {
                'is_featured': True,
                'status': 'published',
                'limit': 6,
                'sort': 'order',
            })
            featured_viewers = featured_result['viewers']
        except Exception as e:
            log.error(f"Error getting featured viewers: {str(e)}")
            model.Session.rollback()

    # Get categories for filter tabs
    from ckanext.pages.featured_viewers.logic.schema import VIEWER_CATEGORIES

    # Check if user can create
    can_create = False
    can_review = False
    my_drafts = []
    pending_count = 0
    if g.userobj:
        try:
            tk.check_access('featured_viewer_create', context, {})
            can_create = True
        except tk.NotAuthorized:
            pass

        can_review = _can_review_viewers(g.userobj)

        # Get user's draft viewers
        try:
            draft_result = tk.get_action('featured_viewer_list')(list_context, {
                'status': 'draft',
                'author_id': g.userobj.id,
                'limit': 10,
            })
            my_drafts = draft_result.get('viewers', [])
        except Exception:
            pass

        # Get pending review count for reviewers
        if can_review:
            try:
                sub_result = tk.get_action('featured_viewer_list')(list_context, {
                    'status': 'submitted', 'limit': 1,
                })
                rev_result = tk.get_action('featured_viewer_list')(list_context, {
                    'status': 'under_review', 'limit': 1,
                })
                pending_count = sub_result.get('count', 0) + rev_result.get('count', 0)
            except Exception:
                pass

    extra_vars = {
        'viewers': viewers,
        'featured_viewers': featured_viewers,
        'total_count': total_count,
        'page': page,
        'total_pages': total_pages,
        'limit': limit,
        'sort': sort,
        'category_filter': category_filter,
        'initiative_filter': initiative_filter,
        'q': q,
        'facets': facets,
        'categories': VIEWER_CATEGORIES,
        'can_create': can_create,
        'can_review': can_review,
        'my_drafts': my_drafts,
        'pending_count': pending_count,
    }

    return render_template('featured_viewers/list.html', **extra_vars)


# ============================================================================
# Create Route
# ============================================================================

@featured_viewers_blueprint.route('/new', methods=['GET', 'POST'])
def create():
    """Create a new featured viewer."""
    context = _get_context()

    if not g.userobj:
        flash(tk._('Please log in to create a viewer'), 'error')
        return redirect(url_for('user.login'))

    try:
        tk.check_access('featured_viewer_create', context, {})
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to create viewers'))

    from ckanext.pages.featured_viewers.logic.schema import VIEWER_CATEGORIES

    if request.method == 'POST':
        data_dict = _extract_form_data(request.form)

        try:
            viewer = tk.get_action('featured_viewer_create')(context, data_dict)
            flash(tk._('Viewer created successfully'), 'success')
            return redirect(url_for('featured_viewers.show', slug=viewer['slug']))
        except tk.ValidationError as e:
            extra_vars = {
                'data': data_dict,
                'errors': e.error_dict,
                'error_summary': e.error_summary,
                'is_new': True,
                'categories': VIEWER_CATEGORIES,
            }
            return render_template('featured_viewers/edit.html', **extra_vars)
        except Exception as e:
            log.error(f"Error creating viewer: {str(e)}", exc_info=True)
            flash(tk._('Error creating viewer: {}').format(str(e)), 'error')
            extra_vars = {
                'data': data_dict,
                'errors': {},
                'error_summary': {'Error': str(e)},
                'is_new': True,
                'categories': VIEWER_CATEGORIES,
            }
            return render_template('featured_viewers/edit.html', **extra_vars)

    extra_vars = {
        'data': {},
        'errors': {},
        'error_summary': {},
        'is_new': True,
        'categories': VIEWER_CATEGORIES,
    }
    return render_template('featured_viewers/edit.html', **extra_vars)


# ============================================================================
# Show Route
# ============================================================================

@featured_viewers_blueprint.route('/<slug>')
def show(slug):
    """View a single featured viewer with embedded map."""
    context = _get_context()

    try:
        show_context = dict(context)
        show_context['ignore_auth'] = True

        viewer = tk.get_action('featured_viewer_show')(show_context, {
            'slug': slug,
            'include_datasets': True,
        })

        # Check access for non-published
        if viewer.get('status') != 'published':
            try:
                tk.check_access('featured_viewer_show', context, {'id': viewer['id']})
            except tk.NotAuthorized:
                tk.abort(403, tk._('Not authorized to view this viewer'))

        # Record view
        try:
            tk.get_action('featured_viewer_record_view')(
                {'ignore_auth': True}, {'id': viewer['id']}
            )
        except Exception as e:
            log.warning(f"Failed to record view: {str(e)}")
            model.Session.rollback()

    except tk.ObjectNotFound:
        tk.abort(404, tk._('Viewer not found'))
    except Exception as e:
        log.error(f"Error showing viewer: {str(e)}")
        tk.abort(500, tk._('Error loading viewer'))

    # Check edit permission
    can_edit = False
    can_review = False
    can_publish = False
    is_author = False
    if g.userobj:
        try:
            tk.check_access('featured_viewer_update', context, {'id': viewer['id']})
            can_edit = True
        except tk.NotAuthorized:
            pass
        try:
            tk.check_access('featured_viewer_review', context, {'id': viewer['id']})
            can_review = True
        except tk.NotAuthorized:
            pass
        try:
            tk.check_access('featured_viewer_approve', context, {'id': viewer['id']})
            can_publish = True
        except tk.NotAuthorized:
            pass

        from ckanext.pages.featured_viewers.auth.permissions import _is_viewer_author
        is_author = _is_viewer_author(g.user, viewer)

    from ckanext.pages.featured_viewers.logic.schema import VIEWER_CATEGORIES
    from ckanext.pages.featured_viewers.logic.workflow import ViewerWorkflow
    allowed_transitions = ViewerWorkflow.get_allowed_transitions(viewer.get('status', 'draft'))

    extra_vars = {
        'viewer': viewer,
        'can_edit': can_edit,
        'can_review': can_review,
        'can_publish': can_publish,
        'is_author': is_author,
        'categories': VIEWER_CATEGORIES,
        'allowed_transitions': allowed_transitions,
    }

    return render_template('featured_viewers/show.html', **extra_vars)


# ============================================================================
# Edit Route
# ============================================================================

@featured_viewers_blueprint.route('/<slug>/edit', methods=['GET', 'POST'])
def edit(slug):
    """Edit an existing featured viewer."""
    context = _get_context()

    if not g.userobj:
        flash(tk._('Please log in'), 'error')
        return redirect(url_for('user.login'))

    try:
        viewer = tk.get_action('featured_viewer_show')(context, {
            'slug': slug, 'include_datasets': True,
        })
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Viewer not found'))

    try:
        tk.check_access('featured_viewer_update', context, {'id': viewer['id']})
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to edit this viewer'))

    from ckanext.pages.featured_viewers.logic.schema import VIEWER_CATEGORIES

    if request.method == 'POST':
        data_dict = _extract_form_data(request.form)
        data_dict['id'] = viewer['id']

        try:
            updated = tk.get_action('featured_viewer_update')(context, data_dict)
            flash(tk._('Viewer updated successfully'), 'success')
            return redirect(url_for('featured_viewers.show', slug=updated['slug']))
        except tk.ValidationError as e:
            extra_vars = {
                'data': {**viewer, **data_dict},
                'errors': e.error_dict,
                'error_summary': e.error_summary,
                'is_new': False,
                'categories': VIEWER_CATEGORIES,
            }
            return render_template('featured_viewers/edit.html', **extra_vars)

    extra_vars = {
        'data': viewer,
        'errors': {},
        'error_summary': {},
        'is_new': False,
        'categories': VIEWER_CATEGORIES,
    }
    return render_template('featured_viewers/edit.html', **extra_vars)


# ============================================================================
# Delete Route
# ============================================================================

@featured_viewers_blueprint.route('/<slug>/delete', methods=['POST'])
def delete(slug):
    """Delete a featured viewer."""
    context = _get_context()

    if not g.userobj:
        tk.abort(403)

    try:
        viewer = tk.get_action('featured_viewer_show')(context, {'slug': slug})
        tk.get_action('featured_viewer_delete')(context, {'id': viewer['id']})
        flash(tk._('Viewer deleted'), 'success')
    except tk.ObjectNotFound:
        tk.abort(404)
    except tk.NotAuthorized:
        tk.abort(403)

    return redirect(url_for('featured_viewers.index'))


# ============================================================================
# Workflow Routes (submit, publish, review, pending-review)
# ============================================================================

def _can_review_viewers(user_obj):
    """Check if user can review viewers (sysadmin or org admin)."""
    if not user_obj:
        return False
    if user_obj.sysadmin:
        return True
    from ckan import authz as _authz
    return _authz.has_user_permission_for_some_org(user_obj.id, 'admin')


@featured_viewers_blueprint.route('/<slug>/submit', methods=['POST'])
def submit(slug):
    """Submit a viewer for review."""
    log.info(f"[FEATURED_VIEWERS_ROUTE] Submitting viewer: {slug}")

    context = _get_context()

    try:
        viewer = tk.get_action('featured_viewer_show')(context, {'slug': slug})
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Viewer not found'))

    try:
        tk.get_action('featured_viewer_submit')(context, {
            'id': viewer['id'],
        })
        flash(tk._('Viewer submitted for review. An administrator will review it shortly.'), 'success')
    except tk.ValidationError as e:
        error_msg = '; '.join(e.error_summary.values()) if e.error_summary else str(e)
        flash(tk._('Cannot submit viewer: {}').format(error_msg), 'error')
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to submit this viewer'))
    except Exception as e:
        log.error(f"[FEATURED_VIEWERS_ROUTE] Error submitting viewer {slug}: {str(e)}")
        flash(tk._('Error submitting viewer: {}').format(str(e)), 'error')

    return redirect(url_for('featured_viewers.show', slug=slug))


@featured_viewers_blueprint.route('/<slug>/publish', methods=['POST'])
def publish(slug):
    """Publish a viewer directly (for sysadmins/org admins)."""
    log.info(f"[FEATURED_VIEWERS_ROUTE] Publishing viewer: {slug}")

    context = _get_context()

    try:
        viewer = tk.get_action('featured_viewer_show')(context, {'slug': slug})
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Viewer not found'))

    try:
        tk.get_action('featured_viewer_approve')(context, {
            'id': viewer['id'],
        })
        flash(tk._('Viewer published successfully'), 'success')
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to publish this viewer'))
    except Exception as e:
        log.error(f"Error publishing viewer: {str(e)}")
        flash(tk._('Error publishing viewer: {}').format(str(e)), 'error')

    return redirect(url_for('featured_viewers.show', slug=slug))


@featured_viewers_blueprint.route('/<slug>/review', methods=['GET', 'POST'])
def review(slug):
    """Review a submitted viewer."""
    log.info(f"[FEATURED_VIEWERS_ROUTE] Reviewing viewer: {slug}")

    context = _get_context()

    try:
        viewer = tk.get_action('featured_viewer_show')(context, {'slug': slug})
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Viewer not found'))

    try:
        tk.check_access('featured_viewer_review', context, {'id': viewer['id']})
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized to review this viewer'))

    if request.method == 'POST':
        action = request.form.get('action')

        try:
            if action == 'start_review':
                tk.get_action('featured_viewer_review')(context, {'id': viewer['id']})
                flash(tk._('Review started'), 'success')

            elif action == 'approve':
                tk.get_action('featured_viewer_approve')(context, {'id': viewer['id']})
                flash(tk._('Viewer approved and published'), 'success')
                return redirect(url_for('featured_viewers.show', slug=slug))

            elif action == 'request_changes':
                required_changes = request.form.get('required_changes')
                if not required_changes:
                    flash(tk._('Please specify required changes'), 'error')
                else:
                    tk.get_action('featured_viewer_request_changes')(context, {
                        'id': viewer['id'],
                        'required_changes': required_changes,
                    })
                    flash(tk._('Changes requested'), 'success')
                    return redirect(url_for('featured_viewers.show', slug=slug))

        except tk.ValidationError as e:
            error_msg = '; '.join(e.error_summary.values()) if e.error_summary else str(e)
            flash(tk._('Error: {}').format(error_msg), 'error')
        except Exception as e:
            log.error(f"Error in review action: {str(e)}")
            flash(tk._('Error: {}').format(str(e)), 'error')

        # Reload viewer after action
        try:
            viewer = tk.get_action('featured_viewer_show')(context, {'slug': slug})
        except Exception:
            pass

    from ckanext.pages.featured_viewers.logic.schema import VIEWER_CATEGORIES

    extra_vars = {
        'viewer': viewer,
        'categories': VIEWER_CATEGORIES,
    }
    return render_template('featured_viewers/show.html', **extra_vars)


@featured_viewers_blueprint.route('/pending-review')
def pending_review():
    """List viewers pending review."""
    log.info("[FEATURED_VIEWERS_ROUTE] Listing viewers pending review")

    context = _get_context()

    if not g.userobj:
        flash(tk._('Please log in'), 'error')
        return redirect(url_for('user.login'))

    if not _can_review_viewers(g.userobj):
        flash(tk._('You do not have permission to review viewers'), 'error')
        return redirect(url_for('featured_viewers.index'))

    list_context = dict(context)
    list_context['ignore_auth'] = True

    status_filter = request.args.get('status', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    offset = (page - 1) * limit

    # Get submitted viewers
    submitted_viewers = []
    submitted_count = 0
    try:
        if not status_filter or status_filter == 'submitted':
            result = tk.get_action('featured_viewer_list')(list_context, {
                'status': 'submitted', 'limit': limit, 'offset': offset,
            })
            submitted_viewers = result.get('viewers', [])
            submitted_count = result.get('count', 0)
    except Exception as e:
        log.error(f"Error listing submitted viewers: {str(e)}")
        model.Session.rollback()

    # Get under_review viewers
    review_viewers = []
    review_count = 0
    try:
        if not status_filter or status_filter == 'under_review':
            result = tk.get_action('featured_viewer_list')(list_context, {
                'status': 'under_review', 'limit': limit, 'offset': offset,
            })
            review_viewers = result.get('viewers', [])
            review_count = result.get('count', 0)
    except Exception as e:
        log.error(f"Error listing under_review viewers: {str(e)}")
        model.Session.rollback()

    from ckanext.pages.featured_viewers.logic.schema import VIEWER_CATEGORIES

    extra_vars = {
        'submitted_viewers': submitted_viewers,
        'review_viewers': review_viewers,
        'submitted_count': submitted_count,
        'review_count': review_count,
        'total_pending': submitted_count + review_count,
        'status_filter': status_filter,
        'page': page,
        'limit': limit,
        'categories': VIEWER_CATEGORIES,
    }

    return render_template('featured_viewers/pending_review.html', **extra_vars)


# ============================================================================
# Map Room Routes
# ============================================================================

@featured_viewers_blueprint.route('/rooms/')
def rooms_index():
    """List all map rooms."""
    context = _get_context()
    list_context = dict(context)
    list_context['ignore_auth'] = True

    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 18))
    category_filter = request.args.get('category', '')
    initiative_filter = request.args.get('initiative', '')
    q = request.args.get('q', '')
    offset = (page - 1) * limit

    data_dict = {
        'limit': limit,
        'offset': offset,
        'q': q,
        'status': 'published',
    }
    if category_filter:
        data_dict['category'] = category_filter
    if initiative_filter:
        data_dict['initiative'] = initiative_filter

    try:
        result = tk.get_action('map_room_list')(list_context, data_dict)
        rooms = result.get('rooms', [])
        total_count = result.get('count', 0)
    except Exception as e:
        log.error(f"Error listing rooms: {str(e)}")
        model.Session.rollback()
        rooms = []
        total_count = 0

    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0

    can_create = False
    if g.userobj:
        try:
            tk.check_access('map_room_create', context, {})
            can_create = True
        except tk.NotAuthorized:
            pass

    from ckanext.pages.featured_viewers.logic.schema import VIEWER_CATEGORIES

    extra_vars = {
        'rooms': rooms,
        'total_count': total_count,
        'page': page,
        'total_pages': total_pages,
        'limit': limit,
        'category_filter': category_filter,
        'initiative_filter': initiative_filter,
        'q': q,
        'categories': VIEWER_CATEGORIES,
        'can_create': can_create,
    }
    return render_template('featured_viewers/rooms/list.html', **extra_vars)


@featured_viewers_blueprint.route('/rooms/new', methods=['GET', 'POST'])
def rooms_create():
    """Create a new map room."""
    context = _get_context()

    if not g.userobj:
        flash(tk._('Please log in'), 'error')
        return redirect(url_for('user.login'))

    try:
        tk.check_access('map_room_create', context, {})
    except tk.NotAuthorized:
        tk.abort(403, tk._('Not authorized'))

    from ckanext.pages.featured_viewers.logic.schema import VIEWER_CATEGORIES, AVAILABLE_ICONS

    # Fetch all published viewers for the viewer selector
    all_viewers = []
    try:
        viewer_result = tk.get_action('featured_viewer_list')(
            {'ignore_auth': True}, {'status': 'published', 'limit': 200}
        )
        all_viewers = viewer_result.get('viewers', [])
    except Exception:
        pass

    if request.method == 'POST':
        data_dict = _extract_room_form_data(request.form)
        viewer_ids = data_dict.pop('viewer_ids', [])

        try:
            room = tk.get_action('map_room_create')(context, data_dict)
            # Sync selected viewers
            if viewer_ids:
                tk.get_action('sync_room_viewers')(context, {
                    'room_id': room['id'],
                    'viewer_ids': viewer_ids,
                })
            flash(tk._('Map Room created successfully'), 'success')
            return redirect(url_for('featured_viewers.rooms_show', slug=room['slug']))
        except tk.ValidationError as e:
            extra_vars = {
                'data': data_dict,
                'errors': e.error_dict,
                'error_summary': e.error_summary,
                'is_new': True,
                'categories': VIEWER_CATEGORIES,
                'available_icons': AVAILABLE_ICONS,
                'all_viewers': all_viewers,
            }
            return render_template('featured_viewers/rooms/edit.html', **extra_vars)
        except Exception as e:
            log.error(f"Error creating room: {str(e)}")
            flash(str(e), 'error')
            extra_vars = {
                'data': data_dict,
                'errors': {},
                'error_summary': {},
                'is_new': True,
                'categories': VIEWER_CATEGORIES,
                'available_icons': AVAILABLE_ICONS,
                'all_viewers': all_viewers,
            }
            return render_template('featured_viewers/rooms/edit.html', **extra_vars)

    extra_vars = {
        'data': {},
        'errors': {},
        'error_summary': {},
        'is_new': True,
        'categories': VIEWER_CATEGORIES,
        'available_icons': AVAILABLE_ICONS,
        'all_viewers': all_viewers,
    }
    return render_template('featured_viewers/rooms/edit.html', **extra_vars)


@featured_viewers_blueprint.route('/rooms/<slug>')
def rooms_show(slug):
    """Show a map room with its viewers."""
    context = _get_context()

    try:
        show_context = dict(context)
        show_context['ignore_auth'] = True
        room = tk.get_action('map_room_show')(show_context, {
            'slug': slug, 'include_viewers': True,
        })

        if room.get('status') != 'published':
            try:
                tk.check_access('map_room_update', context, {'id': room['id']})
            except tk.NotAuthorized:
                tk.abort(403)
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Map Room not found'))
    except Exception as e:
        log.error(f"Error showing room: {str(e)}")
        tk.abort(500)

    can_edit = False
    if g.userobj:
        try:
            tk.check_access('map_room_update', context, {'id': room['id']})
            can_edit = True
        except tk.NotAuthorized:
            pass

    from ckanext.pages.featured_viewers.logic.schema import VIEWER_CATEGORIES

    extra_vars = {
        'room': room,
        'can_edit': can_edit,
        'categories': VIEWER_CATEGORIES,
    }
    return render_template('featured_viewers/rooms/show.html', **extra_vars)


@featured_viewers_blueprint.route('/rooms/<slug>/edit', methods=['GET', 'POST'])
def rooms_edit(slug):
    """Edit a map room."""
    context = _get_context()

    if not g.userobj:
        flash(tk._('Please log in'), 'error')
        return redirect(url_for('user.login'))

    try:
        room = tk.get_action('map_room_show')(context, {
            'slug': slug, 'include_viewers': True,
        })
    except tk.ObjectNotFound:
        tk.abort(404)

    try:
        tk.check_access('map_room_update', context, {'id': room['id']})
    except tk.NotAuthorized:
        tk.abort(403)

    from ckanext.pages.featured_viewers.logic.schema import VIEWER_CATEGORIES, AVAILABLE_ICONS

    if request.method == 'POST':
        data_dict = _extract_room_form_data(request.form)
        viewer_ids = data_dict.pop('viewer_ids', [])
        data_dict['id'] = room['id']

        try:
            updated = tk.get_action('map_room_update')(context, data_dict)
            # Sync selected viewers
            tk.get_action('sync_room_viewers')(context, {
                'room_id': room['id'],
                'viewer_ids': viewer_ids,
            })
            flash(tk._('Map Room updated'), 'success')
            return redirect(url_for('featured_viewers.rooms_show', slug=updated['slug']))
        except tk.ValidationError as e:
            all_viewers = []
            try:
                viewer_result = tk.get_action('featured_viewer_list')(
                    {'ignore_auth': True}, {'status': 'published', 'limit': 200}
                )
                all_viewers = viewer_result.get('viewers', [])
            except Exception:
                pass
            extra_vars = {
                'data': {**room, **data_dict},
                'errors': e.error_dict,
                'error_summary': e.error_summary,
                'is_new': False,
                'categories': VIEWER_CATEGORIES,
                'available_icons': AVAILABLE_ICONS,
                'all_viewers': all_viewers,
            }
            return render_template('featured_viewers/rooms/edit.html', **extra_vars)

    # Fetch all published viewers for the "add viewer" selector
    all_viewers = []
    try:
        viewer_result = tk.get_action('featured_viewer_list')(
            {'ignore_auth': True}, {'status': 'published', 'limit': 200}
        )
        all_viewers = viewer_result.get('viewers', [])
    except Exception:
        pass

    extra_vars = {
        'data': room,
        'errors': {},
        'error_summary': {},
        'is_new': False,
        'categories': VIEWER_CATEGORIES,
        'available_icons': AVAILABLE_ICONS,
        'all_viewers': all_viewers,
    }
    return render_template('featured_viewers/rooms/edit.html', **extra_vars)


@featured_viewers_blueprint.route('/rooms/<slug>/delete', methods=['POST'])
def rooms_delete(slug):
    """Delete a map room."""
    context = _get_context()

    if not g.userobj:
        tk.abort(403)

    try:
        room = tk.get_action('map_room_show')(context, {'slug': slug})
        tk.get_action('map_room_delete')(context, {'id': room['id']})
        flash(tk._('Map Room deleted'), 'success')
    except tk.ObjectNotFound:
        tk.abort(404)
    except tk.NotAuthorized:
        tk.abort(403)

    return redirect(url_for('featured_viewers.rooms_index'))


@featured_viewers_blueprint.route('/rooms/<slug>/add-viewer', methods=['POST'])
def rooms_add_viewer(slug):
    """Add a viewer to a room."""
    context = _get_context()

    try:
        room = tk.get_action('map_room_show')(context, {'slug': slug})
        viewer_id = request.form.get('viewer_id')
        if viewer_id:
            tk.get_action('map_room_add_viewer')(context, {
                'room_id': room['id'],
                'viewer_id': viewer_id,
            })
            flash(tk._('Viewer added to room'), 'success')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('featured_viewers.rooms_edit', slug=slug))


@featured_viewers_blueprint.route('/rooms/<slug>/remove-viewer', methods=['POST'])
def rooms_remove_viewer(slug):
    """Remove a viewer from a room."""
    context = _get_context()

    try:
        room = tk.get_action('map_room_show')(context, {'slug': slug})
        viewer_id = request.form.get('viewer_id')
        if viewer_id:
            tk.get_action('map_room_remove_viewer')(context, {
                'room_id': room['id'],
                'viewer_id': viewer_id,
            })
            flash(tk._('Viewer removed from room'), 'success')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('featured_viewers.rooms_edit', slug=slug))


# ============================================================================
# API: Resolve Terria Share Link
# ============================================================================

@featured_viewers_blueprint.route('/api/resolve-share-link')
def resolve_share_link():
    """
    Resolve a Terria share link and return the full JSON config.

    Handles two formats:
    - #share=ID  -> fetches from Terria server /share/{ID}
    - #start=JSON -> decodes the URL-encoded JSON

    Query params:
        url: Full Terria share URL

    Returns:
        JSON: {success: true, config: {...}, base_url: "..."}
    """
    if not g.user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 403

    share_url = request.args.get('url', '').strip()
    if not share_url:
        return jsonify({'success': False, 'error': 'Missing url parameter'}), 400

    try:
        parsed = urllib.parse.urlparse(share_url)
        fragment = parsed.fragment

        # SSRF protection: only allow known Terria domains
        allowed_domains = [
            'map.dev-wins.com',
            'terria.water-data.org',
            'data210.dev-wins.com',
        ]
        try:
            configured = tk.config.get('ckanext.pages.terria_base_url', '')
            if configured:
                from urllib.parse import urlparse as _urlparse
                configured_host = _urlparse(configured).netloc
                if configured_host:
                    allowed_domains.append(configured_host)
        except Exception:
            pass

        if not parsed.netloc or parsed.netloc not in allowed_domains:
            return jsonify({
                'success': False,
                'error': 'Domain not allowed. Allowed: {}'.format(
                    ', '.join(allowed_domains))
            }), 400

        if parsed.scheme not in ('http', 'https'):
            return jsonify({
                'success': False, 'error': 'Only http/https URLs are allowed'
            }), 400

        base_url = '{scheme}://{netloc}{path}'.format(
            scheme=parsed.scheme,
            netloc=parsed.netloc,
            path=parsed.path.rstrip('/') + '/'
        )

        if not fragment:
            return jsonify({
                'success': False,
                'error': 'URL has no fragment (#share= or #start=)'
            }), 400

        # Parse fragment as key=value params
        hash_params = urllib.parse.parse_qs(fragment)

        # Handle #share=ID
        share_id = hash_params.get('share', [None])[0]
        if share_id:
            import requests as http_requests
            endpoint = '{base}share/{sid}'.format(
                base=base_url, sid=urllib.parse.quote(share_id, safe='')
            )
            log.info('Resolving Terria share link: %s', endpoint)
            resp = http_requests.get(endpoint, timeout=15)
            resp.raise_for_status()

            config = resp.json()
            return jsonify({
                'success': True,
                'config': config,
                'base_url': base_url,
                'source': 'share',
            })

        # Handle #start=JSON
        start_value = hash_params.get('start', [None])[0]
        if start_value:
            # Try direct parse, then URL-decoded parse
            config = None
            candidates = [start_value]
            if '%' in start_value:
                try:
                    candidates.append(urllib.parse.unquote(start_value))
                except Exception:
                    pass

            for candidate in candidates:
                try:
                    config = json.loads(candidate)
                    break
                except (json.JSONDecodeError, TypeError):
                    continue

            if config is None:
                return jsonify({
                    'success': False,
                    'error': 'Could not parse #start payload as JSON'
                }), 400

            return jsonify({
                'success': True,
                'config': config,
                'base_url': base_url,
                'source': 'start',
            })

        return jsonify({
            'success': False,
            'error': 'URL fragment must contain #share= or #start='
        }), 400

    except Exception as e:
        log.error('Error resolving Terria share link: %s', str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to resolve share link'
        }), 500


@featured_viewers_blueprint.route('/api/save-to-terria', methods=['POST'])
def save_to_terria():
    """
    Save a Terria JSON config to the Terria share service.

    Posts the config to Terria's /share endpoint and returns the
    short share URL with #share=ID.

    Request body (JSON):
        config: Terria config object
        base_url: (optional) Terria instance base URL

    Returns:
        JSON: {success: true, share_url: "https://.../#share=ID", share_id: "ID"}
    """
    if not g.user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 403

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid JSON body'}), 400

    config = data.get('config')
    if not config or not isinstance(config, dict):
        return jsonify({'success': False, 'error': 'Missing or invalid config object'}), 400

    base_url = (data.get('base_url') or 'https://map.dev-wins.com/').rstrip('/') + '/'

    # Validate domain
    allowed_domains = [
        'map.dev-wins.com',
        'terria.water-data.org',
        'data210.dev-wins.com',
    ]
    try:
        configured = tk.config.get('ckanext.pages.terria_base_url', '')
        if configured:
            configured_host = urllib.parse.urlparse(configured).netloc
            if configured_host:
                allowed_domains.append(configured_host)
    except Exception:
        pass

    parsed_base = urllib.parse.urlparse(base_url)
    if parsed_base.netloc not in allowed_domains:
        return jsonify({
            'success': False,
            'error': 'Domain not allowed: {}'.format(parsed_base.netloc)
        }), 400

    try:
        import requests as http_requests
        share_endpoint = '{}share'.format(base_url)
        log.info('Saving config to Terria share: %s', share_endpoint)

        resp = http_requests.post(
            share_endpoint,
            json=config,
            headers={'Content-Type': 'application/json'},
            timeout=15,
        )
        resp.raise_for_status()

        result = resp.json()
        share_id = result.get('id')
        if not share_id:
            return jsonify({
                'success': False,
                'error': 'Terria did not return a share ID'
            }), 502

        share_url = '{}#share={}'.format(base_url, share_id)
        return jsonify({
            'success': True,
            'share_id': share_id,
            'share_url': share_url,
            'base_url': base_url,
        })

    except Exception as e:
        log.error('Error saving to Terria share: %s', str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to save config to Terria'
        }), 500


@featured_viewers_blueprint.route('/api/search-terria-datasets')
def search_terria_datasets():
    """
    Search CKAN datasets that have resources with terria-compatible formats.

    Query params:
        q: search query (default '')
        limit: max results (default 10)

    Returns:
        JSON: {success: true, results: [{id, title, name, organization, resources: [...]}]}
    """
    if not g.user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 403

    q = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 50)

    try:
        context = _get_context()
        terria_formats = [
            'shp', 'wms', 'wfs', 'kml', 'geojson', 'czml',
            'wmts', 'tif', 'tiff', 'geotiff', 'cog', 'csv', 'json',
            'esri rest'
        ]

        # Build fq to filter datasets with compatible resources
        fq_parts = []
        format_clauses = ' OR '.join(
            'res_format:"{}"'.format(f) for f in terria_formats
        )
        fq_parts.append('({})'.format(format_clauses))

        search_result = tk.get_action('package_search')(context, {
            'q': q or '*:*',
            'fq': ' '.join(fq_parts),
            'rows': limit,
            'include_private': False,
        })

        results = []
        for pkg in search_result.get('results', []):
            compatible_resources = []
            for res in pkg.get('resources', []):
                fmt = (res.get('format') or '').lower()
                if fmt in terria_formats:
                    compatible_resources.append({
                        'id': res.get('id'),
                        'name': res.get('name') or res.get('description') or res.get('url', ''),
                        'format': res.get('format', ''),
                        'url': res.get('url', ''),
                    })

            if compatible_resources:
                org = pkg.get('organization') or {}
                results.append({
                    'id': pkg.get('id'),
                    'title': pkg.get('title', ''),
                    'name': pkg.get('name', ''),
                    'organization': org.get('title', ''),
                    'organization_image': org.get('image_display_url', ''),
                    'resources': compatible_resources,
                })

        return jsonify({
            'success': True,
            'count': search_result.get('count', 0),
            'results': results,
        })

    except Exception as e:
        log.error('Error searching terria datasets: %s', str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to search datasets'
        }), 500


# ============================================================================
# Helpers
# ============================================================================

def _extract_form_data(form):
    """Extract viewer data from form submission."""
    data_dict = {
        'title': form.get('title', '').strip(),
        'slug': form.get('slug', '').strip(),
        'description': form.get('description', '').strip(),
        'category': form.get('category', 'general'),
        'initiative': form.get('initiative', '').strip() or None,
        'icon_class': form.get('icon_class', '').strip(),
        'thumbnail_url': form.get('thumbnail_url', '').strip(),
        'terria_share_link': form.get('terria_share_link', '').strip(),
        'meta_description': form.get('meta_description', '').strip(),
        'organization_id': form.get('organization_id', '').strip() or None,
    }

    # JSONB fields
    for field in ('terria_config', 'map_layers', 'tags', 'countries'):
        raw = form.get(field, '')
        if raw:
            try:
                data_dict[field] = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                data_dict[field] = raw
        else:
            data_dict[field] = []

    # Boolean fields
    data_dict['is_featured'] = form.get('is_featured') == 'on'
    data_dict['is_public'] = form.get('is_public', 'on') == 'on'

    # Order
    order = form.get('order_index', '0')
    try:
        data_dict['order_index'] = int(order)
    except (ValueError, TypeError):
        data_dict['order_index'] = 0

    # Status
    data_dict['status'] = form.get('status', 'draft')

    return data_dict


def _extract_room_form_data(form):
    """Extract map room data from form submission."""
    data_dict = {
        'title': form.get('title', '').strip(),
        'slug': form.get('slug', '').strip(),
        'description': form.get('description', '').strip(),
        'thumbnail_url': form.get('thumbnail_url', '').strip(),
        'category': form.get('category', 'general'),
        'initiative': form.get('initiative', '').strip() or None,
        'status': form.get('status', 'draft'),
        'is_featured': form.get('is_featured') == 'on',
    }

    order = form.get('order_index', '0')
    try:
        data_dict['order_index'] = int(order)
    except (ValueError, TypeError):
        data_dict['order_index'] = 0

    # Collect selected viewer IDs from checkboxes
    data_dict['viewer_ids'] = form.getlist('viewer_ids')

    return data_dict
