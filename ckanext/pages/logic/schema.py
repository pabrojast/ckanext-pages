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
    boolean_validator = p.toolkit.get_validator('boolean_validator')
    url_validator = p.toolkit.get_validator('url_validator')
    int_validator = p.toolkit.get_validator('int_validator')
    
    def json_validator(key, data, errors, context):
        """Validate and safely handle JSON fields"""
        value = data.get(key)
        if value and value != '':
            try:
                import json
                if isinstance(value, str):
                    json.loads(value)
            except (ValueError, TypeError):
                errors[key].append('Invalid JSON format')
        return data[key]
    
    def optional_int_validator(key, data, errors, context):
        """Validate integer fields that can be empty"""
        value = data.get(key)
        if value and value != '':
            try:
                int(value)
            except (ValueError, TypeError):
                errors[key].append('Must be a valid number')
        return data[key]

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
        'spatial_blocks_metadata': [ignore_missing, json_validator, unicode_safe],  # Metadata for spatial content blocks (legacy)
        'impact_assessment_blocks_metadata': [ignore_missing, json_validator, unicode_safe],  # Metadata for impact assessment content blocks
        'response_activities_blocks_metadata': [ignore_missing, json_validator, unicode_safe],  # Metadata for response activities content blocks
        'recovery_phase_blocks_metadata': [ignore_missing, json_validator, unicode_safe],  # Metadata for recovery phase content blocks
        'resilience_phase_blocks_metadata': [ignore_missing, json_validator, unicode_safe],  # Metadata for resilience phase content blocks
        'additional_info_blocks_metadata': [ignore_missing, json_validator, unicode_safe],  # Metadata for additional information content blocks
        'additional_content': [ignore_missing, unicode_safe],
        'header_image': [ignore_missing, unicode_safe],
        'excerpt': [ignore_missing, unicode_safe],
        # Key Information fields for rapid response
        'key_event_start': [ignore_missing, isodate],               # Event start date
        'key_activation': [ignore_missing, isodate],                # Activation date
        'key_world_heritage_sites': [ignore_missing, unicode_safe], # World Heritage Sites
        'key_biosphere_reserves': [ignore_missing, unicode_safe],   # Biosphere Reserves
        'key_geoparks': [ignore_missing, unicode_safe],             # Geoparks
        'key_people_affected': [ignore_missing, optional_int_validator, unicode_safe],      # People affected
        'key_casualties': [ignore_missing, optional_int_validator, unicode_safe],           # Casualties
        'key_damage_usd': [ignore_missing, unicode_safe],           # Damage in USD (can include currency symbols)
        'key_cities_affected': [ignore_missing, unicode_safe],      # Cities affected
        'timeline_events': [ignore_missing, json_validator, unicode_safe],  # Dynamic timeline events
        'uploaded_images': [ignore_missing, json_validator, unicode_safe],  # Uploaded images metadata
        'image_gallery': [ignore_missing, json_validator, unicode_safe],     # Enhanced image gallery
        'response_activities': [ignore_missing, unicode_safe], # Response activities for rapid response
        'impact_assessment': [ignore_missing, unicode_safe],  # Impact assessment for rapid response
        'recovery_phase': [ignore_missing, unicode_safe],     # Recovery phase for rapid response
        'resilience_phase': [ignore_missing, unicode_safe],   # Resilience phase for rapid response
        'activity_status': [ignore_missing, unicode_safe],   # Activity status phase
        'country': [ignore_missing, unicode_safe],           # Country/countries affected
        'countries_affected': [ignore_missing, json_validator, unicode_safe], # Countries affected (JSON array)
        'priority': [ignore_missing, unicode_safe],          # Priority level
        'severity': [ignore_missing, unicode_safe],          # Severity level
        'event_type': [ignore_missing, unicode_safe],        # Event type (references dynamic event types)
        # Common fields for all content types
        'author': [ignore_missing, unicode_safe],           # Author/Source name for all content
        # Water News specific fields
        'source': [ignore_missing, url_validator, unicode_safe],           # Original source URL
        'external_links': [ignore_missing, unicode_safe],   # Related links
        # Water Events specific fields
        'location': [ignore_missing, unicode_safe],         # Event location
        'organization': [ignore_missing, unicode_safe],     # Organizing institution
        'event_details': [ignore_missing, unicode_safe],    # Event details and schedule
        'speakers': [ignore_missing, unicode_safe],         # Speakers and organizers
        'registration_info': [ignore_missing, unicode_safe], # Registration information
        'registration_url': [ignore_missing, url_validator, unicode_safe], # Registration URL
        # Water Publications specific fields
        'publication_url': [ignore_missing, url_validator, unicode_safe],  # URL to publication
        'publication_type': [ignore_missing, unicode_safe], # Type of publication
        'authors': [ignore_missing, unicode_safe],          # Publication authors
        'publication_details': [ignore_missing, unicode_safe], # Publication bibliographic details
        'download_url': [ignore_missing, url_validator, unicode_safe],     # Direct download URL
        'isbn': [ignore_missing, unicode_safe],             # ISBN for books
        'doi': [ignore_missing, unicode_safe],              # DOI for papers
        'journal': [ignore_missing, unicode_safe],          # Journal name
        'conference': [ignore_missing, unicode_safe],       # Conference name
        'year': [ignore_missing, optional_int_validator, unicode_safe],             # Publication year
        'volume': [ignore_missing, optional_int_validator, unicode_safe],           # Volume number
        'issue': [ignore_missing, optional_int_validator, unicode_safe],            # Issue number
        'pages': [ignore_missing, unicode_safe],            # Page numbers
        'abstract': [ignore_missing, unicode_safe],         # Publication abstract
        # Water Management Tools specific fields (formerly Open Source Software)
        'key_features': [ignore_missing, unicode_safe],     # Key features list
        'technical_requirements': [ignore_missing, unicode_safe], # Technical requirements
        'installation_instructions': [ignore_missing, unicode_safe], # Installation instructions
        'repository_url': [ignore_missing, url_validator, unicode_safe],   # Repository URL
        'website_url': [ignore_missing, url_validator, unicode_safe],      # Official website
        'documentation_url': [ignore_missing, url_validator, unicode_safe], # Documentation URL
        'learning_resources': [ignore_missing, unicode_safe], # Learning resources
        'example_applications': [ignore_missing, unicode_safe], # Example applications
        'software_category': [ignore_missing, unicode_safe], # Software categories (comma-separated for multiple)
        'software_license': [ignore_missing, unicode_safe], # Software license
        'development_status': [ignore_missing, unicode_safe], # Development status (Active, Beta, Stable, Maintained, Deprecated, Archived)
        'access_type': [ignore_missing, unicode_safe],      # Open Source or Open Access
        'programming_language': [ignore_missing, unicode_safe], # Programming languages (comma-separated for multiple)
        'additional_languages': [ignore_missing, unicode_safe], # Additional programming languages not in the main list
        'platform': [ignore_missing, unicode_safe],         # Platform compatibility (comma-separated for multiple)
        'version': [ignore_missing, unicode_safe],          # Current version
        'release_date': [ignore_missing, unicode_safe],     # Release date (open text field)
        'attribution': [ignore_missing, unicode_safe],      # Attribution requirements
        'organization_id': [ignore_missing, unicode_safe],  # CKAN organization
        'credit_organization': [ignore_missing, unicode_safe], # Credit organization name
        'member_states': [ignore_missing, json_validator, unicode_safe],    # Member states JSON array
        'header_display_mode': [ignore_missing, unicode_safe], # Header display mode (text, logo, logo_text)
        'include_logo_in_gallery': [ignore_missing, boolean_validator], # Include logo in gallery option
        'add_background': [ignore_missing, boolean_validator], # Add white background to logo
    }


def default_event_types_schema():
    """Schema for event types management"""
    ignore_empty = p.toolkit.get_validator('ignore_empty')
    ignore_missing = p.toolkit.get_validator('ignore_missing')
    not_empty = p.toolkit.get_validator('not_empty')
    name_validator = p.toolkit.get_validator('name_validator')
    unicode_safe = p.toolkit.get_validator('unicode_safe')

    return {
        'id': [ignore_empty, unicode_safe],
        'name': [not_empty, unicode_safe, name_validator],  # Internal name (e.g., 'tropical-cyclone')
        'title': [not_empty, unicode_safe],                 # Display title (e.g., 'Tropical Cyclone')
        'title_plural': [ignore_missing, unicode_safe],     # Plural form (e.g., 'Tropical Cyclones')
        'description': [ignore_missing, unicode_safe],      # Description of the event type
        'icon': [ignore_missing, unicode_safe],             # Icon class (e.g., 'fa-hurricane')
        'color': [ignore_missing, unicode_safe],            # Color code for the event type
        'active': [ignore_missing, p.toolkit.get_validator('boolean_validator')], # Whether active
        'order': [ignore_missing, unicode_safe],            # Display order
        'created': [ignore_missing, p.toolkit.get_validator('isodate')],
        'modified': [ignore_missing, p.toolkit.get_validator('isodate')],
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


def update_event_types_schema():
    '''
    Returns the schema for the event types fields that can be added by other
    extensions.

    :returns: a dictionary mapping fields keys to lists of validator and
    converter functions to be applied to those fields
    :rtype: dictionary
    '''

    schema = default_event_types_schema()
    for plugin in p.PluginImplementations(IPagesSchema):
        if hasattr(plugin, 'update_event_types_schema'):
            schema = plugin.update_event_types_schema(schema)

    return schema
