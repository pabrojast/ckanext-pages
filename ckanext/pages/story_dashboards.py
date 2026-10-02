"""Same-origin dashboard chooser shared with the native Terria story editor."""
from flask import Blueprint, make_response
from flask_wtf.csrf import generate_csrf
from ckan.plugins import toolkit as tk

blueprint = Blueprint('story_dashboards', __name__)


@blueprint.route('/story-dashboards/picker')
def picker():
    # All searches and previews use the current CKAN session and normal actions.
    response = make_response(tk.render('story_dashboards/picker.html', {
        'picker_csrf': generate_csrf(),
    }))
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response
