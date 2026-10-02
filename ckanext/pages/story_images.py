"""Personal story image library, independent of Data Stories being enabled."""
import datetime
import hashlib
import io
import logging
import os
import uuid

import sqlalchemy as sa
from flask import Blueprint, has_request_context, jsonify, redirect, request, send_file
from flask_wtf.csrf import generate_csrf, validate_csrf
from wtforms.validators import ValidationError as CsrfError
from werkzeug.datastructures import FileStorage

from ckan import model
from ckan.lib import uploader
from ckan.plugins import toolkit as tk
from ckanext.pages.db import BaseModel
from ckanext.pages.story_image_processing import prepare_image, MAX_PIXELS

log = logging.getLogger(__name__)
blueprint = Blueprint('story_images', __name__)
STORAGE_TYPE = 'story_images'


class StoryImage(BaseModel):
    __tablename__ = 'ckanext_pages_story_images'
    id = sa.Column(sa.UnicodeText, primary_key=True)
    owner_id = sa.Column(sa.UnicodeText, sa.ForeignKey('user.id', ondelete='SET NULL'))
    filename = sa.Column(sa.UnicodeText, nullable=False)
    storage_kind = sa.Column(sa.UnicodeText, nullable=False)
    original_name = sa.Column(sa.UnicodeText, nullable=False)
    digest = sa.Column(sa.String(64), nullable=False)
    mime = sa.Column(sa.UnicodeText, nullable=False)
    size = sa.Column(sa.Integer, nullable=False)
    width = sa.Column(sa.Integer, nullable=False)
    height = sa.Column(sa.Integer, nullable=False)
    alt = sa.Column(sa.UnicodeText, nullable=False, default='')
    caption = sa.Column(sa.UnicodeText, nullable=False, default='')
    credit = sa.Column(sa.UnicodeText, nullable=False, default='')
    archived = sa.Column(sa.Boolean, nullable=False, default=False)
    created_at = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    __table_args__ = (sa.UniqueConstraint('owner_id', 'digest', name='story_image_owner_digest'),
                      sa.Index('story_image_owner_created', 'owner_id', 'created_at'))


def _user(context):
    user = model.User.get(context.get('user')) if context.get('user') else None
    if not user or user.state != 'active':
        raise tk.NotAuthorized('Sign in to use your images.')
    return user


def _owner(context, data):
    user = _user(context)
    owner = model.User.get(data.get('owner_id')) if data.get('owner_id') else user
    if not owner or (owner.id != user.id and not user.sysadmin):
        raise tk.NotAuthorized('You can only manage your own images.')
    return owner


def _item(context, data):
    user = _user(context)
    item = model.Session.query(StoryImage).get(data.get('id'))
    if item is None:
        raise tk.ObjectNotFound('Image not found.')
    if item.owner_id != user.id and not user.sysadmin:
        raise tk.NotAuthorized('You can only manage your own images.')
    return item


def auth_create(context, data_dict=None):
    try:
        _user(context)
        return {'success': True}
    except tk.NotAuthorized:
        return {'success': False}


def auth_list(context, data_dict=None):
    try:
        _owner(context, data_dict or {})
        return {'success': True}
    except tk.NotAuthorized:
        return {'success': False}


def auth_update(context, data_dict=None):
    try:
        _item(context, data_dict or {})
        return {'success': True}
    except (tk.NotAuthorized, tk.ObjectNotFound):
        return {'success': False}


def _csrf():
    # Action API routes are normally CSRF exempt in CKAN; protect these too.
    if has_request_context():
        token = request.headers.get('X-CSRFToken') or request.form.get('_csrf_token')
        try:
            validate_csrf(token)
        except CsrfError as exc:
            raise tk.ValidationError({'csrf': ['Refresh the page and try again.']}) from exc


def _serialize(item):
    return {'id': item.id, 'url': tk.url_for('story_images.file', image_id=item.id, _external=True),
            'name': item.original_name, 'mime': item.mime, 'size': item.size,
            'width': item.width, 'height': item.height, 'alt': item.alt,
            'caption': item.caption, 'credit': item.credit, 'archived': item.archived,
            'created_at': item.created_at.isoformat()}


def story_image_create(context, data_dict):
    tk.check_access('story_image_create', context, data_dict)
    user = _user(context)
    _csrf()
    upload = data_dict.get('upload')
    if not isinstance(upload, FileStorage) or not upload.filename:
        raise tk.ValidationError({'upload': ['Choose an image file.']})
    limit = int(uploader.get_max_image_size() * 1024 * 1024)
    raw = upload.stream.read(limit + 1)
    if len(raw) > limit:
        raise tk.ValidationError({'upload': ['Image exceeds the portal upload limit.']})
    digest = hashlib.sha256(raw).hexdigest()
    try:
        content, (extension, mime), dimensions = prepare_image(raw)
    except ValueError as exc:
        raise tk.ValidationError({'upload': [str(exc)]}) from exc
    if len(content) > limit:
        raise tk.ValidationError({'upload': ['Prepared image exceeds the portal upload limit.']})
    # Serialize matching uploads across workers, including first upload races.
    if model.Session.bind.dialect.name == 'postgresql':
        key = int.from_bytes(hashlib.sha256((user.id + digest).encode()).digest()[:8], 'big', signed=True)
        model.Session.execute(sa.text('SELECT pg_advisory_xact_lock(:key)'), {'key': key})
    item = model.Session.query(StoryImage).filter_by(owner_id=user.id, digest=digest).first()
    if item:
        item.archived = False
        model.Session.commit()
        return dict(_serialize(item), uploaded=1, fileName=item.original_name)
    image_id = str(uuid.uuid4())
    values = {'upload': FileStorage(stream=io.BytesIO(content),
                                   filename=image_id + '.' + extension, content_type=mime)}
    # No silent local fallback if the configured backend fails.
    store = uploader.get_uploader(STORAGE_TYPE)
    store.update_data_dict(values, 'image_url', 'upload', 'clear_upload')
    store.upload(uploader.get_max_image_size())
    filename = store.filename
    if not filename or os.path.basename(filename) != filename:
        raise tk.ValidationError({'upload': ['Storage returned an invalid filename.']})
    item = StoryImage(id=image_id, owner_id=user.id, filename=filename,
                      storage_kind='asset' if hasattr(store, '_storage') else 'local',
                      original_name=os.path.basename(upload.filename)[:255], digest=digest,
                      mime=mime, size=len(content), width=dimensions[0], height=dimensions[1],
                      alt=os.path.splitext(os.path.basename(upload.filename))[0][:500])
    model.Session.add(item)
    model.Session.commit()
    return dict(_serialize(item), uploaded=1, fileName=item.original_name)


@tk.side_effect_free
def story_image_list(context, data_dict):
    tk.check_access('story_image_list', context, data_dict)
    owner = _owner(context, data_dict)
    try:
        offset = max(0, int(data_dict.get('offset', 0)))
        limit = min(100, max(1, int(data_dict.get('limit', 24))))
    except (ValueError, TypeError):
        raise tk.ValidationError({'pagination': ['Invalid pagination.']})
    query = model.Session.query(StoryImage).filter_by(owner_id=owner.id)
    query = query.filter_by(archived=tk.asbool(data_dict.get('archived', False)))
    term = str(data_dict.get('q', '')).strip()[:200]
    if term:
        pattern = '%' + term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        query = query.filter(sa.or_(StoryImage.original_name.ilike(pattern, escape='\\'),
                                   StoryImage.alt.ilike(pattern, escape='\\')))
    count = query.count()
    items = query.order_by(StoryImage.created_at.desc(), StoryImage.id).offset(offset).limit(limit).all()
    return {'items': [_serialize(item) for item in items], 'count': count, 'offset': offset, 'limit': limit}


def story_image_update(context, data_dict):
    tk.check_access('story_image_update', context, data_dict)
    item = _item(context, data_dict)
    _csrf()
    changes = {}
    for key, maximum in [('alt', 500), ('caption', 2000), ('credit', 500)]:
        if key in data_dict:
            value = data_dict[key]
            if not isinstance(value, str) or len(value) > maximum:
                raise tk.ValidationError({key: ['Text is too long or invalid.']})
            changes[key] = value
    if 'archived' in data_dict:
        try:
            changes['archived'] = tk.asbool(data_dict['archived'])
        except ValueError as exc:
            raise tk.ValidationError({'archived': ['Expected true or false.']}) from exc
    for key, value in changes.items():
        setattr(item, key, value)
    model.Session.commit()
    return _serialize(item)


def _context():
    return {'user': getattr(tk.g, 'user', None)}


def _private(response):
    request.environ['__no_cache__'] = True
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['CDN-Cache-Control'] = 'no-store'
    response.headers['Surrogate-Control'] = 'no-store'
    response.headers['Vary'] = 'Cookie, Authorization'
    return response


@blueprint.after_app_request
def private_api_cache(response):
    if request.path.startswith('/api/') and '/action/story_image_' in request.path:
        return _private(response)
    return response


@blueprint.route('/story-images/upload', methods=['GET', 'POST'])
def upload():
    try:
        _user(_context())
        if request.method == 'GET':
            return _private(jsonify(csrf_token=generate_csrf(),
                                    max_bytes=int(uploader.get_max_image_size() * 1024 * 1024),
                                    max_pixels=MAX_PIXELS))
        result = tk.get_action('story_image_create')(_context(), {'upload': request.files.get('upload')})
        return _private(jsonify(result))
    except tk.NotAuthorized:
        return _private(jsonify(uploaded=0, error={'message': 'Sign in to upload images.'})), 401
    except tk.ValidationError as exc:
        return _private(jsonify(uploaded=0, error={'message': str(exc)})), 400
    except Exception:
        model.Session.rollback()
        log.exception('Story image upload failed')
        return _private(jsonify(uploaded=0, error={'message': 'Upload failed. Your draft has been kept; please retry.'})), 503


@blueprint.route('/story-images/<uuid:image_id>')
def file(image_id):
    image_id = str(image_id)
    item = model.Session.query(StoryImage).get(image_id)
    if item is None:
        tk.abort(404, 'Image not found.')
    if item.storage_kind == 'asset':
        from ckanext.asset_storage.uploader import get_configured_storage
        from ckanext.asset_storage.storage.exc import ObjectNotFound
        try:
            target = get_configured_storage().download(STORAGE_TYPE + '/' + item.filename)
        except ObjectNotFound:
            tk.abort(404, 'Image not found.')
        if target.fileobj:
            response = send_file(target.fileobj, mimetype=item.mime)
        else:
            response = redirect(target.redirect_to, code=302)
            # Never cache redirects carrying expiring storage credentials.
            request.environ['__no_cache__'] = True
            response.headers['Cache-Control'] = 'no-store'
    else:
        directory = uploader.Upload(STORAGE_TYPE).storage_path
        if not directory:
            tk.abort(503, 'Image storage is not configured.')
        response = send_file(os.path.join(directory, item.filename), mimetype=item.mime)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@blueprint.route('/story-images/library', endpoint='picker')
@blueprint.route('/user/<id>/story-images')
def library(id=None):
    try:
        owner = _owner(_context(), {'owner_id': id} if id else {})
    except tk.NotAuthorized:
        tk.abort(403, 'Sign in to view your image library.')
    user = tk.get_action('user_show')(_context(), {'id': owner.id, 'include_num_followers': True})
    picker = id is None
    html = tk.render('story_images/picker.html' if picker else 'story_images/library.html',
                     extra_vars={'user': user, 'user_dict': user, 'is_myself': owner.id == _user(_context()).id,
                                 'is_sysadmin': _user(_context()).sysadmin,
                                 'picker': picker, 'image_owner_id': owner.id})
    from flask import make_response
    return _private(make_response(html))
