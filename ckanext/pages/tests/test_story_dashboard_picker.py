"""Picker language is scoped to the iframe, never persisted in CKAN's session."""
import json
import unittest
from unittest.mock import patch

from flask import Flask
from ckanext.pages import story_dashboards


class DashboardPickerLanguageTest(unittest.TestCase):
    def test_allowlist_and_normal_language_fallback(self):
        cases = [('en', 'es', 'en'), ('es', 'en', 'es'), (None, 'es_CL', 'es'),
                 ('fr', 'es-CL', 'es'), ('<script>', 'en', 'en'),
                 ('ES', 'fr', 'en'), (None, None, 'en'), (None, 'de', 'en')]
        for requested, current, expected in cases:
            with self.subTest(requested=requested, current=current):
                self.assertEqual(story_dashboards.picker_language(requested, current), expected)

    def test_route_keeps_session_language_and_security_headers(self):
        app = Flask(__name__)
        app.secret_key = 'isolated-picker-language-test'
        app.register_blueprint(story_dashboards.blueprint)
        client = app.test_client()
        with client.session_transaction() as session:
            session['language'] = 'fr'
        with patch.object(story_dashboards.h, 'lang', return_value='es-CL'), \
                patch.object(story_dashboards.tk, 'render', side_effect=lambda _, context: json.dumps(context)):
            for query, expected in [('?lang=en', 'en'), ('?lang=es', 'es'),
                                    ('?lang=unsupported', 'es'), ('', 'es')]:
                response = client.get('/story-dashboards/picker' + query)
                self.assertEqual(response.status_code, 200)
                context = json.loads(response.data)
                self.assertEqual(context['picker_language'], expected)
                self.assertTrue(context['picker_csrf'])
                self.assertEqual(response.headers['Cache-Control'], 'private, no-store')
                self.assertEqual(response.headers['X-Frame-Options'], 'SAMEORIGIN')
                with client.session_transaction() as session:
                    self.assertEqual(session['language'], 'fr')


if __name__ == '__main__':
    unittest.main()
