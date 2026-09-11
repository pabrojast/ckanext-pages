"""Image conversion and display helpers for Rapid Response only."""

import base64
import binascii
import hashlib
import io
import re
from html.parser import HTMLParser

from PIL import Image, ImageOps


DATA_IMAGE_RE = re.compile(
    r'data:image/[a-zA-Z0-9.+-]+;base64,[a-zA-Z0-9+/=\r\n]+', re.I)


def walk_images(value, resolve):
    """Replace data URIs without reserializing HTML or changing JSON types."""
    if isinstance(value, str):
        return DATA_IMAGE_RE.sub(lambda m: resolve(m.group()), value)
    if isinstance(value, list):
        return [walk_images(item, resolve) for item in value]
    if isinstance(value, dict):
        return {key: walk_images(item, resolve) for key, item in value.items()}
    return value


def decode_image(uri):
    try:
        raw = base64.b64decode(''.join(uri.split(',', 1)[1].split()), validate=True)
    except (ValueError, IndexError, binascii.Error) as exc:
        raise ValueError('Invalid base64 image') from exc
    if not raw:
        raise ValueError('Empty image')
    return raw


def optimize_image(raw):
    """Return display bytes, extension, MIME, and dimensions; keep animations."""
    with Image.open(io.BytesIO(raw)) as source:
        image_format = source.format
        formats = {'JPEG': ('jpg', 'image/jpeg'), 'PNG': ('png', 'image/png'),
                   'WEBP': ('webp', 'image/webp'), 'GIF': ('gif', 'image/gif')}
        if image_format not in formats:
            raise ValueError('Unsupported inline image format: %s' % image_format)
        extension, mime = formats[image_format]
        if getattr(source, 'is_animated', False):
            source.verify()
            return raw, extension, mime, source.size
        source.load()
        image = ImageOps.exif_transpose(source)
        original_size = image.size
        image.thumbnail((1600, 1600), getattr(Image, 'Resampling', Image).LANCZOS)
        output = io.BytesIO()
        if image_format == 'JPEG':
            image.convert('RGB').save(output, 'JPEG', quality=80, optimize=True)
        elif image_format == 'PNG':
            image.save(output, 'PNG', optimize=True)
        elif image_format == 'WEBP':
            image.save(output, 'WEBP', quality=80)
        else:
            image.save(output, 'GIF')
        result = output.getvalue()
        if image.size == original_size and len(result) >= len(raw):
            result = raw
        return result, extension, mime, image.size


def digest(value):
    return hashlib.sha256(value).hexdigest()


class _LazyMediaParser(HTMLParser):
    """Collect insertions into existing tags, keeping the HTML byte-for-byte."""

    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.line_offsets = [0]
        for match in re.finditer('\n', text):
            self.line_offsets.append(match.end())
        self.insertions = []

    def handle_starttag(self, tag, attrs):
        if tag not in ('img', 'iframe'):
            return
        attrs = dict(attrs)
        additions = ''
        if 'loading' not in attrs:
            additions += ' loading="lazy"'
        if tag == 'img' and 'decoding' not in attrs:
            additions += ' decoding="async"'
        if additions:
            raw = self.get_starttag_text()
            line, column = self.getpos()
            end = self.line_offsets[line - 1] + column + len(raw) - 1
            if raw.endswith('/>'):
                end -= 1
            self.insertions.append((end, additions))

    handle_startendtag = handle_starttag


def lazy_media_html(value):
    """Call after CKAN's HTML rendering/sanitization, not instead of it."""
    if not value:
        return value
    text = str(value)
    parser = _LazyMediaParser(text)
    parser.feed(text)
    for offset, addition in reversed(parser.insertions):
        text = text[:offset] + addition + text[offset:]
    return text
