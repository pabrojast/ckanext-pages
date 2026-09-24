"""Declarative story visuals. URLs are generated from CKAN view IDs, never HTML."""
import re
import math
from uuid import UUID


def identifier(value):
    return value if isinstance(value, str) and re.fullmatch(r'[\w-]{1,128}', value) else None


def dashboard_state(value):
    value = value if isinstance(value, dict) else {}
    filters = value.get('filters') or []
    if not isinstance(filters, list) or len(filters) > 24:
        raise ValueError('Use at most 24 story filters.')
    result = []
    for item in filters:
        if not isinstance(item, dict) or not isinstance(item.get('field'), str):
            raise ValueError('Invalid story filter.')
        op = item.get('op')
        values = item.get('value') if op in ('in', 'between') else [item.get('value')]
        if (op not in ('eq', 'in', 'gte', 'lte', 'between') or not isinstance(values, list)
                or not 1 <= len(values) <= 1000 or (op == 'between' and len(values) != 2)
                or any(not isinstance(v, (str, int, float, bool)) or
                       (isinstance(v, float) and not math.isfinite(v)) for v in values)):
            raise ValueError('Invalid story filter value.')
        result.append({k: item[k] for k in ('field', 'op', 'value')})
    return {'filters': result, 'widgetId': identifier(value.get('widgetId'))}


def dashboard_block(block):
    try:
        view_id = str(UUID(str(block.get('view_id'))))
        return {'type': 'dashboard', 'version': 1,
                'id': identifier(block.get('id')) or view_id,
                'view_id': view_id, 'title': str(block.get('title') or 'Dashboard'),
                'state': dashboard_state(block.get('state')),
                'url': '/dashboard/%s/embed' % view_id}
    except (ValueError, TypeError, AttributeError):
        return {'type': 'visual_error', 'message': 'This dashboard reference is invalid.'}


def references(block):
    result = []
    raw = block.get('references') or []
    if not isinstance(raw, list):
        return result
    for ref in raw[:100]:
        if not isinstance(ref, dict) or not identifier(ref.get('id')):
            continue
        try:
            result.append({'id': ref['id'], 'version': 1,
                           'source_id': identifier(ref.get('source_id')),
                           'slide_id': ref.get('slide_id') if isinstance(ref.get('slide_id'), str) and len(ref['slide_id']) <= 512 else None,
                           'dashboard_id': identifier(ref.get('dashboard_id')),
                           'state': dashboard_state(ref.get('state')),
                           'on_enter': bool(ref.get('on_enter'))})
        except ValueError:
            continue
    return result
