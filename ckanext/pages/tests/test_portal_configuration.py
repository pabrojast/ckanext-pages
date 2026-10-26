"""Portal settings retain the default routes and support custom branding."""
import importlib.util
from pathlib import Path

import pytest
from flask import Flask

from ckan.plugins import toolkit as tk
from ckanext.pages import plugin
from ckanext.pages.data_stories.helpers.terria import get_terria_base_url
from ckanext.pages.featured_viewers.blueprint.routes import (
    _default_terria_base, _terria_hosts,
)


@pytest.fixture(autouse=True)
def portal_settings(monkeypatch):
    for key in (
        'ckanext.pages.water_family.enabled', 'ckanext.pages.terria_base_url',
        'ckanext.featured_viewers.extra_terria_hosts',
        'ckanext.data_stories.hero_image', 'ckanext.featured_viewers.hero_image',
    ):
        monkeypatch.delitem(tk.config, key, raising=False)
    monkeypatch.setitem(tk.config, 'ckan.site_url', 'https://portal.example/')


@pytest.mark.parametrize('setting,enabled', [(None, True), ('true', True), ('false', False)])
def test_water_family_route_switch_keeps_core_pages(monkeypatch, setting, enabled):
    if setting is not None:
        monkeypatch.setitem(tk.config, 'ckanext.pages.water_family.enabled', setting)
    path = Path(__file__).resolve().parents[1] / 'blueprint.py'
    spec = importlib.util.spec_from_file_location('pages_config_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app = Flask(__name__)
    app.register_blueprint(module.pages)
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    assert 'pages.pages_index' in endpoints
    assert 'pages.blog_index' in endpoints
    for endpoint in ('rapid_response_index', 'water_family_index', 'water_news_index',
                     'water_events_index', 'open_source_software_index',
                     'ai_water_tools_index', 'crida_index', 'event_types_admin',
                     'disaster_types_admin'):
        assert ('pages.' + endpoint in endpoints) is enabled


def test_terria_defaults_to_this_portal():
    assert get_terria_base_url() == 'https://portal.example/terria'
    assert _default_terria_base() == 'https://portal.example/terria/'
    assert _terria_hosts() == ['portal.example']


def test_explicit_terria_and_additional_hosts(monkeypatch):
    base = 'https://maps.example/viewer/'
    monkeypatch.setitem(tk.config, 'ckanext.pages.terria_base_url', base)
    monkeypatch.setitem(tk.config, 'ckanext.featured_viewers.extra_terria_hosts',
                        'legacy.example maps.example legacy.example')
    assert get_terria_base_url() == base
    assert _default_terria_base() == base
    assert _terria_hosts() == ['maps.example', 'portal.example', 'legacy.example']


@pytest.mark.parametrize('module,helper,default', [
    ('data_stories', plugin.get_data_stories_hero_image, '/Landing_page/Content/IHPTITLE02DATASTORIES.jpg'),
    ('featured_viewers', plugin.get_featured_viewers_hero_image, '/Landing_page/Content/IHPTITLE04VIEWERS.jpg'),
])
def test_hero_defaults_and_override(monkeypatch, module, helper, default):
    assert helper() == default
    monkeypatch.setitem(tk.config, 'ckanext.' + module + '.hero_image', '/custom/hero.jpg')
    assert helper() == '/custom/hero.jpg'
