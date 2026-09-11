"""Reversible, per-page migration of inline Rapid Response images."""

import gzip
import io
import json
import os
from pathlib import Path
from urllib.parse import quote, urlparse

import click
import requests
import sqlalchemy as sa
from werkzeug.datastructures import FileStorage

from ckan import model
from ckan.lib import uploader
from ckan.plugins import toolkit as tk

from ckanext.pages.db import Page
from ckanext.pages.rapid_response_media import (
    decode_image, digest, optimize_image, walk_images,
)


FIELDS = ('content', 'extras', 'revisions')


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      default=str, separators=(',', ':')).encode('utf-8')


def fingerprint(row):
    return digest(encoded(row))


def atomic_json(path, value, compressed=False):
    temporary = path.with_name(path.name + '.tmp')
    payload = encoded(value)
    with open(temporary, 'wb') as stream:
        os.chmod(temporary, 0o600)
        stream.write(gzip.compress(payload) if compressed else payload)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def read_json(path, compressed=False):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if compressed else raw)


def snapshot(page_id, lock=False):
    query = sa.select(Page.__table__).where(Page.id == page_id)
    if lock:
        query = query.with_for_update()
    row = model.Session.execute(query).mappings().first()
    return json.loads(encoded(dict(row))) if row else None


def replace_snapshot(row, resolver):
    result = dict(row)
    result['content'] = walk_images(row.get('content'), resolver)
    extras = row.get('extras')
    if extras:
        parsed = json.loads(extras)
        changed = walk_images(parsed, resolver)
        # Do not rewrite extras when there are no images to replace.
        if changed != parsed:
            result['extras'] = json.dumps(changed, ensure_ascii=False)
    result['revisions'] = walk_images(row.get('revisions'), resolver)
    return result


def commit_page(before, after):
    """Avoid overwriting a save made while files were being uploaded."""
    try:
        current = snapshot(before['id'], lock=True)
        if fingerprint(current) != fingerprint(before):
            raise ValueError('Page changed during conversion; retry from a new backup')
        model.Session.execute(
            sa.update(Page.__table__).where(Page.id == before['id']).values(
                **{key: after[key] for key in FIELDS}))
        model.Session.commit()
    except Exception:
        model.Session.rollback()
        raise


def verify_asset(url, expected):
    with requests.get(url, timeout=(10, 45), stream=True) as response:
        response.raise_for_status()
        output = io.BytesIO()
        for chunk in response.iter_content(65536):
            output.write(chunk)
            if output.tell() > len(expected):
                raise ValueError('Uploaded image size does not match')
        if digest(output.getvalue()) != digest(expected):
            raise ValueError('Uploaded image checksum does not match')


def upload_display(data, extension, mime):
    upload = uploader.get_uploader('page_images')
    filename = 'rr-%s.%s' % (digest(data), extension)
    values = {'upload': FileStorage(stream=io.BytesIO(data),
                                    filename=filename, content_type=mime)}
    upload.update_data_dict(values, 'image_url', 'upload', 'clear_upload')
    upload.upload(uploader.get_max_image_size())
    url = values.get('image_url') or upload.filename
    if not url:
        raise ValueError('Uploader returned no URL')
    if urlparse(url).scheme not in ('http', 'https'):
        url = tk.config['ckan.site_url'].rstrip('/') + '/uploads/page_images/' + quote(url)
    verify_asset(url, data)
    return url


@click.command('optimize-rapid-response-images')
@click.option('--page', 'page_name', help='Limit the operation to one page slug')
@click.option('--apply', 'do_apply', is_flag=True, help='Upload images and update pages')
@click.option('--backup-dir', type=click.Path(file_okay=False),
              help='Required for --apply; stores full rows, originals and manifest')
@click.option('--restore', type=click.Path(exists=True, dir_okay=False),
              help='Restore pages from this manifest (requires --apply)')
def optimize_rapid_response_images(page_name, do_apply, backup_dir, restore):
    """Audit by default. Convert images only with --apply and --backup-dir.

    Copy backups outside the pod. A full external database/row backup must
    already exist before a production conversion. Restore refuses to
    overwrite pages edited after the conversion; uploaded files are retained.
    """
    if restore:
        return restore_pages(Path(restore), do_apply, page_name)
    if do_apply and not backup_dir:
        raise click.UsageError('--apply requires --backup-dir')
    root = Path(backup_dir) if backup_dir else None
    manifest = {'version': 1, 'site': tk.config.get('ckan.site_url'),
                'pages': {}, 'images': {}}
    if do_apply:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        manifest_path = root / 'manifest.json'
        if manifest_path.exists():
            manifest = read_json(manifest_path)
            if manifest['site'] != tk.config.get('ckan.site_url'):
                raise click.ClickException('Backup belongs to a different site')
    query = sa.select(Page.id).where(Page.page_type == 'rapid-response')
    if page_name:
        query = query.where(Page.name == page_name)
    ids = [row[0] for row in model.Session.execute(query)]
    model.Session.rollback()
    failures = []
    converted = 0
    for page_id in ids:
        before = snapshot(page_id)
        model.Session.rollback()
        count = [0]

        def count_image(uri):
            count[0] += 1
            return uri

        replace_snapshot(before, count_image)
        if not count[0]:
            click.echo('%s: no inline images' % before['name'])
            continue
        click.echo('%s: %d image occurrences, including revisions' % (
            before['name'], count[0]))
        if not do_apply:
            continue
        try:
            backup_file = root / (page_id + '.before.json.gz')
            if backup_file.exists():
                if fingerprint(read_json(backup_file, True)) != fingerprint(before):
                    raise ValueError('Existing backup differs; use a new backup directory')
            else:
                atomic_json(backup_file, before, True)
            entry = {'name': before['name'], 'before': backup_file.name,
                     'before_sha256': fingerprint(before), 'status': 'prepared'}
            manifest['pages'][page_id] = entry
            atomic_json(manifest_path, manifest)
            uri_cache = {}

            def resolve(uri):
                uri_key = digest(uri.encode())
                if uri_key in uri_cache:
                    return uri_cache[uri_key]
                raw = decode_image(uri)
                key = digest(raw)
                if key not in manifest['images']:
                    original = root / (key + '.original')
                    if not original.exists():
                        with open(original, 'xb') as stream:
                            os.chmod(original, 0o600)
                            stream.write(raw)
                            stream.flush()
                            os.fsync(stream.fileno())
                    if digest(original.read_bytes()) != key:
                        raise ValueError('Original image backup checksum mismatch')
                    display, ext, mime, size = optimize_image(raw)
                    url = upload_display(display, ext, mime)
                    manifest['images'][key] = {
                        'original': original.name, 'original_bytes': len(raw),
                        'display_bytes': len(display), 'display_sha256': digest(display),
                        'url': url, 'width': size[0], 'height': size[1]}
                    atomic_json(manifest_path, manifest)
                else:
                    display, _, _, _ = optimize_image(raw)
                    verify_asset(manifest['images'][key]['url'], display)
                uri_cache[uri_key] = manifest['images'][key]['url']
                return uri_cache[uri_key]

            after = replace_snapshot(before, resolve)
            entry['after_sha256'] = fingerprint(after)
            # Persist rollback information BEFORE committing the database.
            atomic_json(manifest_path, manifest)
            commit_page(before, after)
            entry['status'] = 'applied'
            atomic_json(manifest_path, manifest)
            converted += 1
            click.echo('  converted; content %d -> %d bytes' % (
                len((before['content'] or '').encode()), len((after['content'] or '').encode())))
        except Exception as exc:
            model.Session.rollback()
            failures.append(before['name'])
            click.echo('  FAILED: %s' % exc, err=True)
    click.echo('%s: %d pages checked, %d converted' % (
        'Applied' if do_apply else 'Dry-run', len(ids), converted))
    if failures:
        raise click.ClickException('Conversion failed for: ' + ', '.join(failures))


def restore_pages(path, do_apply, page_name):
    manifest = read_json(path)
    if manifest.get('site') != tk.config.get('ckan.site_url'):
        raise click.ClickException('Backup belongs to a different site')
    for page_id, entry in manifest['pages'].items():
        if page_name and entry['name'] != page_name:
            continue
        before = read_json(path.parent / entry['before'], True)
        if fingerprint(before) != entry['before_sha256']:
            raise click.ClickException('Backup checksum mismatch')
        current = snapshot(page_id)
        model.Session.rollback()
        current_hash = fingerprint(current)
        if current_hash == entry['before_sha256']:
            click.echo('%s: already restored' % entry['name'])
            continue
        if current_hash != entry.get('after_sha256'):
            raise click.ClickException('%s changed since conversion; refusing overwrite' % entry['name'])
        if do_apply:
            commit_page(current, before)
        click.echo('%s: %s' % (entry['name'], 'restored' if do_apply else 'would restore'))


def get_commands():
    return [optimize_rapid_response_images]
