"""Same-origin dashboard chooser shared with the native Terria story editor."""
from flask import Blueprint, make_response, request
from flask_wtf.csrf import generate_csrf
from ckan.lib import helpers as h
from ckan.plugins import toolkit as tk

blueprint = Blueprint('story_dashboards', __name__)


def picker_language(requested, current):
    """An embed may choose EN/ES without changing CKAN's session language."""
    if requested in ('en', 'es'):
        return requested
    normal = str(current or 'en').lower().replace('_', '-').split('-')[0]
    return normal if normal in ('en', 'es') else 'en'


@blueprint.route('/story-dashboards/picker')
def picker():
    # All searches and previews use the current CKAN session and normal actions.
    response = make_response(tk.render('story_dashboards/picker.html', {
        'picker_csrf': generate_csrf(),
        'picker_language': picker_language(request.args.get('lang'), h.lang()),
    }))
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response
