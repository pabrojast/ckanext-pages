"""Run with pytest --noconftest; media utilities do not require CKAN/DB."""
import base64
import io
import json

import pytest
from PIL import Image

from ckanext.pages.rapid_response_media import (
    decode_image, digest, lazy_media_html, optimize_image, walk_images,
)


def image_bytes(size=(2400, 1800), mode='RGB', fmt='JPEG'):
    image = Image.new(mode, size, (15, 110, 180, 70) if mode == 'RGBA' else (15, 110, 180))
    output = io.BytesIO()
    image.save(output, fmt)
    return output.getvalue()


def test_large_photo_becomes_small_display_file():
    original = image_bytes()
    output, ext, mime, size = optimize_image(original)
    assert size == (1600, 1200)
    assert (ext, mime) == ('jpg', 'image/jpeg')
    assert len(output) < len(original)
    assert Image.open(io.BytesIO(output)).size == size


def test_transparency_survives():
    raw = image_bytes((2400, 1800), 'RGBA', 'PNG')
    output, ext, mime, size = optimize_image(raw)
    image = Image.open(io.BytesIO(output))
    assert image.getpixel((0, 0))[3] == 70
    assert (ext, mime, size) == ('png', 'image/png', (1600, 1200))


def test_small_images_are_not_upscaled():
    assert optimize_image(image_bytes((64, 32)))[3] == (64, 32)


def test_animation_is_byte_identical():
    stream = io.BytesIO()
    frames = [Image.new('RGB', (16, 16), color) for color in ('red', 'blue')]
    frames[0].save(stream, 'GIF', save_all=True, append_images=frames[1:], loop=0)
    raw = stream.getvalue()
    assert optimize_image(raw)[0] == raw


def test_invalid_image_does_not_convert():
    with pytest.raises(Exception):
        optimize_image(b'not an image')
    with pytest.raises(ValueError):
        decode_image('data:image/png;base64,%%%')


def test_nested_blocks_revisions_and_legacy_json_preserve_types():
    uri = 'data:image/jpeg;base64,' + base64.b64encode(image_bytes((4, 4))).decode()
    html = '<p class="ql-align-center"><img style="width: 40%" src="' + uri + '"></p>'
    values = {'content': html, 'blocks': [{'content': html, 'id': 'impact-1'}],
              'legacy': json.dumps([{'content': html}]),
              'revisions': {'r1': {'content': html, 'created': '2026-09-01', 'current': True}}}
    result = walk_images(values, lambda _: 'https://assets.example/photo.jpg')
    assert uri in values['content']
    assert isinstance(result['legacy'], str)
    assert result['blocks'][0]['id'] == 'impact-1'
    assert result['revisions']['r1']['current'] is True
    assert 'data:image' not in json.dumps(result)
    assert 'class="ql-align-center"' in result['content']
    assert 'style="width: 40%"' in result['content']
    assert walk_images(result, lambda _: pytest.fail('converted twice')) == result
    assert digest(decode_image(uri)) == digest(image_bytes((4, 4)))


def test_lazy_media_retains_markup_and_iframe_attributes():
    html = ('<blockquote>Text &amp; more</blockquote>\n'
            '<p class="ql-align-center"><img src="/image.png" width="600" /></p>'
            '<div style="height:920px"><iframe src="/terria/#share=abc" '
            'allowfullscreen height="920" width="100%"></iframe></div>')
    rendered = lazy_media_html(html)
    assert rendered.replace(' loading="lazy"', '').replace(' decoding="async"', '') == html
    assert rendered.count('loading="lazy"') == 2
    assert lazy_media_html(rendered) == rendered


def test_explicit_loading_and_code_samples_are_preserved():
    html = ('<img src="/cover.jpg" loading="eager" decoding="sync">'
            '<pre>&lt;iframe src="example"&gt;</pre>'
            '<script>var example = "<img src=x>";</script>')
    assert lazy_media_html(html) == html


def test_no_content():
    assert lazy_media_html(None) is None
    assert walk_images({'value': None, 'count': 2}, None) == {'value': None, 'count': 2}
