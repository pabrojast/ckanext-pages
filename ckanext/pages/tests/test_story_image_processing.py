import importlib.util
import io
from pathlib import Path

import pytest
from PIL import Image

spec = importlib.util.spec_from_file_location('story_image_processing',
    Path(__file__).parents[1] / 'story_image_processing.py')
processing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processing)


def raster(fmt='PNG', size=(20, 30), mode='RGBA'):
    data = io.BytesIO()
    Image.new(mode, size, (10, 30, 90, 80) if mode == 'RGBA' else 'red').save(data, fmt)
    return data.getvalue()


def test_resize_keeps_alpha_and_format():
    result, (ext, mime), dimensions = processing.prepare_image(raster(size=(3200, 2000)))
    assert (ext, mime, dimensions) == ('png', 'image/png', (1600, 1000))
    image = Image.open(io.BytesIO(result))
    assert image.mode == 'RGBA'
    assert image.getpixel((0, 0))[3] == 80


def test_animation_keeps_all_frames():
    data = io.BytesIO()
    Image.new('RGB', (20, 20), 'red').save(data, 'GIF', save_all=True,
        append_images=[Image.new('RGB', (20, 20), 'blue')], duration=100, loop=0)
    result, (_, mime), size = processing.prepare_image(data.getvalue())
    assert result == data.getvalue()
    assert mime == 'image/gif'
    assert Image.open(io.BytesIO(result)).n_frames == 2


@pytest.mark.parametrize('raw', [b'', b'GIF89a', b'<svg></svg>', b'<html>image.png</html>'])
def test_invalid_content_is_rejected(raw):
    with pytest.raises(ValueError):
        processing.prepare_image(raw)


def test_pixel_budget(monkeypatch):
    monkeypatch.setattr(processing, 'MAX_PIXELS', 20)
    with pytest.raises(ValueError):
        processing.prepare_image(raster())


def test_nested_story_fields_and_legacy_json_are_checked():
    assert processing.has_pending_images({'blocks': [{'content': '<img src="DATA:image/png;base64,eA==">'}]})
    assert processing.has_pending_images({'blocks_metadata': '{"url":"blob:https://example.test/id"}'})
    assert not processing.has_pending_images({'url': 'https://example.test/story-images/id'})
