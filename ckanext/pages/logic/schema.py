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
        'response_activities': [ignore_missing, unicode_safe], # Response activities for rapid response
        'impact_assessment': [ignore_missing, unicode_safe],  # Impact assessment for rapid response
        'activity_status': [ignore_missing, unicode_safe],   # Activity status phase
        'country': [ignore_missing, unicode_safe],           # Country/countries affected
        'priority': [ignore_missing, unicode_safe],          # Priority level
        'severity': [ignore_missing, unicode_safe],          # Severity level
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
        # Open Source Software specific fields
        'key_features': [ignore_missing, unicode_safe],     # Key features list
        'technical_requirements': [ignore_missing, unicode_safe], # Technical requirements
        'installation_instructions': [ignore_missing, unicode_safe], # Installation instructions
        'repository_url': [ignore_missing, unicode_safe],   # Repository URL
        'website_url': [ignore_missing, unicode_safe],      # Official website
        'documentation_url': [ignore_missing, unicode_safe], # Documentation URL
        'learning_resources': [ignore_missing, unicode_safe], # Learning resources
        'example_applications': [ignore_missing, unicode_safe], # Example applications
        'software_category': [ignore_missing, unicode_safe], # Software category
        'software_license': [ignore_missing, unicode_safe], # Software license
        'project_status': [ignore_missing, unicode_safe],   # Project status
        'access_type': [ignore_missing, unicode_safe],      # Open Source or Open Access
        'programming_language': [ignore_missing, unicode_safe], # Programming language
        'platform': [ignore_missing, unicode_safe],         # Platform compatibility
        'version': [ignore_missing, unicode_safe],          # Current version
        'attribution': [ignore_missing, unicode_safe],      # Attribution requirements
        'organization_id': [ignore_missing, unicode_safe],  # CKAN organization
        'credit_organization': [ignore_missing, unicode_safe], # Credit organization name
        'member_states': [ignore_missing, unicode_safe],    # Member states JSON array
        'header_display_mode': [ignore_missing, unicode_safe], # Header display mode (text, logo, logo_text)
        'include_logo_in_gallery': [ignore_missing, unicode_safe], # Include logo in gallery option
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
