import datetime
import json
import logging

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
    log = logging.getLogger(__name__)
    org_id = data_dict.get('org_id')
    page = data_dict.get('page')

    try:
        # Ensure valid database session before query
        if not ensure_valid_session():
            log.error("Database session is invalid, cannot fetch page")
            return None

        out = db.Page.get(group_id=org_id, name=page)
        if out:
            out = db.table_dictize(out, context)
        return out
    except Exception as e:
        log = logging.getLogger(__name__)
        error_str = str(e).lower()
        
        # Different logging based on error type
        if any(keyword in error_str for keyword in [
            'server closed the connection',
            'connection unexpectedly',
            'nonetype',
            'cursor',
            'connection refused',
            'no connection to the server'
        ]):
            log.warning("Database connection error fetching page: %s", str(e))
        else:
            log.error("Error fetching page: %s", str(e))
        return None


def _pages_list(context, data_dict):
    log = logging.getLogger(__name__)
    search = {}
    org_id = data_dict.get('org_id')
    ordered = data_dict.get('order')
    order_publish_date = data_dict.get('order_publish_date')
    page_type = data_dict.get('page_type')
    private = data_dict.get('private', True)
    limit = data_dict.get('limit')
    offset = data_dict.get('offset')
    
    # New search and filter parameters
    q = data_dict.get('q')  # Search query
    event_type = data_dict.get('event_type')  # Event type filter
    order_by = data_dict.get('order_by')  # Custom ordering
    submission_status = data_dict.get('submission_status')  # Submission status filter
    
    # DEBUG: Log filtering parameters for open-source-software
    if page_type == 'open-source-software':
        log.info(f"[PAGES_LIST] Filtering open-source-software - private: {private}, submission_status: {submission_status}")
    
    # Additional filters for rapid-response pages
    country = data_dict.get('country')  # Country filter
    activity_status = data_dict.get('activity_status')  # Activity status filter
    severity = data_dict.get('severity')  # Severity filter
    event_status = data_dict.get('event_status')  # Event status filter
    
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
    if country:
        search['country'] = country
    if activity_status:
        search['activity_status'] = activity_status
    if severity:
        search['severity'] = severity
    if event_status:
        search['event_status'] = event_status
    if submission_status:
        search['submission_status'] = submission_status
    if limit is not None:
        try:
            limit_value = tk.asint(limit)
            if limit_value < 0:
                raise ValueError("limit must be >= 0")
            search['limit'] = limit_value
        except (TypeError, ValueError):
            log.warning("Invalid pages_list limit value: %r", limit)
    if offset is not None:
        try:
            offset_value = tk.asint(offset)
            if offset_value < 0:
                raise ValueError("offset must be >= 0")
            search['offset'] = offset_value
        except (TypeError, ValueError):
            log.warning("Invalid pages_list offset value: %r", offset)
        
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
        if not ensure_valid_session():
            log.error("Database session is invalid, returning empty list")
            return []
        
        # Debug logging for filtering
        if log.isEnabledFor(logging.DEBUG):
            log.debug(f"Pages list search parameters: {search}")
            if country:
                log.debug(f"Filtering by country: {country}")
            if activity_status:
                log.debug(f"Filtering by activity_status: {activity_status}")
        
        # Additional debug for open-source-software
        if search.get('page_type') == 'open-source-software':
            log.info(f"[PAGES_LIST] Executing query with search params: {search}")
            
        out = db.Page.pages(**search)
        
        # Log results count for open-source-software
        if search.get('page_type') == 'open-source-software':
            log.info(f"[PAGES_LIST] Query returned {len(out)} results for open-source-software")
    except Exception as e:
        # Log the error and return empty list as fallback
        error_str = str(e).lower()
        
        # Different logging based on error type
        if any(keyword in error_str for keyword in [
            'server closed the connection',
            'connection unexpectedly',
            'nonetype',
            'cursor',
            'connection refused',
            'no connection to the server'
        ]):
            log.warning("Database connection error fetching pages list: %s", str(e))
        else:
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
                      'private': pg.private,
                      'submission_status': getattr(pg, 'submission_status', None),
                      'user_id': getattr(pg, 'user_id', None),
                      'ihp_organization': getattr(pg, 'ihp_organization', None),
                      'featured': getattr(pg, 'featured', False),
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
    log = logging.getLogger(__name__)
    org_id = data_dict.get('org_id')
    page = data_dict.get('page')
    # we need the page in the context for name validation
    context['page'] = page
    context['group_id'] = org_id
    schema = update_pages_schema()

    # DEBUG: Log incoming data_dict
    log.info(f"[PAGES_UPDATE] Processing page '{page}' with data_dict keys: {list(data_dict.keys())}")
    if 'content' in data_dict:
        content_preview = data_dict['content'][:100] if data_dict['content'] else 'EMPTY'
        log.info(f"[PAGES_UPDATE] 'content' field present in data_dict: {len(data_dict['content']) if data_dict['content'] else 0} chars, preview: {content_preview}")
    else:
        log.warning(f"[PAGES_UPDATE] 'content' field NOT present in data_dict!")

    # +1 is the Current state by default while ckanext.pages.revisions_limit is the amounf of previous states
    revisions_limit = tk.asint(tk.config.get('ckanext.pages.revisions_limit', '3')) + 1
    force_revisions_limit = tk.asbool(tk.config.get('ckanext.pages.revisions_force_limit', False))

    data, errors = df.validate(data_dict, schema, context)

    # DEBUG: Log data after validation
    if 'content' in data:
        content_preview = data['content'][:100] if data['content'] else 'EMPTY'
        log.info(f"[PAGES_UPDATE] After validation - 'content' field: {len(data['content']) if data['content'] else 0} chars, preview: {content_preview}")
    else:
        log.warning(f"[PAGES_UPDATE] After validation - 'content' field NOT in validated data!")

    # DEBUG: Check if submission_status survived validation
    log.info(f"[PAGES_UPDATE] After validation - submission_status in data: {'submission_status' in data}, value: {data.get('submission_status')}")
    log.info(f"[PAGES_UPDATE] After validation - submission_status in data_dict: {'submission_status' in data_dict}, value: {data_dict.get('submission_status')}")

    if errors:
        raise p.toolkit.ValidationError(errors)

    out = db.Page.get(group_id=org_id, name=page)
    if not out:
        out = db.Page()
        out.group_id = org_id
        out.name = page
    # `featured` is admin-only. Strip it from non-admin payloads so the
    # regular edit form can never flip it via a crafted request — toggling
    # is exposed via a dedicated admin endpoint instead.
    if 'featured' in data or 'ihp_official' in data or 'ihp_official' in data_dict:
        try:
            _is_admin_for_featured = tk.check_access('sysadmin', context, {})
        except Exception:
            _is_admin_for_featured = False
        if not _is_admin_for_featured:
            data.pop('featured', None)
            data.pop('ihp_official', None)
            data_dict.pop('featured', None)
            data_dict.pop('ihp_official', None)

    items = ['title', 'content', 'name', 'private',
             'order', 'page_type', 'publish_date', 'submission_status',
             'ihp_organization', 'submitted_at', 'reviewed_at', 'reviewed_by',
             'featured']

    # Handle submission workflow for open-source-software and water-family types
    submission_action_raw = data_dict.get('submission_action')
    submission_action = None
    if isinstance(submission_action_raw, str):
        normalized_action = submission_action_raw.strip().lower()
        if normalized_action in {'draft', 'submit', 'publish'}:
            submission_action = normalized_action

    water_family_types = ['open-source-software', 'ai-water-tools', 'water-news', 'water-events', 'water-publications', 'crida-case-study']
    target_page_type = data.get('page_type') or data_dict.get('page_type')
    if not target_page_type and out:
        target_page_type = out.page_type

    if submission_action and target_page_type in water_family_types:
        # Protect publish from privilege escalation via crafted requests.
        if submission_action == 'publish':
            is_admin_for_publish = False
            try:
                is_admin_for_publish = tk.check_access('sysadmin', context, {})
            except Exception:
                is_admin_for_publish = False

            if not is_admin_for_publish:
                log.warning(
                    "[PAGES_UPDATE] User '%s' attempted publish without sysadmin rights. Forcing submit workflow.",
                    context.get('user')
                )
                submission_action = 'submit'

        if submission_action == 'draft':
            data['submission_status'] = 'draft'
            data['private'] = True  # Keep as private for drafts
            # Clear previous review metadata when reverting to draft
            data['reviewed_at'] = None
            data['reviewed_by'] = None
        elif submission_action == 'submit':
            data['submission_status'] = 'pending'
            data['private'] = True  # Keep private until approved
            data['submitted_at'] = datetime.datetime.utcnow()
            # Clear previous review metadata on resubmission
            data['reviewed_at'] = None
            data['reviewed_by'] = None
            # Auto-set organization from user if not already set
            if not data.get('ihp_organization'):
                user_org = _get_user_organization(context['user'])
                if user_org:
                    data['ihp_organization'] = user_org.id
                    log = logging.getLogger(__name__)
                    log.info(f"Auto-assigned organization {user_org.title or user_org.display_name or user_org.name} to user {context['user']}")
        elif submission_action == 'publish':
            data['submission_status'] = 'approved'
            data['private'] = False
            now = datetime.datetime.utcnow()
            data['reviewed_at'] = now.isoformat()
            reviewer = context.get('user') or getattr(tk.g, 'user', None)
            if reviewer:
                data['reviewed_by'] = reviewer
            # Ensure submitted_at populated if never set
            if not data.get('submitted_at'):
                data['submitted_at'] = now

    # Ensure organization handling for open-source-software and water-family types
    if data.get('page_type') in water_family_types:
        # Non-admins: validate the selected org belongs to the user
        is_admin = False
        try:
            is_admin = tk.check_access('sysadmin', context, {})
        except Exception:
            is_admin = False

        if not is_admin:
            # Get ALL organizations the user belongs to
            user_org_ids = set()
            try:
                user_obj = model.User.get(context['user'])
                if user_obj:
                    member_orgs = model.Session.query(model.Member.group_id).filter(
                        model.Member.table_name == 'user',
                        model.Member.table_id == user_obj.id,
                        model.Member.group_id.in_(
                            model.Session.query(model.Group.id).filter(
                                model.Group.type == 'organization',
                                model.Group.state == 'active'
                            )
                        )
                    ).all()
                    user_org_ids = {m.group_id for m in member_orgs}
            except Exception:
                pass

            submitted_org = data.get('ihp_organization')
            if submitted_org and submitted_org in user_org_ids:
                # User selected one of their own orgs — allow it
                log.info(f"User {context['user']} selected valid organization {submitted_org}")
            elif user_org_ids:
                # Invalid or missing org — default to first user org
                fallback_org_id = next(iter(user_org_ids))
                data['ihp_organization'] = fallback_org_id
                log.info(f"Defaulted organization to {fallback_org_id} for user {context['user']}")
        else:
            # Admins: if missing, try to default to user's org to avoid empty values
            if not data.get('ihp_organization'):
                user_org = _get_user_organization(context['user'])
                if user_org:
                    data['ihp_organization'] = user_org.id
                    log = logging.getLogger(__name__)
                    org_label = user_org.title or user_org.display_name or user_org.name
                    log.info(f"Defaulted organization to {org_label} for admin {context['user']}")

    # backward compatible with older version where page_type does not exist
    workflow_computed_fields = {'submission_status', 'private', 'submitted_at', 'reviewed_at', 'reviewed_by'}
    for item in items:
        if item in ['submitted_at', 'reviewed_at'] and data.get(item):
            # Handle datetime fields
            if isinstance(data.get(item), str):
                try:
                    setattr(out, item, datetime.datetime.fromisoformat(data.get(item).replace('Z', '+00:00')))
                except (ValueError, TypeError):
                    setattr(out, item, datetime.datetime.utcnow())
            else:
                setattr(out, item, data.get(item))
        else:
            # For workflow fields generated from submission_action, prefer computed
            # values from validated data and do not overwrite from raw form payload.
            if submission_action and item in workflow_computed_fields:
                if item in data:
                    value = data.get(item)
                else:
                    value = data_dict.get(item)
            # CRITICAL FIX: For fields that might be lost during validation,
            # check data_dict first, then data, then use default
            # Prefer data_dict for non-workflow fields to avoid validation stripping
            elif item in data_dict and data_dict.get(item):
                # Use data_dict value if it exists and is not empty
                value = data_dict.get(item)
                if item in data and data.get(item) != value:
                    log.info(f"[PAGES_UPDATE] Using data_dict value for '{item}': {value} (data had: {data.get(item)})")
            elif item in data:
                value = data.get(item)
            else:
                value = 'page' if item == 'page_type' else None

            # Ensure 'private' is always a proper boolean, not a string
            if item == 'private':
                value = tk.asbool(value) if value is not None else False
            elif item == 'featured':
                if value in (None, ''):
                    value = bool(getattr(out, 'featured', False))
                else:
                    value = tk.asbool(value)

            setattr(out, item, value)
            # DEBUG: Log content field specifically
            if item == 'content':
                content_len = len(value) if value else 0
                log.info(f"[PAGES_UPDATE] Setting 'content' attribute: {content_len} chars")
            # DEBUG: Log critical fields for open-source-software
            if item in ['submission_status', 'ihp_organization', 'private']:
                log.info(f"[PAGES_UPDATE] Setting '{item}' attribute: {value} (from data_dict: {data_dict.get(item)}, from data: {data.get(item)})")

    # Start with existing extras from DB to preserve fields not in the
    # current form submission (prevents silent data loss on edit).
    existing_extras = {}
    if out.extras:
        try:
            existing_extras = json.loads(out.extras) if isinstance(out.extras, str) else out.extras
            if not isinstance(existing_extras, dict):
                existing_extras = {}
        except (ValueError, TypeError):
            existing_extras = {}

    extras = existing_extras.copy()

    # Sysadmin "IHP Official" override: an empty submitted value means the
    # admin chose "Auto", so the previous override (if any) must be cleared
    # rather than silently preserved by the merge below. Only sysadmins
    # could have submitted this field — non-admin payloads were stripped
    # earlier (see `featured` handling above).
    if 'ihp_official' in data_dict:
        raw_official = data_dict.get('ihp_official')
        if isinstance(raw_official, str) and raw_official.strip() == '':
            extras.pop('ihp_official', None)

    extra_keys = set(schema.keys()) - set(items + ['id', 'created'])
    for key in extra_keys:
        if key in data:
            value = data.get(key)
            # Handle datetime objects by converting to ISO format strings
            if isinstance(value, datetime.datetime):
                extras[key] = value.isoformat()
            elif isinstance(value, str):
                # Deserialize JSON strings so json.dumps(extras) won't
                # double-encode them (e.g. uploaded_images, timeline_events).
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, (list, dict)):
                        extras[key] = parsed
                    else:
                        extras[key] = value
                except (ValueError, TypeError):
                    extras[key] = value
            else:
                extras[key] = value
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

    # DEBUG: Log final saved content and critical fields
    log.info(f"[PAGES_UPDATE] Page '{page}' saved successfully. Content length: {len(out.content) if out.content else 0} chars")
    log.info(f"[PAGES_UPDATE] Final state - submission_status: {out.submission_status}, private: {out.private}, ihp_organization: {out.ihp_organization}")


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

    log = logging.getLogger(__name__)
    log.info(f"[PAGES_UPLOAD] Starting upload - data_dict keys: {list(data_dict.keys()) if data_dict else 'None'}")

    try:
        try:
            p.toolkit.check_access('ckanext_pages_upload', context, data_dict)
        except p.toolkit.NotAuthorized:
            log.error("[PAGES_UPLOAD] Authorization failed")
            raise

        # Use the plugin system to get the appropriate uploader
        # This will use asset-storage if available, or fall back to default Upload
        use_fallback = False
        log.info("[PAGES_UPLOAD] Getting uploader through plugin system")
        
        try:
            # Use CKAN's plugin system to get the right uploader
            # This will call asset-storage's get_uploader() if available
            upload = uploader.get_uploader('page_images')
            log.info(f"[PAGES_UPLOAD] Successfully got uploader: {type(upload).__name__}")
        except Exception as e:
            # Fallback to base Upload if plugin system fails
            log.warning(f"[PAGES_UPLOAD] Plugin uploader failed with {type(e).__name__}: {str(e)}, using base Upload")
            from ckan.lib.uploader import Upload
            upload = Upload(object_type='page_images')
            log.info("[PAGES_UPLOAD] Using base Upload class")

        log.info("[PAGES_UPLOAD] Updating data_dict with file info")

        # Update data dict with upload info
        upload.update_data_dict(data_dict, 'image_url', 'upload', 'clear_upload')

        max_image_size = uploader.get_max_image_size()
        log.info(f"[PAGES_UPLOAD] Attempting upload with max size: {max_image_size}MB")

        try:
            upload.upload(max_image_size)
            log.info("[PAGES_UPLOAD] Upload successful")

            # Set image_url from uploaded filename if not already set
            if not data_dict.get('image_url') and upload.filename:
                data_dict['image_url'] = upload.filename
                log.info(f"[PAGES_UPLOAD] Set image_url from upload: {upload.filename}")
        except p.toolkit.ValidationError as e:
            log.error(f"[PAGES_UPLOAD] Validation error: {str(e)}")
            message = (
                "Can't upload the file, size is too large. "
                "(Max allowed is {0}mb)".format(max_image_size)
            )
            return {'uploaded': 0, 'error': {'message': message}}

    except Exception as e:
        log.error(f"[PAGES_UPLOAD] Unexpected error during upload: {type(e).__name__}: {str(e)}", exc_info=True)
        return {'uploaded': 0, 'error': {'message': f'Upload failed: {str(e)}'}}

    # Procesar la imagen si es un logo
    image_url = data_dict.get('image_url')
    # Ensure image_url is a string (could be int from form processing)
    if image_url is not None and not isinstance(image_url, str):
        image_url = str(image_url) if image_url else None
    is_logo = data_dict.get('is_logo', False)
    add_background = data_dict.get('add_background', False)
    
    if image_url and is_logo:
        try:
            # Obtener la ruta del archivo subido
            if isinstance(image_url, str) and image_url[0:6] not in {'http:/', 'https:'}:
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
            log = logging.getLogger(__name__)
            log.error(f"Error processing logo image: {str(e)}")
    
    # Generar URL final
    if image_url and isinstance(image_url, str) and image_url[0:6] not in {'http:/', 'https:'}:
        image_url = h.url_for_static(
            'uploads/page_images/%s' % image_url,
            qualified=True
        )
    
    # Ensure filename is a string
    filename = upload.filename if hasattr(upload, 'filename') else None
    if filename is not None and not isinstance(filename, str):
        filename = str(filename) if filename else None
    
    return {'url': image_url, 'fileName': filename, 'uploaded': 1}


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
                except (OSError, IOError):
                    pass
            
            return processed_path
            
    except Exception as e:
        log = logging.getLogger(__name__)
        log.error(f"Error processing logo image: {str(e)}")
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


# Water Family Public API Actions

WATER_FAMILY_TYPES = ['water-news', 'water-events', 'water-publications', 'crida-case-study']
WATER_FAMILY_LIST_MAX_LIMIT = 100
WATER_FAMILY_LIST_DEFAULT_LIMIT = 20


def _water_family_list(context, data_dict):
    """Internal function to list water family content with filters.

    Only returns public, approved content. Supports filtering by page_type,
    initiative, member_state, organization, water_type, water_category,
    full-text search, and pagination.
    """
    log = logging.getLogger(__name__)
    search = {}

    # Restrict to water family page types
    page_type = data_dict.get('page_type')
    if page_type:
        if page_type not in WATER_FAMILY_TYPES:
            raise p.toolkit.ValidationError(
                {'page_type': ['Must be one of: %s' % ', '.join(WATER_FAMILY_TYPES)]}
            )
        search['page_type'] = page_type

    # Security: only public, approved content
    search['private'] = False
    search['submission_status'] = 'approved'

    # Water family specific filters
    initiative = data_dict.get('initiative')
    if initiative:
        search['initiative'] = initiative

    member_state = data_dict.get('member_state')
    if member_state:
        search['member_state'] = member_state

    organization = data_dict.get('organization')
    if organization:
        search['ihp_organization'] = organization

    # Common filters
    q = data_dict.get('q')
    if q:
        search['q'] = q

    water_type = data_dict.get('water_type')
    if water_type:
        search['water_type'] = water_type

    water_category = data_dict.get('water_category')
    if water_category:
        search['water_category'] = water_category

    # Ordering
    order_publish_date = data_dict.get('order_publish_date', True)
    if order_publish_date:
        search['order_publish_date'] = True

    # Pagination
    limit = WATER_FAMILY_LIST_DEFAULT_LIMIT
    if data_dict.get('limit') is not None:
        try:
            limit = min(max(0, tk.asint(data_dict['limit'])),
                        WATER_FAMILY_LIST_MAX_LIMIT)
        except (TypeError, ValueError):
            log.warning("Invalid water_family_list limit: %r", data_dict.get('limit'))
    search['limit'] = limit

    offset = 0
    if data_dict.get('offset') is not None:
        try:
            offset = max(0, tk.asint(data_dict['offset']))
        except (TypeError, ValueError):
            log.warning("Invalid water_family_list offset: %r", data_dict.get('offset'))
    search['offset'] = offset

    # No org_id means site-wide pages
    search['group_id'] = None

    try:
        if not ensure_valid_session():
            log.error("Database session invalid for water_family_list")
            return {'count': 0, 'results': []}

        # Get count without limit/offset for pagination metadata
        count_search = {k: v for k, v in search.items()
                        if k not in ('limit', 'offset')}
        total_results = db.Page.pages(**count_search)
        total_count = len(total_results)

        # If no page_type specified, filter to water family types only
        if not page_type:
            total_results = [pg for pg in total_results
                            if pg.page_type in WATER_FAMILY_TYPES]
            total_count = len(total_results)

        # Get paginated results
        out = db.Page.pages(**search)

        # Filter to water family types if no specific type requested
        if not page_type:
            out = [pg for pg in out if pg.page_type in WATER_FAMILY_TYPES]

    except Exception as e:
        log.error("Error in water_family_list: %s", str(e))
        return {'count': 0, 'results': []}

    out_list = []
    for pg in out:
        try:
            parser = HTMLFirstImage()
            if pg.content:
                parser.feed(pg.content)
            img = parser.first_image

            pg_row = {
                'title': pg.title,
                'name': pg.name,
                'content': pg.content,
                'publish_date': pg.publish_date.isoformat() if pg.publish_date else None,
                'page_type': pg.page_type,
                'created': pg.created.isoformat() if pg.created else None,
                'modified': pg.modified.isoformat() if pg.modified else None,
                'ihp_organization': getattr(pg, 'ihp_organization', None),
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
            log.warning("Error processing page %s: %s",
                        getattr(pg, 'name', 'unknown'), str(e))
            continue

    return {
        'count': total_count,
        'results': out_list,
    }


@tk.side_effect_free
def water_family_list(context, data_dict):
    """Public API: List water family content (news, events, publications).

    Filterable by page_type, initiative, member_state, organization,
    water_type, water_category, and free-text search. Only returns
    public, approved content. No authentication required.

    :param page_type: Filter by type (water-news, water-events, water-publications)
    :param initiative: Filter by initiative name
    :param member_state: Filter by member state name
    :param organization: Filter by IHP organization ID
    :param q: Free-text search query
    :param water_type: Filter by water type
    :param water_category: Filter by water category
    :param limit: Max results (default 20, max 100)
    :param offset: Pagination offset
    :param order_publish_date: Order by publish date desc (default True)
    :returns: dict with 'count' (total) and 'results' (list of page dicts)
    """
    try:
        p.toolkit.check_access('ckanext_water_family_list', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized'))
    return _water_family_list(context, data_dict)


@tk.side_effect_free
def water_family_show(context, data_dict):
    """Public API: Show a single water family page by name/slug.

    Only returns public, approved content. No authentication required.

    :param page: Page name/slug (required)
    :returns: dict with page details, or None if not found/not public
    """
    try:
        p.toolkit.check_access('ckanext_water_family_show', context, data_dict)
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized'))

    page_name = data_dict.get('page')
    if not page_name:
        raise p.toolkit.ValidationError({'page': ['Missing value']})

    try:
        if not ensure_valid_session():
            return None

        out = db.Page.get(name=page_name)
        if not out:
            return None

        # Only return public, approved water family content
        if out.page_type not in WATER_FAMILY_TYPES:
            return None
        if out.private:
            return None
        if getattr(out, 'submission_status', None) != 'approved':
            return None

        result = db.table_dictize(out, context)
        return result

    except Exception as e:
        log = logging.getLogger(__name__)
        log.error("Error in water_family_show: %s", str(e))
        return None


# Event Types Management Actions

def _get_default_event_types():
    """Get default event types for water events"""
    return [
        {
            'id': 'conference',
            'name': 'conference',
            'title': 'Conference',
            'title_plural': 'Conferences',
            'description': 'Large-scale professional gathering for presentations and networking',
            'icon': 'fa-users',
            'color': '#0072BC',
            'active': True,
            'order': 1,
            'is_default': True
        },
        {
            'id': 'workshop',
            'name': 'workshop',
            'title': 'Workshop',
            'title_plural': 'Workshops',
            'description': 'Interactive session focused on practical skills and collaboration',
            'icon': 'fa-wrench',
            'color': '#009EE0',
            'active': True,
            'order': 2,
            'is_default': True
        },
        {
            'id': 'seminar',
            'name': 'seminar',
            'title': 'Seminar',
            'title_plural': 'Seminars',
            'description': 'Educational session led by an expert on a specific topic',
            'icon': 'fa-chalkboard-teacher',
            'color': '#005A9C',
            'active': True,
            'order': 3,
            'is_default': True
        },
        {
            'id': 'training',
            'name': 'training',
            'title': 'Training',
            'title_plural': 'Trainings',
            'description': 'Structured learning programme to develop specific competencies',
            'icon': 'fa-graduation-cap',
            'color': '#28a745',
            'active': True,
            'order': 4,
            'is_default': True
        },
        {
            'id': 'webinar',
            'name': 'webinar',
            'title': 'Webinar',
            'title_plural': 'Webinars',
            'description': 'Online presentation or lecture accessible remotely',
            'icon': 'fa-desktop',
            'color': '#17a2b8',
            'active': True,
            'order': 5,
            'is_default': True
        },
        {
            'id': 'meeting',
            'name': 'meeting',
            'title': 'Meeting',
            'title_plural': 'Meetings',
            'description': 'Formal or informal gathering for discussion and decision-making',
            'icon': 'fa-handshake',
            'color': '#6f42c1',
            'active': True,
            'order': 6,
            'is_default': True
        },
        {
            'id': 'prize-award',
            'name': 'prize-award',
            'title': 'Prize Award',
            'title_plural': 'Prize Awards',
            'description': 'Ceremony recognising outstanding contributions in water science',
            'icon': 'fa-trophy',
            'color': '#ffc107',
            'active': True,
            'order': 7,
            'is_default': True
        },
        {
            'id': 'ceremony',
            'name': 'ceremony',
            'title': 'Ceremony',
            'title_plural': 'Ceremonies',
            'description': 'Formal event marking a special occasion or milestone',
            'icon': 'fa-star',
            'color': '#e83e8c',
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
        log = logging.getLogger(__name__)
        log.warning("Could not save event types to config: %s", str(e))
    
    return deleted_type


# Disaster Types Management Actions

def _get_default_disaster_types():
    """Get default disaster types for rapid response events"""
    return [
        {
            'id': 'tropical-cyclone',
            'name': 'tropical-cyclone',
            'title': 'Tropical Cyclone',
            'title_plural': 'Tropical Cyclones',
            'description': 'Hurricanes, typhoons, and cyclones with strong winds and heavy rainfall',
            'icon': 'fa-wind',
            'color': '#0072BC',
            'active': True,
            'order': 1,
            'is_default': True
        },
        {
            'id': 'earthquake',
            'name': 'earthquake',
            'title': 'Earthquake',
            'title_plural': 'Earthquakes',
            'description': 'Seismic events causing ground shaking and structural damage',
            'icon': 'fa-house-damage',
            'color': '#8B4513',
            'active': True,
            'order': 2,
            'is_default': True
        },
        {
            'id': 'tsunami',
            'name': 'tsunami',
            'title': 'Tsunami',
            'title_plural': 'Tsunamis',
            'description': 'Large ocean waves caused by underwater earthquakes or volcanic eruptions',
            'icon': 'fa-water',
            'color': '#005A9C',
            'active': True,
            'order': 3,
            'is_default': True
        },
        {
            'id': 'flood',
            'name': 'flood',
            'title': 'Flood',
            'title_plural': 'Floods',
            'description': 'Overflow of water submerging normally dry land areas',
            'icon': 'fa-cloud-showers-heavy',
            'color': '#009EE0',
            'active': True,
            'order': 4,
            'is_default': True
        },
        {
            'id': 'wildfire',
            'name': 'wildfire',
            'title': 'Wildfire',
            'title_plural': 'Wildfires',
            'description': 'Uncontrolled fires in vegetation areas affecting water resources',
            'icon': 'fa-fire',
            'color': '#FF4500',
            'active': True,
            'order': 5,
            'is_default': True
        },
        {
            'id': 'volcanic-eruption',
            'name': 'volcanic-eruption',
            'title': 'Volcanic Eruption',
            'title_plural': 'Volcanic Eruptions',
            'description': 'Eruptions of molten rock, ash, and gases from volcanoes',
            'icon': 'fa-mountain',
            'color': '#DC143C',
            'active': True,
            'order': 6,
            'is_default': True
        },
        {
            'id': 'drought',
            'name': 'drought',
            'title': 'Drought',
            'title_plural': 'Droughts',
            'description': 'Prolonged periods of abnormally low rainfall leading to water shortage',
            'icon': 'fa-sun',
            'color': '#DAA520',
            'active': True,
            'order': 7,
            'is_default': True
        },
        {
            'id': 'armed-conflict',
            'name': 'armed-conflict',
            'title': 'Armed Conflict',
            'title_plural': 'Armed Conflicts',
            'description': 'War-related water crises and destruction of water infrastructure',
            'icon': 'fa-shield-alt',
            'color': '#4B0082',
            'active': True,
            'order': 8,
            'is_default': True
        },
        {
            'id': 'man-made-disaster',
            'name': 'man-made-disaster',
            'title': 'Man-made Disaster',
            'title_plural': 'Man-made Disasters',
            'description': 'Human-caused disasters such as industrial contamination, bombing of water infrastructure, or chemical spills',
            'icon': 'fa-industry',
            'color': '#696969',
            'active': True,
            'order': 9,
            'is_default': True
        }
    ]


@tk.side_effect_free
def disaster_types_list(context, data_dict):
    """List all disaster types (active and inactive)"""
    try:
        pass
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(401, p.toolkit._('Not authorized to see this page'))

    try:
        custom_types_json = tk.config.get('ckanext.pages.disaster_types', '')
        if custom_types_json:
            disaster_types = json.loads(custom_types_json)
        else:
            disaster_types = _get_default_disaster_types()
    except (json.JSONDecodeError, ValueError):
        disaster_types = _get_default_disaster_types()

    active_only = data_dict.get('active_only', False)
    if active_only:
        disaster_types = [dt for dt in disaster_types if dt.get('active', True)]

    disaster_types.sort(key=lambda x: x.get('order', 999))

    return disaster_types


@tk.side_effect_free
def disaster_types_show(context, data_dict):
    """Show a single disaster type by ID"""
    try:
        p.toolkit.check_access('ckanext_disaster_types_show', context, data_dict)
    except p.toolkit.NotAuthorized:
        raise

    disaster_type_id = data_dict.get('id')
    if not disaster_type_id:
        raise p.toolkit.ValidationError({'id': ['Missing value']})

    all_types = disaster_types_list(context, {})
    disaster_type = next((dt for dt in all_types if dt['id'] == disaster_type_id), None)

    if not disaster_type:
        raise p.toolkit.ObjectNotFound('Disaster type not found')

    return disaster_type


def disaster_types_create(context, data_dict):
    """Create a new disaster type"""
    try:
        p.toolkit.check_access('ckanext_disaster_types_create', context, data_dict)
    except p.toolkit.NotAuthorized:
        raise

    from ckanext.pages.logic.schema import update_disaster_types_schema

    schema = update_disaster_types_schema()
    data, errors = df.validate(data_dict, schema, context)
    if errors:
        raise p.toolkit.ValidationError(errors)

    existing_types = disaster_types_list(context, {})

    new_id = data.get('id') or data.get('name', '').lower().replace(' ', '-')
    if any(dt['id'] == new_id for dt in existing_types):
        raise p.toolkit.ValidationError({'id': ['Disaster type ID already exists']})

    new_disaster_type = {
        'id': new_id,
        'name': data.get('name', new_id),
        'title': data.get('title', ''),
        'title_plural': data.get('title_plural', ''),
        'description': data.get('description', ''),
        'icon': data.get('icon', 'fa-exclamation-triangle'),
        'color': data.get('color', '#dc3545'),
        'active': data.get('active', True),
        'order': data.get('order', len(existing_types) + 1),
        'is_default': False,
        'created': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'modified': datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    existing_types.append(new_disaster_type)

    try:
        config_value = json.dumps(existing_types)
    except Exception as e:
        log = logging.getLogger(__name__)
        log.warning("Could not save disaster types to config: %s", str(e))

    return new_disaster_type


def disaster_types_update(context, data_dict):
    """Update an existing disaster type"""
    try:
        p.toolkit.check_access('ckanext_disaster_types_update', context, data_dict)
    except p.toolkit.NotAuthorized:
        raise

    from ckanext.pages.logic.schema import update_disaster_types_schema

    schema = update_disaster_types_schema()
    data, errors = df.validate(data_dict, schema, context)
    if errors:
        raise p.toolkit.ValidationError(errors)

    disaster_type_id = data.get('id')
    if not disaster_type_id:
        raise p.toolkit.ValidationError({'id': ['Missing value']})

    existing_types = disaster_types_list(context, {})

    disaster_type_index = None
    for i, dt in enumerate(existing_types):
        if dt['id'] == disaster_type_id:
            disaster_type_index = i
            break

    if disaster_type_index is None:
        raise p.toolkit.ObjectNotFound('Disaster type not found')

    current_type = existing_types[disaster_type_index]
    for key in ['title', 'title_plural', 'description', 'icon', 'color', 'active', 'order']:
        if key in data:
            current_type[key] = data[key]
    current_type['modified'] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    updated_type = existing_types[disaster_type_index].copy()
    existing_types[disaster_type_index] = updated_type

    try:
        config_value = json.dumps(existing_types)
    except Exception as e:
        log = logging.getLogger(__name__)
        log.warning("Could not save disaster types to config: %s", str(e))

    return updated_type


def disaster_types_delete(context, data_dict):
    """Delete a disaster type"""
    try:
        p.toolkit.check_access('ckanext_disaster_types_delete', context, data_dict)
    except p.toolkit.NotAuthorized:
        raise

    disaster_type_id = data_dict.get('id')
    if not disaster_type_id:
        raise p.toolkit.ValidationError({'id': ['Missing value']})

    existing_types = disaster_types_list(context, {})

    disaster_type_index = None
    for i, dt in enumerate(existing_types):
        if dt['id'] == disaster_type_id:
            disaster_type_index = i
            break

    if disaster_type_index is None:
        raise p.toolkit.ObjectNotFound('Disaster type not found')

    current_type = existing_types[disaster_type_index]
    if current_type.get('is_default', False):
        raise p.toolkit.ValidationError({
            'id': ['Cannot delete a default disaster type. You can deactivate it instead.']
        })

    try:
        pages_using_type = tk.get_action('ckanext_pages_list')(
            context, {'page_type': 'rapid-response', 'event_type': disaster_type_id}
        )
        if pages_using_type:
            raise p.toolkit.ValidationError({
                'id': [f'Cannot delete disaster type. It is being used by {len(pages_using_type)} rapid response page(s).']
            })
    except Exception:
        pass

    deleted_type = existing_types.pop(disaster_type_index)

    try:
        config_value = json.dumps(existing_types)
    except Exception as e:
        log = logging.getLogger(__name__)
        log.warning("Could not save disaster types to config: %s", str(e))

    return deleted_type


def _get_user_organization(username):
    """Get the organization associated with the current user"""
    try:
        if not username:
            return None

        # Get user's organizations (as a member)
        user_obj = model.User.get(username)
        if not user_obj:
            return None

        # Get organizations where user is a member
        member_orgs = model.Session.query(model.Member).filter(
            model.Member.table_name == 'user',
            model.Member.table_id == user_obj.id,
            model.Member.group_id.in_(
                model.Session.query(model.Group.id).filter(
                    model.Group.type == 'organization',
                    model.Group.state == 'active'
                )
            )
        ).all()

        if member_orgs:
            # Return the first organization (could be enhanced to handle multiple)
            org_id = member_orgs[0].group_id
            return model.Group.get(org_id)

        return None

    except Exception as e:
        log = logging.getLogger(__name__)
        log.error("Error getting user organization: %s", str(e))
        return None


def water_family_upload(context, data_dict):
    """Upload a file for water-family content (news, events, publications).

    This function provides specialized upload handling for water-family content types
    with specific validation rules and metadata management.

    Supported water-family types:
    - water-news: News articles with header images
    - water-events: Event content with promotional images
    - water-publications: Publications with PDFs and cover images

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - upload: File object to upload
            - water_content_type: Type of water content (water-news, water-events, water-publications)
            - file_type: Type of file (image, document, thumbnail)
            - asset_role: Optional semantic role for the asset (e.g. agenda_document)
            - is_logo: Boolean, if True processes image as logo (optional)
            - add_background: Boolean, add white background to logo (optional)

    Returns:
        Dict with upload result:
            - uploaded: 1 if successful, 0 if failed
            - url: URL of uploaded file
            - fileName: Name of uploaded file
            - metadata: Additional metadata about the file

    Raises:
        NotAuthorized: If user not authorized to upload
        ValidationError: If file validation fails
    """
    log = logging.getLogger(__name__)
    log.info(f"[WATER_FAMILY_UPLOAD] Starting upload - data_dict keys: {list(data_dict.keys()) if data_dict else 'None'}")

    # Extract water-specific parameters
    water_content_type = data_dict.get('water_content_type', '')
    file_type = data_dict.get('file_type', 'image')
    asset_role = data_dict.get('asset_role', '')

    # Validate water content type
    valid_water_types = ['water-news', 'water-events', 'water-publications']
    if water_content_type and water_content_type not in valid_water_types:
        log.error(f"[WATER_FAMILY_UPLOAD] Invalid water_content_type: {water_content_type}")
        return {'uploaded': 0, 'error': {'message': f'Invalid water content type: {water_content_type}'}}

    log.info(f"[WATER_FAMILY_UPLOAD] Water content type: {water_content_type}, file type: {file_type}, asset role: {asset_role}")

    try:
        # Authorization check - use water-specific auth
        try:
            p.toolkit.check_access('ckanext_water_family_upload', context, data_dict)
        except p.toolkit.NotAuthorized:
            log.error("[WATER_FAMILY_UPLOAD] Authorization failed")
            raise p.toolkit.NotAuthorized(p.toolkit._('Not authorized to upload files for water content'))

        # Validate file type and size based on water content type and file type
        validation_result = _validate_water_file(data_dict, water_content_type, file_type, asset_role=asset_role)
        if not validation_result['valid']:
            log.error(f"[WATER_FAMILY_UPLOAD] Validation failed: {validation_result['message']}")
            return {'uploaded': 0, 'error': {'message': validation_result['message']}}

        # Use the plugin system to get the appropriate uploader
        use_fallback = False
        log.info("[WATER_FAMILY_UPLOAD] Getting uploader through plugin system")
        
        try:
            upload = uploader.get_uploader('page_images')
            log.info(f"[WATER_FAMILY_UPLOAD] Successfully got uploader: {type(upload).__name__}")
        except Exception as e:
            log.warning(f"[WATER_FAMILY_UPLOAD] Plugin uploader failed with {type(e).__name__}: {str(e)}, using base Upload")
            from ckan.lib.uploader import Upload
            upload = Upload(object_type='page_images')
            log.info("[WATER_FAMILY_UPLOAD] Using base Upload class")

        log.info("[WATER_FAMILY_UPLOAD] Updating data_dict with file info")

        # Update data dict with upload info
        upload.update_data_dict(data_dict, 'image_url', 'upload', 'clear_upload')

        # Get max size based on file type
        max_size = validation_result['max_size_mb']
        log.info(f"[WATER_FAMILY_UPLOAD] Attempting upload with max size: {max_size}MB")

        try:
            upload.upload(max_size)
            log.info("[WATER_FAMILY_UPLOAD] Upload successful")

            # Set image_url from uploaded filename if not already set
            if not data_dict.get('image_url') and upload.filename:
                data_dict['image_url'] = upload.filename
                log.info(f"[WATER_FAMILY_UPLOAD] Set image_url from upload: {upload.filename}")
        except p.toolkit.ValidationError as e:
            log.error(f"[WATER_FAMILY_UPLOAD] Validation error: {str(e)}")
            message = f"Can't upload the file, size is too large. (Max allowed is {max_size}mb)"
            return {'uploaded': 0, 'error': {'message': message}}

    except Exception as e:
        log.error(f"[WATER_FAMILY_UPLOAD] Unexpected error: {type(e).__name__}: {str(e)}", exc_info=True)
        return {'uploaded': 0, 'error': {'message': f'Upload failed: {str(e)}'}}

    # Process image if it's a logo
    image_url = data_dict.get('image_url')
    is_logo = data_dict.get('is_logo', False)
    add_background = data_dict.get('add_background', False)

    if image_url and is_logo:
        try:
            if image_url[0:6] not in {'http:/', 'https:'}:
                upload_dir = upload.get_directory()
                image_path = os.path.join(upload_dir, image_url)
                processed_image_path = _process_logo_image(image_path, upload_dir, add_background)

                if processed_image_path:
                    image_url = os.path.basename(processed_image_path)
                    upload.filename = image_url
                    log.info(f"[WATER_FAMILY_UPLOAD] Logo processed: {image_url}")

        except Exception as e:
            log.error(f"[WATER_FAMILY_UPLOAD] Error processing logo: {str(e)}")

    # Generate final URL
    if image_url and image_url[0:6] not in {'http:/', 'https:'}:
        image_url = h.url_for_static(f'uploads/page_images/{image_url}', qualified=True)

    # Build metadata for water content
    metadata = _build_water_file_metadata(data_dict, water_content_type, file_type, validation_result)

    log.info(f"[WATER_FAMILY_UPLOAD] Upload completed successfully: {image_url}")
    return {'url': image_url, 'fileName': upload.filename, 'uploaded': 1, 'metadata': metadata}


def _validate_water_file(data_dict, water_content_type, file_type, asset_role=''):
    """Validate file for water-family content.

    Args:
        data_dict: Request data containing file info
        water_content_type: Type of water content (water-news, water-events, water-publications)
        file_type: Type of file (image, document, thumbnail)
        asset_role: Optional semantic role for the file

    Returns:
        Dict with validation result:
            - valid: Boolean
            - message: Error message if invalid
            - max_size_mb: Maximum allowed size in MB
            - allowed_extensions: List of allowed file extensions
    """
    log = logging.getLogger(__name__)

    # Define allowed file types and max sizes
    allowed_image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
    allowed_document_extensions = ['pdf', 'doc', 'docx']

    # Default max sizes (in MB)
    max_image_size = 5  # 5MB for images
    max_document_size = 20  # 20MB for documents (publications may have large PDFs)

    # Adjust based on water content type
    if water_content_type == 'water-publications':
        max_document_size = 30  # Allow larger PDFs for publications

    # Determine allowed extensions and max size based on file type
    if water_content_type == 'water-events' and asset_role == 'agenda_document':
        allowed_extensions = ['pdf'] + allowed_image_extensions
        max_size = max_document_size
    elif file_type == 'document':
        allowed_extensions = allowed_document_extensions
        max_size = max_document_size
    else:  # image, thumbnail, or default
        allowed_extensions = allowed_image_extensions
        max_size = max_image_size

    # Get uploaded file info
    upload_field = data_dict.get('upload')
    if not upload_field:
        return {'valid': False, 'message': 'No file provided', 'max_size_mb': max_size,
                'allowed_extensions': allowed_extensions}

    # Extract filename
    filename = getattr(upload_field, 'filename', '')
    if not filename:
        return {'valid': False, 'message': 'Invalid file', 'max_size_mb': max_size,
                'allowed_extensions': allowed_extensions}

    # Check file extension
    file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if file_ext not in allowed_extensions:
        allowed_exts_str = ', '.join(allowed_extensions)
        message = f'File type .{file_ext} not allowed. Allowed types: {allowed_exts_str}'
        log.warning(f"[WATER_FILE_VALIDATION] {message}")
        return {'valid': False, 'message': message, 'max_size_mb': max_size,
                'allowed_extensions': allowed_extensions}

    log.info(f"[WATER_FILE_VALIDATION] File validated: {filename} ({file_ext}), max size: {max_size}MB")
    return {'valid': True, 'message': 'Valid', 'max_size_mb': max_size, 'allowed_extensions': allowed_extensions}


def _build_water_file_metadata(data_dict, water_content_type, file_type, validation_result):
    """Build metadata for uploaded water-family file.

    Args:
        data_dict: Request data
        water_content_type: Type of water content
        file_type: Type of file
        validation_result: Result from validation

    Returns:
        Dict with file metadata
    """
    import mimetypes

    upload_field = data_dict.get('upload')
    filename = getattr(upload_field, 'filename', '')
    file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        if file_ext in ['jpg', 'jpeg']:
            mime_type = 'image/jpeg'
        elif file_ext == 'png':
            mime_type = 'image/png'
        elif file_ext == 'gif':
            mime_type = 'image/gif'
        elif file_ext == 'webp':
            mime_type = 'image/webp'
        elif file_ext == 'svg':
            mime_type = 'image/svg+xml'
        elif file_ext == 'pdf':
            mime_type = 'application/pdf'
        else:
            mime_type = 'application/octet-stream'

    metadata = {
        'water_content_type': water_content_type,
        'file_type': file_type,
        'asset_role': data_dict.get('asset_role', ''),
        'original_filename': filename,
        'file_extension': file_ext,
        'mime_type': mime_type,
        'max_size_mb': validation_result['max_size_mb'],
        'allowed_extensions': validation_result['allowed_extensions'],
        'uploaded_at': datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    return metadata


# ============================================================
# CRIDA Case Study Actions
# ============================================================

CRIDA_CASE_STUDY_TYPE = 'crida-case-study'


def _crida_case_study_list(context, data_dict):
    """Internal function to list CRIDA case studies.

    Only returns public, approved content. Supports filtering by country,
    theme, status, and search query.
    """
    import json as json_module
    log = logging.getLogger(__name__)

    search = {}
    search['page_type'] = CRIDA_CASE_STUDY_TYPE
    search['private'] = False
    search['submission_status'] = 'approved'

    q = data_dict.get('q')
    if q:
        search['q'] = q

    country = data_dict.get('country')
    if country:
        search['country'] = country

    order_by = data_dict.get('order_by', 'recent')
    search['order_by'] = order_by

    try:
        limit = int(data_dict.get('limit', 100))
        search['limit'] = max(1, min(limit, 500))
    except (ValueError, TypeError):
        search['limit'] = 100

    try:
        offset = int(data_dict.get('offset', 0))
        search['offset'] = max(0, offset)
    except (ValueError, TypeError):
        search['offset'] = 0

    try:
        ensure_valid_session = getattr(
            __import__('ckanext.pages.db', fromlist=['ensure_valid_session']),
            'ensure_valid_session', lambda: None
        )
        ensure_valid_session()

        out = db.Page.pages(**search)

        results = [db.table_dictize(pg, context) for pg in out]

        # Post-filter by theme and status if specified
        theme = data_dict.get('theme')
        crida_status = data_dict.get('crida_status')

        if theme or crida_status:
            filtered = []
            for r in results:
                if theme:
                    themes_raw = r.get('themes', '[]')
                    try:
                        themes_list = json_module.loads(themes_raw) if isinstance(themes_raw, str) else themes_raw
                    except Exception:
                        themes_list = []
                    if theme not in themes_list:
                        continue
                if crida_status:
                    if r.get('crida_status', '') != crida_status:
                        continue
                filtered.append(r)
            results = filtered

        return results

    except Exception as e:
        log.error("Error in crida_case_study_list: %s", str(e))
        return []


def crida_case_study_list(context, data_dict):
    """List CRIDA case studies (public API).

    Returns only public, approved content. No authentication required.

    :param q: Search query (optional)
    :param country: Filter by country (optional)
    :param theme: Filter by theme (optional)
    :param crida_status: Filter by status - Finished, Ongoing, Planned (optional)
    :param order_by: Sort order - recent, oldest (optional, default: recent)
    :param limit: Max results (optional, default: 100)
    :param offset: Pagination offset (optional, default: 0)
    """
    try:
        p.toolkit.check_access('ckanext_crida_case_study_list', context, data_dict)
    except p.toolkit.NotAuthorized:
        raise

    return _crida_case_study_list(context, data_dict)


def crida_case_study_show(context, data_dict):
    """Show a single CRIDA case study (public API).

    Only returns public, approved content. No authentication required.
    """
    log = logging.getLogger(__name__)
    try:
        p.toolkit.check_access('ckanext_crida_case_study_show', context, data_dict)
    except p.toolkit.NotAuthorized:
        raise

    page = data_dict.get('page')
    if not page:
        raise p.toolkit.ValidationError({'page': ['Missing value']})

    try:
        out = db.Page.get(name=page, page_type=CRIDA_CASE_STUDY_TYPE)
        if not out:
            raise p.toolkit.ObjectNotFound('CRIDA case study not found')

        if out.private or getattr(out, 'submission_status', None) != 'approved':
            raise p.toolkit.ObjectNotFound('CRIDA case study not found')

        return db.table_dictize(out, context)

    except p.toolkit.ObjectNotFound:
        raise
    except Exception as e:
        log.error("Error in crida_case_study_show: %s", str(e))
        raise p.toolkit.ObjectNotFound('CRIDA case study not found')


def crida_geojson(context, data_dict):
    """Generate GeoJSON FeatureCollection from approved CRIDA case studies.

    Returns a GeoJSON object compatible with Terria and standard GIS tools.

    :param country: Filter by country (optional)
    :param theme: Filter by theme (optional)
    :param crida_status: Filter by status (optional)
    """
    import json as json_module

    try:
        p.toolkit.check_access('ckanext_crida_geojson', context, data_dict)
    except p.toolkit.NotAuthorized:
        raise

    case_studies = _crida_case_study_list(context, data_dict)

    features = []
    for cs in case_studies:
        lat = cs.get('latitude')
        lon = cs.get('longitude')

        if not lat or not lon:
            continue

        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (ValueError, TypeError):
            continue

        # Parse themes
        themes_raw = cs.get('themes', '[]')
        try:
            themes_list = json_module.loads(themes_raw) if isinstance(themes_raw, str) else themes_raw
        except Exception:
            themes_list = []

        # Parse partners
        partners_raw = cs.get('partners', '[]')
        try:
            partners_list = json_module.loads(partners_raw) if isinstance(partners_raw, str) else partners_raw
        except Exception:
            partners_list = []

        feature = {
            "type": "Feature",
            "properties": {
                "country": cs.get('country', ''),
                "title": cs.get('title', ''),
                "status": cs.get('crida_status', ''),
                "themes": themes_list,
                "partners": partners_list,
                "summary": cs.get('excerpt', '') or cs.get('content', '')[:200],
                "url": '/crida/case-studies/' + cs.get('name', ''),
                "case_study_url": cs.get('case_study_url', ''),
                "image": cs.get('header_image', ''),
                "coord_note": cs.get('coord_note', ''),
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon_f, lat_f]
            }
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "name": "unesco_crida_case_studies",
        "crs": {
            "type": "name",
            "properties": {
                "name": "EPSG:4326"
            }
        },
        "features": features
    }
