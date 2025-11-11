# encoding: utf-8
"""
Terria integration helpers for data stories.

Provides utilities for working with Terria map configurations,
share links, and embedding Terria visualizations.
"""

import json
import re
import logging
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Dict, Optional, List, Any, Tuple

log = logging.getLogger(__name__)


def get_terria_base_url():
    """
    Get the base URL for Terria instance from CKAN config.

    Returns:
        str: Base URL for Terria (e.g., 'https://terria.water-data.org')
    """
    from ckan.plugins import toolkit as tk

    default_url = 'https://terria.water-data.org'
    return tk.config.get('ckanext.pages.terria_base_url', default_url)


def parse_terria_share_link(share_link: str) -> Optional[Dict[str, Any]]:
    """
    Parse a Terria share link and extract the initialization data.

    Terria share links contain base64-encoded JSON in the URL fragment.
    Format: https://terria.example.com/#share=abc123

    Args:
        share_link: Full Terria share URL

    Returns:
        dict: Parsed initialization data, or None if parsing fails

    Example:
        >>> config = parse_terria_share_link('https://terria.water-data.org/#share=abc123')
        >>> print(config['initSources'])
    """
    if not share_link or not isinstance(share_link, str):
        return None

    try:
        # Parse URL
        parsed = urlparse(share_link)

        # Extract fragment (everything after #)
        fragment = parsed.fragment
        if not fragment:
            log.warning("No fragment found in Terria share link")
            return None

        # Parse fragment parameters
        # Format: #share=abc123 or #start={"initSources":[...]}
        if fragment.startswith('share='):
            # This is a share ID, we cannot directly parse the config
            # without calling Terria's API
            share_id = fragment.replace('share=', '')
            return {
                'type': 'share_id',
                'share_id': share_id,
                'share_link': share_link,
                'base_url': f"{parsed.scheme}://{parsed.netloc}",
            }

        elif fragment.startswith('start='):
            # This is direct initialization JSON
            json_str = fragment.replace('start=', '')
            # URL decode
            import urllib.parse
            json_str = urllib.parse.unquote(json_str)

            # Parse JSON
            init_data = json.loads(json_str)
            return {
                'type': 'init_json',
                'init_data': init_data,
                'share_link': share_link,
                'base_url': f"{parsed.scheme}://{parsed.netloc}",
            }
        else:
            log.warning(f"Unknown fragment format: {fragment}")
            return None

    except Exception as e:
        log.error(f"Error parsing Terria share link: {str(e)}")
        return None


def generate_terria_embed_url(init_json: Optional[str] = None,
                               share_link: Optional[str] = None,
                               hide_ui_controls: bool = True) -> Optional[str]:
    """
    Generate an embed-friendly URL for Terria map.

    Args:
        init_json: Terria initialization JSON (as string or dict)
        share_link: Existing Terria share link
        hide_ui_controls: Whether to hide UI controls in embed (default True)

    Returns:
        str: Embed URL suitable for iframe src, or None if invalid input

    Example:
        >>> url = generate_terria_embed_url(share_link='https://terria.water-data.org/#share=abc')
        >>> print(url)  # Ready to use in iframe src
    """
    base_url = get_terria_base_url()

    # If share link provided, use it directly
    if share_link:
        parsed = parse_terria_share_link(share_link)
        if not parsed:
            return None

        # Use the base URL from the share link if available
        if 'base_url' in parsed:
            base_url = parsed['base_url']

        embed_url = share_link

    # Otherwise, construct from init_json
    elif init_json:
        try:
            # Parse JSON if string
            if isinstance(init_json, str):
                config = json.loads(init_json)
            else:
                config = init_json

            # URL encode the JSON
            import urllib.parse
            encoded_config = urllib.parse.quote(json.dumps(config))

            # Build URL
            embed_url = f"{base_url}/#start={encoded_config}"

        except Exception as e:
            log.error(f"Error generating Terria embed URL: {str(e)}")
            return None
    else:
        # No configuration provided
        return None

    # Add embed parameters if needed
    if hide_ui_controls and '?' not in embed_url and '#' in embed_url:
        # Insert query params before fragment
        parts = embed_url.split('#')
        embed_url = f"{parts[0]}?hideWorkbench=1&hideExplorerPanel=1#{parts[1]}"

    return embed_url


def validate_terria_init_json(init_json: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a Terria initialization JSON configuration.

    Args:
        init_json: JSON string or dict containing Terria init config

    Returns:
        tuple: (is_valid: bool, error_message: str or None)

    Example:
        >>> is_valid, error = validate_terria_init_json('{"initSources": [...]}')
        >>> if not is_valid:
        >>>     print(f"Invalid config: {error}")
    """
    if not init_json:
        return False, "Empty configuration"

    try:
        # Parse JSON if string
        if isinstance(init_json, str):
            config = json.loads(init_json)
        else:
            config = init_json

        # Check if it's a dict
        if not isinstance(config, dict):
            return False, "Configuration must be a JSON object"

        # Basic structure validation
        # Terria init can have various top-level keys:
        # - initSources: catalog items to load
        # - viewerMode: 2d or 3d
        # - baseMaps: custom base maps
        # - camera: initial camera position

        # At minimum, should have initSources or workbench
        has_content = any(key in config for key in [
            'initSources', 'catalog', 'workbench', 'stories'
        ])

        if not has_content:
            return False, "Configuration must contain at least one of: initSources, catalog, workbench, stories"

        # If initSources present, validate it's a list
        if 'initSources' in config:
            if not isinstance(config['initSources'], list):
                return False, "initSources must be an array"

        # If workbench present, validate it's a list
        if 'workbench' in config:
            if not isinstance(config['workbench'], list):
                return False, "workbench must be an array"

        return True, None

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def extract_terria_catalog_items(init_json: str) -> List[Dict[str, Any]]:
    """
    Extract catalog item information from Terria init JSON.

    Useful for displaying what datasets/layers are included in a story section.

    Args:
        init_json: Terria initialization JSON

    Returns:
        list: List of catalog item dicts with name, type, and URL information

    Example:
        >>> items = extract_terria_catalog_items(config_json)
        >>> for item in items:
        >>>     print(f"Layer: {item['name']} ({item['type']})")
    """
    items = []

    try:
        # Parse JSON if string
        if isinstance(init_json, str):
            config = json.loads(init_json)
        else:
            config = init_json

        # Extract from initSources
        if 'initSources' in config:
            for source in config['initSources']:
                if isinstance(source, dict):
                    item_info = {
                        'name': source.get('name', 'Unnamed layer'),
                        'type': source.get('type', 'unknown'),
                        'url': source.get('url', ''),
                    }

                    # Add additional useful fields if present
                    if 'description' in source:
                        item_info['description'] = source['description']
                    if 'id' in source:
                        item_info['id'] = source['id']

                    items.append(item_info)

        # Extract from catalog
        if 'catalog' in config:
            catalog = config['catalog']
            if isinstance(catalog, list):
                for group in catalog:
                    if isinstance(group, dict) and 'items' in group:
                        items.extend(_extract_catalog_group_items(group))

        # Extract from workbench (active items)
        if 'workbench' in config:
            for item_id in config['workbench']:
                items.append({
                    'name': item_id,
                    'type': 'workbench_item',
                    'id': item_id,
                })

    except Exception as e:
        log.error(f"Error extracting Terria catalog items: {str(e)}")

    return items


def _extract_catalog_group_items(group: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Recursively extract items from a catalog group.

    Args:
        group: Catalog group dict

    Returns:
        list: Flattened list of catalog items
    """
    items = []

    if 'items' in group:
        for item in group['items']:
            if isinstance(item, dict):
                # Check if this is another group (has items)
                if 'items' in item:
                    items.extend(_extract_catalog_group_items(item))
                else:
                    # This is a leaf item
                    items.append({
                        'name': item.get('name', 'Unnamed layer'),
                        'type': item.get('type', 'unknown'),
                        'url': item.get('url', ''),
                        'id': item.get('id', ''),
                    })

    return items


def get_terria_iframe_html(section: Dict[str, Any],
                           height: int = 600,
                           width: str = '100%') -> Optional[str]:
    """
    Generate HTML for embedding a Terria map in a section.

    Args:
        section: Section dict with terria_config or terria_share_link
        height: Height of iframe in pixels (default 600)
        width: Width of iframe (default '100%')

    Returns:
        str: HTML string for iframe, or None if no Terria config

    Example:
        >>> html = get_terria_iframe_html(section_dict)
        >>> # Returns: '<iframe src="..." width="100%" height="600"></iframe>'
    """
    embed_url = None

    # Try share link first
    if section.get('terria_share_link'):
        embed_url = generate_terria_embed_url(
            share_link=section['terria_share_link']
        )

    # Fall back to config JSON
    elif section.get('terria_config'):
        embed_url = generate_terria_embed_url(
            init_json=section['terria_config']
        )

    if not embed_url:
        return None

    # Build iframe HTML
    html = f'''<div class="terria-embed-container">
    <iframe src="{embed_url}"
            width="{width}"
            height="{height}"
            frameborder="0"
            allow="geolocation"
            class="terria-embed-iframe">
    </iframe>
</div>'''

    return html


def is_terria_url(url: str) -> bool:
    """
    Check if a URL is a valid Terria instance URL.

    Args:
        url: URL to check

    Returns:
        bool: True if URL appears to be a Terria instance
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)

        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False

        # Check for Terria-specific patterns
        # Common patterns: #share=, #start=, /story/
        if any(pattern in url for pattern in ['#share=', '#start=', '/story/']):
            return True

        # Check if it's a known Terria domain
        known_domains = [
            'terria.water-data.org',
            'terria.io',
            'nationalmap.gov.au',
        ]

        # Add configured domain
        base_url = get_terria_base_url()
        if base_url:
            configured_domain = urlparse(base_url).netloc
            if configured_domain:
                known_domains.append(configured_domain)

        return any(domain in parsed.netloc for domain in known_domains)

    except Exception:
        return False
