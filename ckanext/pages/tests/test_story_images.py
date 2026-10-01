"""Exercise real CKAN auth, persistence and public serving on an isolated DB."""
import io

import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage

from ckan import model
from ckan.plugins import toolkit as tk
from ckan.tests import factories, helpers
from ckanext.pages.story_images import StoryImage


def photo(name='photo.png'):
    buffer = io.BytesIO()
    Image.new('RGBA', (24, 16), (50, 100, 150, 80)).save(buffer, 'PNG')
    buffer.seek(0)
    return FileStorage(stream=buffer, filename=name, content_type='image/png')


@pytest.mark.usefixtures('with_plugins', 'clean_db')
@pytest.mark.ckan_config('ckan.plugins', 'pages image_view')
class TestStoryImages:
    def create(self, user, file=None):
        return helpers.call_action('story_image_create', {'user': user['name']}, upload=file or photo())

    def test_upload_deduplicates_and_archiving_preserves_file(self, tmp_path, monkeypatch, app):
        monkeypatch.setitem(tk.config, 'ckan.storage_path', str(tmp_path))
        owner = factories.User()
        first = self.create(owner)
        second = self.create(owner)
        assert first['id'] == second['id']
        assert '/story-images/' in first['url']
        assert first['size'] > 0
        helpers.call_action('story_image_update', {'user': owner['name']}, id=first['id'], archived=True)
        listing = helpers.call_action('story_image_list', {'user': owner['name']})
        assert listing['count'] == 0
        archived = helpers.call_action('story_image_list', {'user': owner['name']}, archived=True)
        assert archived['count'] == 1
        response = app.get('/story-images/' + first['id'])
        assert response.status_code == 200
        assert response.headers['Content-Type'].startswith('image/png')
        assert Image.open(io.BytesIO(response.data)).getpixel((0, 0))[3] == 80
        assert self.create(owner)['archived'] is False

    def test_other_user_cannot_list_or_modify(self, tmp_path, monkeypatch):
        monkeypatch.setitem(tk.config, 'ckan.storage_path', str(tmp_path))
        owner, other = factories.User(), factories.User()
        image = self.create(owner)
        with pytest.raises(tk.NotAuthorized):
            helpers.call_action('story_image_list', {'user': other['name']}, owner_id=owner['id'])
        with pytest.raises(tk.NotAuthorized):
            helpers.call_action('story_image_update', {'user': other['name']}, id=image['id'], alt='changed')
        assert helpers.call_action('story_image_list', {'user': other['name']})['items'] == []
        # Identical bytes owned by different people have independent library entries.
        assert self.create(other)['id'] != image['id']

    def test_anonymous_upload_is_denied(self):
        with pytest.raises(tk.NotAuthorized):
            helpers.call_action('story_image_create', {'user': ''}, upload=photo())

    def test_invalid_upload_never_creates_a_record(self, tmp_path, monkeypatch):
        monkeypatch.setitem(tk.config, 'ckan.storage_path', str(tmp_path))
        owner = factories.User()
        bad = FileStorage(stream=io.BytesIO(b'<svg/>'), filename='image.png', content_type='image/png')
        with pytest.raises(tk.ValidationError):
            self.create(owner, bad)
        assert model.Session.query(StoryImage).count() == 0

    def test_storage_failure_is_not_a_success(self, monkeypatch):
        owner = factories.User()
        from ckanext.pages import story_images
        def fail(*args):
            raise OSError('Storage unavailable')
        monkeypatch.setattr(story_images.uploader, 'get_uploader', fail)
        with pytest.raises(OSError):
            self.create(owner)
        assert model.Session.query(StoryImage).count() == 0

    def test_new_story_inline_image_is_rejected(self):
        owner = factories.User()
        with pytest.raises(tk.ValidationError):
            helpers.call_action('data_story_create', {'user': owner['name']},
                title='Inline', abstract='<img src="data:image/png;base64,eA==">')

    def test_browser_requires_csrf_and_private_library(self, tmp_path, monkeypatch, app):
        monkeypatch.setitem(tk.config, 'ckan.storage_path', str(tmp_path))
        owner = factories.User()
        env = {'REMOTE_USER': owner['name']}
        anonymous = app.test_client()
        app = app.test_client()
        settings = app.get('/story-images/upload', extra_environ=env)
        assert settings.status_code == 200
        assert settings.headers['Cache-Control'] == 'private, no-store'
        missing = app.post('/story-images/upload', data={'upload': photo()}, extra_environ=env)
        assert missing.status_code == 400
        valid = app.post('/story-images/upload', data={'upload': photo()},
            headers={'X-CSRFToken': settings.json['csrf_token']}, extra_environ=env)
        assert valid.status_code == 200, valid.json
        assert valid.json['uploaded'] == 1
        no_csrf_api = app.post('/api/3/action/story_image_update',
            json={'id': valid.json['id'], 'archived': True}, extra_environ=env)
        assert no_csrf_api.status_code in (400, 409)
        update = app.post('/api/3/action/story_image_update',
            json={'id': valid.json['id'], 'alt': 'River'},
            headers={'X-CSRFToken': settings.json['csrf_token']}, extra_environ=env)
        assert update.status_code == 200
        assert update.json['result']['alt'] == 'River'
        page = app.get('/user/' + owner['name'] + '/story-images', extra_environ=env)
        assert page.status_code == 200, page.data
        assert 'story-image-library' in page.data.decode()
        picker_page = app.get('/story-images/library', extra_environ=env)
        assert picker_page.status_code == 200, picker_page.data
        assert anonymous.get('/story-images/library').status_code == 403
        listing = app.get('/api/3/action/story_image_list', extra_environ=env)
        assert listing.headers['Cache-Control'] == 'private, no-store'
