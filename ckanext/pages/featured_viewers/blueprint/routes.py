"""
Flask routes for Featured Viewers web interface.
"""

import json
import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash
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
    if g.userobj:
        try:
            tk.check_access('featured_viewer_create', context, {})
            can_create = True
        except tk.NotAuthorized:
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
        'q': q,
        'facets': facets,
        'categories': VIEWER_CATEGORIES,
        'can_create': can_create,
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
            log.error(f"Error creating viewer: {str(e)}")
            flash(tk._('Error creating viewer: {}').format(str(e)), 'error')
            extra_vars = {
                'data': data_dict,
                'errors': {},
                'error_summary': {},
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
    if g.userobj:
        try:
            tk.check_access('featured_viewer_update', context, {'id': viewer['id']})
            can_edit = True
        except tk.NotAuthorized:
            pass

    from ckanext.pages.featured_viewers.logic.schema import VIEWER_CATEGORIES

    extra_vars = {
        'viewer': viewer,
        'can_edit': can_edit,
        'categories': VIEWER_CATEGORIES,
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

    if request.method == 'POST':
        data_dict = _extract_room_form_data(request.form)

        try:
            room = tk.get_action('map_room_create')(context, data_dict)
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
            }
            return render_template('featured_viewers/rooms/edit.html', **extra_vars)

    extra_vars = {
        'data': {},
        'errors': {},
        'error_summary': {},
        'is_new': True,
        'categories': VIEWER_CATEGORIES,
        'available_icons': AVAILABLE_ICONS,
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
        data_dict['id'] = room['id']

        try:
            updated = tk.get_action('map_room_update')(context, data_dict)
            flash(tk._('Map Room updated'), 'success')
            return redirect(url_for('featured_viewers.rooms_show', slug=updated['slug']))
        except tk.ValidationError as e:
            extra_vars = {
                'data': {**room, **data_dict},
                'errors': e.error_dict,
                'error_summary': e.error_summary,
                'is_new': False,
                'categories': VIEWER_CATEGORIES,
                'available_icons': AVAILABLE_ICONS,
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
# Helpers
# ============================================================================

def _extract_form_data(form):
    """Extract viewer data from form submission."""
    data_dict = {
        'title': form.get('title', '').strip(),
        'slug': form.get('slug', '').strip(),
        'description': form.get('description', '').strip(),
        'category': form.get('category', 'general'),
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
        'status': form.get('status', 'draft'),
        'is_featured': form.get('is_featured') == 'on',
    }

    order = form.get('order_index', '0')
    try:
        data_dict['order_index'] = int(order)
    except (ValueError, TypeError):
        data_dict['order_index'] = 0

    return data_dict
