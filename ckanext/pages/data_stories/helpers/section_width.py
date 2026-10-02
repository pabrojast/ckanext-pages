"""Section width shared by authoring validation and all story renderers."""
import json
import math


def normalize_section_width(width):
    """Return a validated width; missing settings keep the legacy layout."""
    if width is None:
        return {'mode': 'normal'}
    if not isinstance(width, dict) or width.get('mode') not in ('normal', 'full', 'custom'):
        raise ValueError('Choose Normal, 100% of screen or Custom for section width.')
    mode = width['mode']
    if mode != 'custom':
        return {'mode': mode}
    value, unit = width.get('value'), width.get('unit')
    try:
        finite = isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:
        finite = False
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not finite or value <= 0
            or unit not in ('%', 'px') or (unit == '%' and value > 100)):
        raise ValueError('Section width must be positive pixels or a percentage greater than 0 and at most 100.')
    return {'mode': mode, 'value': value, 'unit': unit}


def _presentation_blocks(section):
    blocks = section.get('blocks_metadata')
    if isinstance(blocks, str):
        try:
            blocks = json.loads(blocks)
        except (TypeError, ValueError):
            blocks = None
    return [block for block in blocks if isinstance(block, dict)
            and block.get('type') == 'presentation'] if isinstance(blocks, list) else []


def get_section_width(section):
    """Build safe CSS from metadata, tolerating malformed historical settings."""
    presentations = _presentation_blocks(section)
    try:
        width = normalize_section_width(presentations[-1].get('width') if presentations else None)
    except ValueError:
        width = {'mode': 'normal'}
    css = ''
    if width['mode'] == 'full':
        css = '100%'
    elif width['mode'] == 'custom':
        css = '%s%s' % (format(width['value'], '.15g'), width['unit'])
    return dict(width, css=css)


def validate_story_section_widths(sections):
    """Validate before any story/section writes, including API and imports."""
    from ckan.plugins import toolkit as tk

    for index, section in enumerate(sections):
        for presentation in _presentation_blocks(section):
            try:
                normalize_section_width(presentation.get('width'))
            except ValueError as error:
                raise tk.ValidationError({
                    'sections': ['Section %d: %s' % (index + 1, error)]
                }) from error
