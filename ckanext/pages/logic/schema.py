import ckan.plugins as p
from ckanext.pages.validators import page_name_validator, not_empty_if_blog
from ckanext.pages.interfaces import IPagesSchema


def default_pages_schema():
    ignore_empty = p.toolkit.get_validator('ignore_empty')
    ignore_missing = p.toolkit.get_validator('ignore_missing')
    not_empty = p.toolkit.get_validator('not_empty')
    isodate = p.toolkit.get_validator('isodate')
    name_validator = p.toolkit.get_validator('name_validator')
    unicode_safe = p.toolkit.get_validator('unicode_safe')

    return {
        'id': [ignore_empty, unicode_safe],
        'title': [not_empty, unicode_safe],
        'name': [
            not_empty, unicode_safe, name_validator, page_name_validator],
        'content': [ignore_missing, unicode_safe],
        'page_type': [ignore_missing, unicode_safe],
        'order': [ignore_missing, unicode_safe],
        'private': [ignore_missing,
                    p.toolkit.get_validator('boolean_validator')],
        'group_id': [ignore_missing, unicode_safe],
        'user_id': [ignore_missing, unicode_safe],
        'created': [ignore_missing, isodate],
        'publish_date': [
            not_empty_if_blog, ignore_missing, isodate],
        # Rapid Response specific fields
        'subtitle': [ignore_missing, unicode_safe],
        'key_info': [ignore_missing, unicode_safe],
        'image_carousel': [ignore_missing, unicode_safe],
        'map_stories': [ignore_missing, unicode_safe],
        'additional_content': [ignore_missing, unicode_safe],
        'header_image': [ignore_missing, unicode_safe],
        'excerpt': [ignore_missing, unicode_safe],
        'timeline_events': [ignore_missing, unicode_safe],  # Dynamic timeline events
        'uploaded_images': [ignore_missing, unicode_safe],  # Uploaded images metadata
        'image_gallery': [ignore_missing, unicode_safe],     # Enhanced image gallery
        # Water News specific fields
        'source': [ignore_missing, unicode_safe],           # Original source URL
        'external_links': [ignore_missing, unicode_safe],   # Related links
        'author': [ignore_missing, unicode_safe],           # Author/Source name
        # Water Events specific fields
        'location': [ignore_missing, unicode_safe],         # Event location
        'organization': [ignore_missing, unicode_safe],     # Organizing institution
        'event_details': [ignore_missing, unicode_safe],    # Event details and schedule
        'speakers': [ignore_missing, unicode_safe],         # Speakers and organizers
        'registration_info': [ignore_missing, unicode_safe], # Registration information
        'registration_url': [ignore_missing, unicode_safe], # Registration URL
        # Water Publications specific fields
        'publication_url': [ignore_missing, unicode_safe],  # URL to publication
        'publication_type': [ignore_missing, unicode_safe], # Type of publication
        'authors': [ignore_missing, unicode_safe],          # Publication authors
        'publication_details': [ignore_missing, unicode_safe], # Publication bibliographic details
        'download_url': [ignore_missing, unicode_safe],     # Direct download URL
        'isbn': [ignore_missing, unicode_safe],             # ISBN for books
        'doi': [ignore_missing, unicode_safe],              # DOI for papers
        'journal': [ignore_missing, unicode_safe],          # Journal name
        'conference': [ignore_missing, unicode_safe],       # Conference name
        'year': [ignore_missing, unicode_safe],             # Publication year
        'volume': [ignore_missing, unicode_safe],           # Volume number
        'issue': [ignore_missing, unicode_safe],            # Issue number
        'pages': [ignore_missing, unicode_safe],            # Page numbers
        'abstract': [ignore_missing, unicode_safe],         # Publication abstract
    }


def update_pages_schema():
    '''
    Returns the schema for the pages fields that can be added by other
    extensions.

    By default these are the keys of the
    :py:func:`ckanext.logic.schema.default_pages_schema`.
    Extensions can add or remove keys from this schema using the
    :py:meth:`ckanext.pages.interfaces.IPagesSchema.update_pages_schema`
    method.

    :returns: a dictionary mapping fields keys to lists of validator and
    converter functions to be applied to those fields
    :rtype: dictionary
    '''

    schema = default_pages_schema()
    for plugin in p.PluginImplementations(IPagesSchema):
        if hasattr(plugin, 'update_pages_schema'):
            schema = plugin.update_pages_schema(schema)

    return schema
