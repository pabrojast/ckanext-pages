"""Bounded raster validation and normalization for story images."""
import io
import re
import warnings

from PIL import Image, ImageOps

FORMATS = {'JPEG': ('jpg', 'image/jpeg'), 'PNG': ('png', 'image/png'),
           'WEBP': ('webp', 'image/webp'), 'GIF': ('gif', 'image/gif')}
MAX_PIXELS = 25000000
MAX_ANIMATION_PIXELS = 100000000
MAX_FRAMES = 500


def prepare_image(raw):
    """Decode before accepting; preserve animation and alpha, remove static EXIF."""
    if not raw:
        raise ValueError('Choose an image file.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                fmt = source.format
                if fmt not in FORMATS:
                    raise ValueError('Choose a JPEG, PNG, WebP or GIF image.')
                width, height = source.size
                frames = getattr(source, 'n_frames', 1)
                if width * height > MAX_PIXELS or frames > MAX_FRAMES:
                    raise ValueError('Image dimensions or animation exceed the limit.')
                if frames > 1:
                    if width * height * frames > MAX_ANIMATION_PIXELS:
                        raise ValueError('Animation exceeds the decoded image limit.')
                    for frame in range(frames):
                        source.seek(frame)
                        source.load()
                    return raw, FORMATS[fmt], (width, height)
                source.load()
                image = ImageOps.exif_transpose(source)
                image.thumbnail((1600, 1600), getattr(Image, 'Resampling', Image).LANCZOS)
                output = io.BytesIO()
                if fmt == 'JPEG':
                    image.convert('RGB').save(output, 'JPEG', quality=85, optimize=True)
                elif fmt == 'WEBP':
                    image.save(output, 'WEBP', quality=85)
                else:
                    image.save(output, fmt)
                return output.getvalue(), FORMATS[fmt], image.size
    except (ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise ValueError('Invalid image or image dimensions exceed the limit.')
    except (OSError, SyntaxError, EOFError) as exc:
        raise ValueError('The file is not a valid supported image.') from exc


def has_pending_images(value):
    """Inspect nested story fields, including JSON encoded block metadata."""
    if isinstance(value, str):
        return bool(re.search(r'(?:data\s*:\s*image/|blob\s*:)', value, re.I))
    if isinstance(value, dict):
        return any(has_pending_images(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(has_pending_images(item) for item in value)
    return False


def validate_story_images(data):
    if has_pending_images(data):
        from ckan.plugins import toolkit as tk
        raise tk.ValidationError({'images': [tk._(
            'Please wait for image uploads to finish, then save again. Your draft has been kept.') ]})
