import datetime
import json

from ckan.model.types import make_uuid
from ckan import model
import ckan.plugins as p
import ckan.lib.navl.dictization_functions as df
import ckan.lib.uploader as uploader
import ckan.lib.helpers as h
from ckan.plugins import toolkit as tk
from html.parser import HTMLParser

from ckanext.pages.logic.schema import update_pages_schema

import ckan.authz as authz

from ckanext.pages import db

# Import database utilities for better error handling
try:
    from ckanext.pages.db_utils import with_db_retry, ensure_valid_session
except ImportError:
    # Fallback if db_utils is not available
    def with_db_retry(max_retries=3, delay=0.5):
        def decorator(func):
            return func
        return decorator
    def ensure_valid_session():
        pass

# Nuevas importaciones para el procesamiento de imágenes
from PIL import Image, ImageOps
import os
import tempfile
import shutil


class HTMLFirstImage(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.first_image = None

    def handle_starttag(self, tag, attrs):
        if tag == 'img' and not self.first_image:
            self.first_image = dict(attrs)['src']


def _pages_show(context, data_dict):
    org_id = data_dict.get('org_id')
    page = data_dict.get('page')
    out = db.Page.get(group_id=org_id, name=page)
    if out:
        out = db.table_dictize(out, context)
    return out


def _pages_list(context, data_dict):
    search = {}
    org_id = data_dict.get('org_id')
    ordered = data_dict.get('order')
    order_publish_date = data_dict.get('order_publish_date')
    page_type = data_dict.get('page_type')
    private = data_dict.get('private', True)
    
    # New search and filter parameters
    q = data_dict.get('q')  # Search query
    event_type = data_dict.get('event_type')  # Event type filter
    order_by = data_dict.get('order_by')  # Custom ordering
    
    if ordered:
        search['order'] = True
    if page_type:
        search['page_type'] = page_type
    if order_publish_date:
        search['order_publish_date'] = True
    if q:
        search['q'] = q
    if event_type:
        search['event_type'] = event_type
    if order_by:
        search['order_by'] = order_by
        
    if not org_id:
        search['group_id'] = None
        try:
            p.toolkit.check_access('ckanext_pages_update', context, data_dict)
            if not private:
                search['private'] = False
        except p.toolkit.NotAuthorized:
            search['private'] = False
    else:
        group = context['model'].Group.get(org_id)
        user = context['user']
        member = authz.has_user_permission_for_group_or_org(
            group.id, user, 'read')
        search['group_id'] = org_id
        if not member:
            search['private'] = False
    
    try:
        # Ensure valid database session before query
        ensure_valid_session()
        out = db.Page.pages(**search)
    except Exception as e:
        # Log the error and return empty list as fallback
        import logging
        log = logging.getLogger(__name__)
        log.error("Error fetching pages list: %s", str(e))
        return []
    
    out_list = []
    for pg in out:
        try:
            parser = HTMLFirstImage()
            if pg.content:
                parser.feed(pg.content)
            img = parser.first_image
            pg_row = {'title': pg.title,
                      'content': pg.content,
                      'name': pg.name,
                      'publish_date': pg.publish_date.isoformat() if pg.publish_date else None,
                      'group_id': pg.group_id,
                      'page_type': pg.page_type,
                      }
            if img:
                pg_row['image'] = img
            extras = pg.extras
            if extras:
                try:
                    pg_row.update(json.loads(pg.extras))
                except (ValueError, TypeError):
                    pass
            out_list.append(pg_row)
        except Exception as e:
            # Skip problematic pages but continue with others
            import logging
            log = logging.getLogger(__name__)
            log.warning("Error processing page %s: %s", getattr(pg, 'name', 'unknown'), str(e))
            continue
    return out_list


def _pages_delete(context, data_dict):
    org_id = data_dict.get('org_id')
    page = data_dict.get('page')
    out = db.Page.get(group_id=org_id, name=page)
    if out:
        session = context['session']
        session.delete(out)
        session.commit()


def _pages_update(context, data_dict):
    org_id = data_dict.get('org_id')
    page = data_dict.get('page')
    # we need the page in the context for name validation
    context['page'] = page
    context['group_id'] = org_id
    schema = update_pages_schema()

    # +1 is the Current state by default while ckanext.pages.revisions_limit is the amounf of previous states
    revisions_limit = tk.asint(tk.config.get('ckanext.pages.revisions_limit', '3')) + 1
    force_revisions_limit = tk.asbool(tk.config.get('ckanext.pages.revisions_force_limit', False))

    data, errors = df.validate(data_dict, schema, context)

    if errors:
        raise p.toolkit.ValidationError(errors)

    out = db.Page.get(group_id=org_id, name=page)
    if not out:
        out = db.Page()
        out.group_id = org_id
        out.name = page
    items = ['title', 'content', 'name', 'private',
             'order', 'page_type', 'publish_date']

    # backward compatible with older version where page_type does not exist
    for item in items:
        setattr(out, item, data.get(item, 'page' if item == 'page_type' else None))

    extras = {}

    extra_keys = set(schema.keys()) - set(items + ['id', 'created'])
    for key in extra_keys:
        if key in data:
            extras[key] = data.get(key)
    out.extras = json.dumps(extras)

    out.modified = datetime.datetime.now(datetime.timezone.utc)
    user = model.User.get(context['user'])
    out.user_id = user.id

    revisions = out.revisions

    new_revision = {
        make_uuid(): {
            "content": out.content,
            "user_id": user.id,
            "created": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "current": True
        }
    }
    if not revisions:
        out.revisions = new_revision
    else:
        if (len(revisions) >= revisions_limit):
            revisions = out.get_ordered_revisions()

            if not force_revisions_limit:
                revisions.popitem()
            else:
                # Remove all previous revisions if there any to match revisions_limit
                # Need to add +1 to the length to include the Active state as done for revisions_limit
                for i in range((len(revisions) + 1) - revisions_limit):
                    revisions.popitem()

        # Remove the current key from all past revisions before merging
        revisions = _remove_keys_revision_from_dict(revisions)
        out.revisions = {**new_revision, **revisions}

    out.save()
    session = context['session']
    session.add(out)
    session.commit()


def _remove_keys_revision_from_dict(data_dict, keys=['current']):
    return {
        id: {
            key: data_dict[id][key] for key in data_dict[id] if key not in keys
            } for id in data_dict
    }


def pages_upload(context, data_dict):
    """ Upload a file to the CKAN server with automatic image processing.

    This method implements the logic for file uploads used by CKEditor with
    automatic image resizing and cropping for logos. For more details on 
    implementation and expected return values see:
     - https://ckeditor.com/docs/ckeditor4/latest/guide/dev_file_upload.html#server-side-configuration

    """

    try:
        p.toolkit.check_access('ckanext_pages_upload', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))

    upload = uploader.get_uploader('page_images')

    upload.update_data_dict(data_dict, 'image_url',
                            'upload', 'clear_upload')

    max_image_size = uploader.get_max_image_size()

    try:
        upload.upload(max_image_size)
    except p.toolkit.ValidationError:
        message = (
            "Can't upload the file, size is too large. "
            "(Max allowed is {0}mb)".format(max_image_size)
        )
        return {'uploaded': 0, 'error': {'message': message}}

    # Procesar la imagen si es un logo
    image_url = data_dict.get('image_url')
    is_logo = data_dict.get('is_logo', False)
    add_background = data_dict.get('add_background', False)
    
    if image_url and is_logo:
        try:
            # Obtener la ruta del archivo subido
            if image_url[0:6] not in {'http:/', 'https:'}:
                # Es un archivo local
                upload_dir = upload.get_directory()
                image_path = os.path.join(upload_dir, image_url)
                
                # Procesar la imagen
                processed_image_path = _process_logo_image(image_path, upload_dir, add_background)
                
                if processed_image_path:
                    # Actualizar la URL de la imagen procesada
                    image_url = os.path.basename(processed_image_path)
                    upload.filename = image_url
                    
        except Exception as e:
            # Log el error pero continúa con la imagen original
            logging.error(f"Error processing logo image: {str(e)}")
    
    # Generar URL final
    if image_url and image_url[0:6] not in {'http:/', 'https:'}:
        image_url = h.url_for_static(
            'uploads/page_images/%s' % image_url,
            qualified=True
        )
    
    return {'url': image_url, 'fileName': upload.filename, 'uploaded': 1}


def _process_logo_image(image_path, upload_dir, add_background=False):
    """
    Procesa una imagen para convertirla en un logo con dimensiones estándar.
    
    Args:
        image_path: Ruta al archivo de imagen original
        upload_dir: Directorio donde guardar la imagen procesada
        add_background: Si se debe agregar fondo blanco (default: False)
        
    Returns:
        Ruta al archivo procesado o None si hay error
    """
    try:
        # Dimensiones estándar para logos
        LOGO_WIDTH = 200
        LOGO_HEIGHT = 80
        
        # Abrir la imagen original
        with Image.open(image_path) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA', 'P'):
                if add_background:
                    # Crear fondo blanco para imágenes con transparencia
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                else:
                    # Mantener transparencia si no se quiere fondo
                    if img.mode == 'P':
                        img = img.convert('RGBA')
            elif img.mode != 'RGB' and img.mode != 'RGBA':
                img = img.convert('RGB')
            
            # Calcular las dimensiones para mantener la proporción
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height
            
            # Determinar si la imagen es más ancha o alta
            if aspect_ratio > LOGO_WIDTH / LOGO_HEIGHT:
                # Imagen más ancha - ajustar por ancho
                new_width = LOGO_WIDTH
                new_height = int(LOGO_WIDTH / aspect_ratio)
            else:
                # Imagen más alta - ajustar por altura
                new_height = LOGO_HEIGHT
                new_width = int(LOGO_HEIGHT * aspect_ratio)
            
            # Redimensionar la imagen manteniendo proporción
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Crear lienzo final
            if add_background or img.mode == 'RGB':
                # Con fondo blanco
                final_img = Image.new('RGB', (LOGO_WIDTH, LOGO_HEIGHT), (255, 255, 255))
                # Centrar la imagen redimensionada
                x_offset = (LOGO_WIDTH - new_width) // 2
                y_offset = (LOGO_HEIGHT - new_height) // 2
                if img_resized.mode == 'RGBA':
                    final_img.paste(img_resized, (x_offset, y_offset), img_resized)
                else:
                    final_img.paste(img_resized, (x_offset, y_offset))
            else:
                # Sin fondo (mantener transparencia)
                final_img = Image.new('RGBA', (LOGO_WIDTH, LOGO_HEIGHT), (255, 255, 255, 0))
                # Centrar la imagen redimensionada
                x_offset = (LOGO_WIDTH - new_width) // 2
                y_offset = (LOGO_HEIGHT - new_height) // 2
                final_img.paste(img_resized, (x_offset, y_offset), img_resized if img_resized.mode == 'RGBA' else None)
            
            # Generar nombre para la imagen procesada
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            if add_background or img.mode == 'RGB' or final_img.mode == 'RGB':
                processed_name = f"{base_name}_logo.jpg"
                processed_path = os.path.join(upload_dir, processed_name)
                # Guardar como JPEG
                final_img.save(processed_path, 'JPEG', quality=90, optimize=True)
            else:
                processed_name = f"{base_name}_logo.png"
                processed_path = os.path.join(upload_dir, processed_name)
                # Guardar como PNG para mantener transparencia
                final_img.save(processed_path, 'PNG', optimize=True)
            
            # Eliminar la imagen original si es diferente
            if os.path.abspath(image_path) != os.path.abspath(processed_path):
                try:
                    os.remove(image_path)
                except:
                    pass
            
            return processed_path
            
    except Exception as e:
        logging.error(f"Error processing logo image: {str(e)}")
        return None


@tk.side_effect_free
def pages_show(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_pages_show', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_show(context, data_dict)


def pages_update(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_pages_update', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_update(context, data_dict)


def pages_revision_restore(context, data_dict):
    p.toolkit.check_access('ckanext_pages_update', context, data_dict)
    name = data_dict.get('page')
    rev = data_dict.get('revision')
    page = db.Page.get(name=name)

    if page and page.revisions:
        page.revisions = _remove_keys_revision_from_dict(page.revisions)
        revision = page.revisions.get(rev)

        try:
            revision['current'] = True
            page.content = revision['content']
            page.save()
            return revision
        except TypeError:
            raise TypeError("Unexpected value.")


def pages_delete(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_pages_delete', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_delete(context, data_dict)


@tk.side_effect_free
def pages_list(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_pages_list', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_list(context, data_dict)


@tk.side_effect_free
def org_pages_show(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_org_pages_show', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_show(context, data_dict)


def org_pages_update(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_org_pages_update', context,
                               data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_update(context, data_dict)


def org_pages_delete(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_org_pages_delete', context,
                               data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_delete(context, data_dict)


@tk.side_effect_free
def org_pages_list(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_org_pages_list', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_list(context, data_dict)


@tk.side_effect_free
def group_pages_show(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_group_pages_show', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_show(context, data_dict)


def group_pages_update(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_group_pages_update', context,
                               data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_update(context, data_dict)


def group_pages_delete(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_group_pages_delete', context,
                               data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_delete(context, data_dict)


@tk.side_effect_free
def group_pages_list(context, data_dict):
    try:
        p.toolkit.check_access('ckanext_group_pages_list', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    return _pages_list(context, data_dict)


# Event Types Management Actions

def _get_default_event_types():
    """Get default event types if no custom types exist"""
    return [
        {
            'id': 'tropical-cyclone',
            'name': 'tropical-cyclone',
            'title': 'Tropical Cyclone',
            'title_plural': 'Tropical Cyclones',
            'description': 'Tropical storm systems with strong winds and heavy rainfall',
            'icon': 'fa-hurricane',
            'color': '#dc3545',
            'active': True,
            'order': 1,
            'is_default': True
        },
        {
            'id': 'earthquake',
            'name': 'earthquake',
            'title': 'Earthquake',
            'title_plural': 'Earthquakes',
            'description': 'Seismic events causing ground shaking',
            'icon': 'fa-earthquake',
            'color': '#6f42c1',
            'active': True,
            'order': 2,
            'is_default': True
        },
        {
            'id': 'tsunami',
            'name': 'tsunami',
            'title': 'Tsunami',
            'title_plural': 'Tsunamis',
            'description': 'Large ocean waves caused by seismic activity',
            'icon': 'fa-water',
            'color': '#17a2b8',
            'active': True,
            'order': 3,
            'is_default': True
        },
        {
            'id': 'flood',
            'name': 'flood',
            'title': 'Flood',
            'title_plural': 'Floods',
            'description': 'Overflow of water onto normally dry land',
            'icon': 'fa-tint',
            'color': '#007bff',
            'active': True,
            'order': 4,
            'is_default': True
        },
        {
            'id': 'wildfire',
            'name': 'wildfire',
            'title': 'Wildfire',
            'title_plural': 'Wildfires',
            'description': 'Uncontrolled fire in natural areas',
            'icon': 'fa-fire',
            'color': '#fd7e14',
            'active': True,
            'order': 5,
            'is_default': True
        },
        {
            'id': 'volcanic-eruption',
            'name': 'volcanic-eruption',
            'title': 'Volcanic Eruption',
            'title_plural': 'Volcanic Eruptions',
            'description': 'Volcanic activity with lava, ash, and gas emissions',
            'icon': 'fa-mountain',
            'color': '#e83e8c',
            'active': True,
            'order': 6,
            'is_default': True
        },
        {
            'id': 'drought',
            'name': 'drought',
            'title': 'Drought',
            'title_plural': 'Droughts',
            'description': 'Extended period of deficient rainfall',
            'icon': 'fa-sun',
            'color': '#ffc107',
            'active': True,
            'order': 7,
            'is_default': True
        },
        {
            'id': 'armed-conflict',
            'name': 'armed-conflict',
            'title': 'Armed Conflict',
            'title_plural': 'Armed Conflicts',
            'description': 'Military conflicts and war-related emergencies',
            'icon': 'fa-crosshairs',
            'color': '#343a40',
            'active': True,
            'order': 8,
            'is_default': True
        }
    ]


@tk.side_effect_free
def event_types_list(context, data_dict):
    """List all event types (active and inactive)"""
    try:
        # For listing, anyone can see the event types
        # We don't use check_access here since this is used for dropdowns
        pass
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    
    # Get custom event types from configuration or database
    # For now, we'll use CKAN config to store event types
    # In a full implementation, you might want to use a separate database table
    
    try:
        # Try to get custom event types from config
        custom_types_json = tk.config.get('ckanext.pages.event_types', '')
        if custom_types_json:
            event_types = json.loads(custom_types_json)
        else:
            # Return default event types
            event_types = _get_default_event_types()
    except (json.JSONDecodeError, ValueError):
        # Fallback to default types if JSON is invalid
        event_types = _get_default_event_types()
    
    # Filter by active status if requested
    active_only = data_dict.get('active_only', False)
    if active_only:
        event_types = [et for et in event_types if et.get('active', True)]
    
    # Sort by order
    event_types.sort(key=lambda x: x.get('order', 999))
    
    return event_types


@tk.side_effect_free
def event_types_show(context, data_dict):
    """Show a specific event type"""
    try:
        p.toolkit.check_access('ckanext_event_types_show', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))
    
    event_type_id = data_dict.get('id')
    if not event_type_id:
        raise p.toolkit.ValidationError({'id': ['Missing value']})
    
    # Get all event types and find the requested one
    all_types = event_types_list(context, {})
    event_type = next((et for et in all_types if et['id'] == event_type_id), None)
    
    if not event_type:
        p.toolkit.abort(404, p.toolkit._('Event type not found'))
    
    return event_type


def event_types_create(context, data_dict):
    """Create a new event type (sysadmin only)"""
    try:
        p.toolkit.check_access('ckanext_event_types_create', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to create event types'))
    
    from ckanext.pages.logic.schema import update_event_types_schema
    import ckan.lib.navl.dictization_functions as df
    
    schema = update_event_types_schema()
    data, errors = df.validate(data_dict, schema, context)
    
    if errors:
        raise p.toolkit.ValidationError(errors)
    
    # Get existing event types
    existing_types = event_types_list(context, {})
    
    # Check if name already exists
    event_name = data['name']
    if any(et['name'] == event_name for et in existing_types):
        raise p.toolkit.ValidationError({'name': ['Event type with this name already exists']})
    
    # Create new event type
    new_event_type = {
        'id': event_name,
        'name': event_name,
        'title': data['title'],
        'title_plural': data.get('title_plural', data['title'] + 's'),
        'description': data.get('description', ''),
        'icon': data.get('icon', 'fa-exclamation-triangle'),
        'color': data.get('color', '#007bff'),
        'active': data.get('active', True),
        'order': data.get('order', len(existing_types) + 1),
        'created': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'is_default': False
    }
    
    # Add to existing types
    existing_types.append(new_event_type)
    
    # Save to config (in a full implementation, you'd save to database)
    try:
        # Note: This requires CKAN configuration to be writable
        # In production, you might want to use a separate configuration mechanism
        config_value = json.dumps(existing_types)
        # For now, we'll just return the new type since config writing requires special permissions
        # tk.config['ckanext.pages.event_types'] = config_value
    except Exception as e:
        import logging
        log = logging.getLogger(__name__)
        log.warning("Could not save event types to config: %s", str(e))
    
    return new_event_type


def event_types_update(context, data_dict):
    """Update an existing event type (sysadmin only)"""
    try:
        p.toolkit.check_access('ckanext_event_types_update', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to update event types'))
    
    from ckanext.pages.logic.schema import update_event_types_schema
    import ckan.lib.navl.dictization_functions as df
    
    schema = update_event_types_schema()
    data, errors = df.validate(data_dict, schema, context)
    
    if errors:
        raise p.toolkit.ValidationError(errors)
    
    event_type_id = data.get('id')
    if not event_type_id:
        raise p.toolkit.ValidationError({'id': ['Missing value']})
    
    # Get existing event types
    existing_types = event_types_list(context, {})
    
    # Find the event type to update
    event_type_index = None
    for i, et in enumerate(existing_types):
        if et['id'] == event_type_id:
            event_type_index = i
            break
    
    if event_type_index is None:
        p.toolkit.abort(404, p.toolkit._('Event type not found'))
    
    # Check if it's a default type and prevent certain changes
    current_type = existing_types[event_type_index]
    if current_type.get('is_default', False):
        # Allow only certain fields to be updated for default types
        allowed_fields = ['title', 'title_plural', 'description', 'icon', 'color', 'active', 'order']
        for field in data:
            if field not in allowed_fields and field in current_type:
                data[field] = current_type[field]
    
    # Update the event type
    updated_type = existing_types[event_type_index].copy()
    updated_type.update(data)
    updated_type['modified'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    existing_types[event_type_index] = updated_type
    
    # Save to config (in a full implementation, you'd save to database)
    try:
        config_value = json.dumps(existing_types)
        # tk.config['ckanext.pages.event_types'] = config_value
    except Exception as e:
        import logging
        log = logging.getLogger(__name__)
        log.warning("Could not save event types to config: %s", str(e))
    
    return updated_type


def event_types_delete(context, data_dict):
    """Delete an event type (sysadmin only)"""
    try:
        p.toolkit.check_access('ckanext_event_types_delete', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to delete event types'))
    
    event_type_id = data_dict.get('id')
    if not event_type_id:
        raise p.toolkit.ValidationError({'id': ['Missing value']})
    
    # Get existing event types
    existing_types = event_types_list(context, {})
    
    # Find the event type to delete
    event_type_index = None
    for i, et in enumerate(existing_types):
        if et['id'] == event_type_id:
            event_type_index = i
            break
    
    if event_type_index is None:
        p.toolkit.abort(404, p.toolkit._('Event type not found'))
    
    # Check if it's a default type
    current_type = existing_types[event_type_index]
    if current_type.get('is_default', False):
        raise p.toolkit.ValidationError({'id': ['Cannot delete default event types. You can deactivate them instead.']})
    
    # Check if any rapid response pages are using this event type
    try:
        pages_using_type = tk.get_action('ckanext_pages_list')(
            context, {'page_type': 'rapid-response', 'event_type': event_type_id}
        )
        if pages_using_type:
            raise p.toolkit.ValidationError({
                'id': [f'Cannot delete event type. It is being used by {len(pages_using_type)} rapid response page(s).']
            })
    except Exception:
        # If we can't check, allow deletion but warn
        pass
    
    # Remove the event type
    deleted_type = existing_types.pop(event_type_index)
    
    # Save to config
    try:
        config_value = json.dumps(existing_types)
        # tk.config['ckanext.pages.event_types'] = config_value
    except Exception as e:
        import logging
        log = logging.getLogger(__name__)
        log.warning("Could not save event types to config: %s", str(e))
    
    return deleted_type
