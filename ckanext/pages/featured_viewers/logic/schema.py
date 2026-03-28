"""
Validation schemas and slug utilities for Featured Viewers.
"""

import re
import logging
import unicodedata

from ckan.plugins.toolkit import get_validator

log = logging.getLogger(__name__)

not_empty = get_validator('not_empty')
ignore_missing = get_validator('ignore_missing')
not_missing = get_validator('not_missing')
unicode_safe = get_validator('unicode_safe')


def featured_viewer_schema():
    """Validation schema for creating/updating a featured viewer."""
    return {
        'title': [not_empty, unicode_safe],
        'slug': [ignore_missing, unicode_safe],
        'description': [ignore_missing, unicode_safe],
        'category': [ignore_missing, unicode_safe],
        'initiative': [ignore_missing, unicode_safe],
        'icon_class': [ignore_missing, unicode_safe],
        'thumbnail_url': [ignore_missing, unicode_safe],
        'terria_share_link': [ignore_missing, unicode_safe],
        'meta_description': [ignore_missing, unicode_safe],
        'organization_id': [ignore_missing, unicode_safe],
    }


def generate_slug(title):
    """Generate a URL-friendly slug from a title."""
    if not title:
        return ''

    # Normalize unicode characters
    slug = unicodedata.normalize('NFKD', title)
    slug = slug.encode('ascii', 'ignore').decode('ascii')
    slug = slug.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')

    return slug[:200]


def validate_slug(slug):
    """Validate a slug format."""
    if not slug:
        return False, 'Slug cannot be empty'

    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', slug) and len(slug) > 1:
        return False, 'Slug must contain only lowercase letters, numbers, and hyphens'

    if len(slug) > 200:
        return False, 'Slug must be 200 characters or less'

    return True, None


# Valid categories for featured viewers
VIEWER_CATEGORIES = {
    'flood-drought': {
        'title': 'Flood & Drought Monitoring',
        'icon': 'fa-tint',
        'color': '#1565C0',
    },
    'water-quality': {
        'title': 'Water Quality',
        'icon': 'fa-flask',
        'color': '#2E7D32',
    },
    'groundwater': {
        'title': 'Groundwater Resources',
        'icon': 'fa-arrow-circle-down',
        'color': '#5D4037',
    },
    'climate-change': {
        'title': 'Climate Change & Water',
        'icon': 'fa-thermometer-half',
        'color': '#E65100',
    },
    'urban-water': {
        'title': 'Urban Water Management',
        'icon': 'fa-building',
        'color': '#6A1B9A',
    },
    'ecohydrology': {
        'title': 'Ecohydrology',
        'icon': 'fa-leaf',
        'color': '#1B5E20',
    },
    'citizen-science': {
        'title': 'Citizen Science',
        'icon': 'fa-users',
        'color': '#00838F',
    },
    'iot-monitoring': {
        'title': 'IoT Monitoring',
        'icon': 'fa-microchip',
        'color': '#37474F',
    },
    'transboundary': {
        'title': 'Transboundary Waters',
        'icon': 'fa-globe',
        'color': '#0277BD',
    },
    'sdg6': {
        'title': 'SDG 6 Indicators',
        'icon': 'fa-bullseye',
        'color': '#00695C',
    },
    'general': {
        'title': 'General',
        'icon': 'fa-map',
        'color': '#0072BC',
    },
}


# Icons available in the visual picker
AVAILABLE_ICONS = [
    'fa-map', 'fa-globe', 'fa-tint', 'fa-flask', 'fa-leaf',
    'fa-thermometer-half', 'fa-building', 'fa-users', 'fa-microchip',
    'fa-bullseye', 'fa-arrow-circle-down', 'fa-water', 'fa-cloud-rain',
    'fa-chart-bar', 'fa-chart-line', 'fa-database', 'fa-layer-group',
    'fa-satellite', 'fa-compass', 'fa-mountain', 'fa-fish', 'fa-tree',
    'fa-sun', 'fa-wind', 'fa-bolt', 'fa-shield-alt', 'fa-recycle',
    'fa-industry', 'fa-city', 'fa-road', 'fa-ship',
]


def map_room_schema():
    """Validation schema for creating/updating a map room."""
    return {
        'title': [not_empty, unicode_safe],
        'slug': [ignore_missing, unicode_safe],
        'description': [ignore_missing, unicode_safe],
        'thumbnail_url': [ignore_missing, unicode_safe],
        'category': [ignore_missing, unicode_safe],
        'initiative': [ignore_missing, unicode_safe],
        'organization_id': [ignore_missing, unicode_safe],
        'countries': [ignore_missing],
    }
