"""
Flask Blueprint for Data Stories Web UI

Provides web routes for viewing, creating, and managing data stories
through a browser interface.
"""

from ckanext.pages.data_stories.blueprint.routes import data_stories_blueprint

__all__ = ['data_stories_blueprint']
