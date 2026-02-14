import ckan.plugins as p
import ckan.lib.navl.dictization_functions as df
from ckanext.pages import db


def page_name_validator(key, data, errors, context):
    session = context['session']
    page = context.get('page')
    group_id = context.get('group_id')
    if page and page == data[key]:
        return

    query = session.query(db.Page.name).filter_by(name=data[key], group_id=group_id)
    result = query.first()
    if result:
        errors[key].append(
            p.toolkit._('Page name already exists in database'))


def not_empty_if_blog(key, data, errors, context):
    value = data.get(key)
    if data.get(('page_type',), '') == 'blog':
        if value is df.missing or not value:
            errors[key].append('Publish Date Must be supplied')


def water_type_validator(key, data, errors, context):
    """Validate water_type field for water-family content.

    Valid water types include:
    - groundwater: Groundwater resources
    - surface_water: Surface water resources (rivers, lakes)
    - coastal_water: Coastal and marine waters
    - wastewater: Wastewater and sanitation
    - transboundary: Transboundary water resources
    - urban_water: Urban water management
    - agricultural_water: Agricultural water use
    - industrial_water: Industrial water use
    - water_quality: Water quality monitoring
    - water_governance: Water governance and policy
    - climate_water: Climate change and water
    - ecosystem: Aquatic ecosystems
    - other: Other water-related topics
    """
    value = data.get(key)

    # If empty or missing, that's ok (field is optional)
    if not value or value is df.missing:
        return

    # List of valid water types
    valid_types = [
        'groundwater',
        'surface_water',
        'coastal_water',
        'wastewater',
        'transboundary',
        'urban_water',
        'agricultural_water',
        'industrial_water',
        'water_quality',
        'water_governance',
        'climate_water',
        'ecosystem',
        'other'
    ]

    if value not in valid_types:
        errors[key].append(
            p.toolkit._('Invalid water type. Must be one of: {}').format(', '.join(valid_types))
        )


def water_category_validator(key, data, errors, context):
    """Validate water_category field for water-family content.

    Categories can be comma-separated for multiple categories.
    Valid categories include:
    - research: Research and studies
    - policy: Policy and legislation
    - technology: Technology and innovation
    - education: Education and capacity building
    - monitoring: Monitoring and assessment
    - management: Water resources management
    - conservation: Conservation and protection
    - cooperation: International cooperation
    - community: Community engagement
    - infrastructure: Infrastructure development
    """
    value = data.get(key)

    # If empty or missing, that's ok (field is optional)
    if not value or value is df.missing:
        return

    # List of valid categories
    valid_categories = [
        'research',
        'policy',
        'technology',
        'education',
        'monitoring',
        'management',
        'conservation',
        'cooperation',
        'community',
        'infrastructure'
    ]

    # Handle comma-separated categories
    if isinstance(value, str):
        categories = [cat.strip() for cat in value.split(',') if cat.strip()]
    else:
        categories = [value]

    # Validate each category
    invalid_categories = []
    for category in categories:
        if category not in valid_categories:
            invalid_categories.append(category)

    if invalid_categories:
        errors[key].append(
            p.toolkit._('Invalid categories: {}. Valid categories are: {}').format(
                ', '.join(invalid_categories),
                ', '.join(valid_categories)
            )
        )


def not_empty_if_water_publication(key, data, errors, context):
    """Ensure a publication reference exists for water-publications pages."""

    def _has_value(raw_value):
        if raw_value is df.missing or raw_value is None:
            return False
        if isinstance(raw_value, str):
            return bool(raw_value.strip())
        return bool(raw_value)

    value = data.get(key)
    page_type = data.get(('page_type',), '')

    if page_type == 'water-publications':
        publication_url = data.get(('publication_url',), '')
        download_url = data.get(('download_url',), '')
        dataset_url = data.get(('dataset_url',), '')
        dataset_title = data.get(('dataset_title',), '')

        has_dataset_upload = False
        try:
            request = p.toolkit.request
            uploaded_file = request.files.get('dataset_upload') if getattr(request, 'files', None) else None
            has_dataset_upload = bool(uploaded_file and getattr(uploaded_file, 'filename', None))
        except Exception:
            has_dataset_upload = False

        if not any([
            _has_value(publication_url),
            _has_value(download_url),
            _has_value(dataset_url),
            # Allow existing records that rely on generated dataset metadata.
            _has_value(dataset_title),
            has_dataset_upload,
        ]):
            if value is df.missing or not value:
                errors[key].append(
                    p.toolkit._('Provide a publication URL, download URL, dataset URL, or upload a file.')
                )
