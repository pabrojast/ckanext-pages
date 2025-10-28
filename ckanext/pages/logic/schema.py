import ckan.plugins as p
from ckanext.pages.validators import (
    page_name_validator,
    not_empty_if_blog,
    water_type_validator,
    water_category_validator,
    not_empty_if_water_publication
)
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
    email_validator = p.toolkit.get_validator('email_validator')
    
    def clean_categories_validator(key, data, errors, context):
        """Clean categories by removing duplicates and empty values"""
        value = data.get(key)

        if not value:
            return data[key]

        # Handle list values (from multi-select forms)
        if isinstance(value, list):
            # Clean and deduplicate
            unique_categories = []
            seen = set()
            for cat in value:
                if cat and isinstance(cat, str):
                    clean_cat = cat.strip()
                    if clean_cat and clean_cat not in seen:
                        unique_categories.append(clean_cat)
                        seen.add(clean_cat)
            data[key] = ','.join(unique_categories)

        # Handle string values (comma-separated)
        elif isinstance(value, str):
            # Split by comma, strip whitespace, remove duplicates and empty values
            categories = [cat.strip() for cat in value.split(',') if cat.strip()]
            # Remove duplicates while preserving order
            unique_categories = []
            seen = set()
            for cat in categories:
                if cat not in seen:
                    unique_categories.append(cat)
                    seen.add(cat)
            data[key] = ','.join(unique_categories)

        return data[key]

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
    
    def safe_boolean_validator(key, data, errors, context):
        """Normalise checkbox-style values before boolean validation"""
        value = data.get(key)

        if value is None:
            return

        # Handle multi-value form fields (eg, checkbox lists)
        if isinstance(value, list):
            if not value:
                value = ''
            else:
                value = value[0]

        # Ensure booleans are represented as the strings expected by CKAN
        if isinstance(value, bool):
            value = 'true' if value else 'false'
        elif isinstance(value, str):
            normalised = value.strip().lower()
            if normalised in {'on', 'yes', '1', 'true'}:
                value = 'true'
            elif normalised in {'off', 'no', '0', 'false'}:
                value = 'false'
            else:
                value = normalised

        if value == '':
            # Leave empty for ignore_missing to drop later in the chain
            return

        data[key] = value

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
        'agenda_document': [ignore_missing, unicode_safe],       # Agenda or flyer document URL
        'header_image': [ignore_missing, unicode_safe],
        'news_attachment': [ignore_missing, unicode_safe],      # Attachment for news articles
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
        # Water Family common fields
        'water_type': [ignore_missing, water_type_validator, unicode_safe],  # Specific water type (validated)
        'water_category': [ignore_missing, water_category_validator, clean_categories_validator, unicode_safe],  # Categories
        'water_metadata': [ignore_missing, json_validator, unicode_safe],  # Additional metadata in JSON format
        'attachments': [ignore_missing, json_validator, unicode_safe],      # Attachments array in JSON format
        # Water News specific fields
        'source': [ignore_missing, url_validator, unicode_safe],           # Original source URL
        'external_links': [ignore_missing, unicode_safe],   # Related links
        # Water Events specific fields
        'location': [ignore_missing, unicode_safe],         # Event location
        'organization': [ignore_missing, unicode_safe],     # Organizing institution
        'ihp_organization': [ignore_missing, unicode_safe], # Primary organization (id)
        'co_organizers': [ignore_missing, unicode_safe],    # Co-organizers text
        'event_details': [ignore_missing, unicode_safe],    # Event details and schedule
        'event_format': [ignore_missing, unicode_safe],     # Event format (in-person, online, hybrid)
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
        'dataset_title': [ignore_missing, unicode_safe],    # Documents dataset title
        'dataset_visibility': [ignore_missing, unicode_safe],  # Visibility for generated dataset
        'dataset_url': [ignore_missing, url_validator, unicode_safe],  # External dataset URL
        'document_format': [ignore_missing, unicode_safe],  # Resource format/extension
        'document_mimetype': [ignore_missing, unicode_safe],  # Resource mimetype
        'contact_name': [ignore_missing, unicode_safe],     # Dataset contact name
        'contact_email': [ignore_missing, email_validator, unicode_safe],  # Dataset contact email
        'dataset_description': [ignore_missing, unicode_safe],  # Dataset description text
        'graphic_overview': [ignore_missing, url_validator, unicode_safe],  # Dataset graphic overview URL
        'dataset_language': [ignore_missing, unicode_safe],  # Dataset metadata language
        'creation_date': [ignore_missing, isodate],         # Dataset/resource creation date
        'country_groups': [ignore_missing, json_validator, unicode_safe],  # Member states JSON payload
        # Water Management Tools specific fields (formerly Open Source Software)
        'key_features': [ignore_missing, unicode_safe],     # Key features list
        'technical_requirements': [ignore_missing, unicode_safe], # Technical requirements
        'installation_instructions': [ignore_missing, unicode_safe], # Installation instructions
        'repository_url': [ignore_missing, url_validator, unicode_safe],   # Repository URL
        'website_url': [ignore_missing, url_validator, unicode_safe],      # Official website
        'documentation_url': [ignore_missing, url_validator, unicode_safe], # Documentation URL
        'learning_resources': [ignore_missing, unicode_safe], # Learning resources
        'example_applications': [ignore_missing, unicode_safe], # Example applications
        'software_category': [ignore_missing, clean_categories_validator, unicode_safe], # Software categories (comma-separated for multiple)
        'software_license': [ignore_missing, unicode_safe], # Software license
        'development_status': [ignore_missing, unicode_safe], # Development status (Active, Beta, Stable, Maintained, Deprecated, Archived)
        'access_type': [ignore_missing, unicode_safe],      # Open Source or Open Access
        'programming_language': [ignore_missing, clean_categories_validator, unicode_safe], # Programming languages (comma-separated for multiple)
        'additional_languages': [ignore_missing, unicode_safe], # Additional programming languages not in the main list
        'platform': [ignore_missing, clean_categories_validator, unicode_safe],         # Platform compatibility (comma-separated for multiple)
        'version': [ignore_missing, unicode_safe],          # Current version
        'release_date': [ignore_missing, unicode_safe],     # Release date (open text field)
        'attribution': [ignore_missing, unicode_safe],      # Attribution requirements
        'organization_id': [ignore_missing, unicode_safe],  # CKAN organization
        'credit_organization': [ignore_missing, unicode_safe], # Credit organization name
        'member_states': [ignore_missing, json_validator, unicode_safe],    # Member states JSON array
        'header_display_mode': [ignore_missing, unicode_safe], # Header display mode (text, logo, logo_text)
        'include_logo_in_gallery': [safe_boolean_validator, ignore_missing, boolean_validator], # Include logo in gallery option
        'add_background': [safe_boolean_validator, ignore_missing, boolean_validator], # Add white background to logo
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


def water_family_schema():
    """Schema for water-family content types (water-news, water-events, water-publications).

    This function defines the schema for all water-family related content types,
    including common fields shared across all types and specific fields for each type.

    Water-family content types:
    - water-news: News articles about water-related topics
    - water-events: Water-related events (conferences, workshops, meetings)
    - water-publications: Water-related publications (reports, papers, books)

    Returns:
        dict: Schema definition with validators for water-family content
    """
    ignore_empty = p.toolkit.get_validator('ignore_empty')
    ignore_missing = p.toolkit.get_validator('ignore_missing')
    not_empty = p.toolkit.get_validator('not_empty')
    isodate = p.toolkit.get_validator('isodate')
    unicode_safe = p.toolkit.get_validator('unicode_safe')
    url_validator = p.toolkit.get_validator('url_validator')
    email_validator = p.toolkit.get_validator('email_validator')
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

    def clean_categories_validator(key, data, errors, context):
        """Clean categories by removing duplicates and empty values"""
        value = data.get(key)

        if not value:
            return data[key]

        # Handle list values (from multi-select forms)
        if isinstance(value, list):
            unique_categories = []
            seen = set()
            for cat in value:
                if cat and isinstance(cat, str):
                    clean_cat = cat.strip()
                    if clean_cat and clean_cat not in seen:
                        unique_categories.append(clean_cat)
                        seen.add(clean_cat)
            data[key] = ','.join(unique_categories)

        # Handle string values (comma-separated)
        elif isinstance(value, str):
            categories = [cat.strip() for cat in value.split(',') if cat.strip()]
            unique_categories = []
            seen = set()
            for cat in categories:
                if cat not in seen:
                    unique_categories.append(cat)
                    seen.add(cat)
            data[key] = ','.join(unique_categories)

        return data[key]

    return {
        # Core fields (inherited from base pages schema)
        'id': [ignore_empty, unicode_safe],
        'title': [not_empty, unicode_safe],
        'name': [not_empty, unicode_safe],
        'content': [ignore_missing, unicode_safe],
        'page_type': [ignore_missing, unicode_safe],  # water-news, water-events, water-publications
        'private': [ignore_missing, p.toolkit.get_validator('boolean_validator')],
        'publish_date': [ignore_missing, isodate],
        'created': [ignore_missing, isodate],

        # Common water-family fields
        'water_type': [ignore_missing, water_type_validator, unicode_safe],  # Specific water type (validated)
        'water_category': [ignore_missing, water_category_validator, clean_categories_validator, unicode_safe],  # Categories
        'water_metadata': [ignore_missing, json_validator, unicode_safe],  # Additional metadata in JSON format
        'attachments': [ignore_missing, json_validator, unicode_safe],  # Attachments array in JSON format
        'author': [ignore_missing, unicode_safe],  # Author/Source name
        'excerpt': [ignore_missing, unicode_safe],  # Short excerpt/summary
        'header_image': [ignore_missing, unicode_safe],  # Header image URL
        'uploaded_images': [ignore_missing, json_validator, unicode_safe],  # Gallery images metadata
        'additional_content': [ignore_missing, unicode_safe],  # Additional rich text content
        'ihp_organization': [ignore_missing, unicode_safe],  # Primary IHP organization (id)

        # Water News specific fields
        'source': [ignore_missing, url_validator, unicode_safe],  # Original source URL
        'external_links': [ignore_missing, unicode_safe],  # Related links (rich text)
        'news_attachment': [ignore_missing, unicode_safe],  # News attachment URL

        # Water Events specific fields
        'location': [ignore_missing, unicode_safe],  # Event location
        'organization': [ignore_missing, unicode_safe],  # Organizing institution
        'co_organizers': [ignore_missing, unicode_safe],  # Co-organizers text
        'event_details': [ignore_missing, unicode_safe],  # Event details and schedule
        'event_format': [ignore_missing, unicode_safe],  # Event format (in-person, online, hybrid)
        'speakers': [ignore_missing, unicode_safe],  # Speakers and organizers
        'registration_info': [ignore_missing, unicode_safe],  # Registration information
        'registration_url': [ignore_missing, url_validator, unicode_safe],  # Registration URL
        'agenda_document': [ignore_missing, unicode_safe],  # Agenda or flyer document URL
        'timeline_events': [ignore_missing, json_validator, unicode_safe],  # Event timeline (JSON)

        # Water Publications specific fields
        'publication_url': [ignore_missing, url_validator, unicode_safe],  # URL to publication
        'publication_type': [ignore_missing, unicode_safe],  # Type (report, paper, book, thesis, etc.)
        'authors': [ignore_missing, unicode_safe],  # Publication authors
        'publication_details': [ignore_missing, unicode_safe],  # Bibliographic details
        'download_url': [ignore_missing, url_validator, unicode_safe],  # Direct download URL
        'isbn': [ignore_missing, unicode_safe],  # ISBN for books
        'doi': [ignore_missing, unicode_safe],  # DOI for papers
        'journal': [ignore_missing, unicode_safe],  # Journal name
        'conference': [ignore_missing, unicode_safe],  # Conference name
        'year': [ignore_missing, optional_int_validator, unicode_safe],  # Publication year
        'volume': [ignore_missing, optional_int_validator, unicode_safe],  # Volume number
        'issue': [ignore_missing, optional_int_validator, unicode_safe],  # Issue number
        'pages': [ignore_missing, unicode_safe],  # Page numbers
        'abstract': [ignore_missing, unicode_safe],  # Publication abstract

        # Dataset integration fields (for publications)
        'dataset_title': [ignore_missing, unicode_safe],  # Documents dataset title
        'dataset_visibility': [ignore_missing, unicode_safe],  # Visibility for generated dataset
        'dataset_url': [ignore_missing, url_validator, unicode_safe],  # External dataset URL
        'document_format': [ignore_missing, unicode_safe],  # Resource format/extension
        'document_mimetype': [ignore_missing, unicode_safe],  # Resource mimetype
        'contact_name': [ignore_missing, unicode_safe],  # Dataset contact name
        'contact_email': [ignore_missing, email_validator, unicode_safe],  # Dataset contact email
        'dataset_description': [ignore_missing, unicode_safe],  # Dataset description text
        'graphic_overview': [ignore_missing, url_validator, unicode_safe],  # Dataset graphic overview URL
        'dataset_language': [ignore_missing, unicode_safe],  # Dataset metadata language
        'creation_date': [ignore_missing, isodate],  # Dataset/resource creation date
        'country_groups': [ignore_missing, json_validator, unicode_safe],  # Member states JSON payload
    }
