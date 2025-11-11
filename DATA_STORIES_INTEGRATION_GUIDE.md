# Data Stories - Guía de Integración

## Pasos para Integrar Data Stories en ckanext-pages

### 1. Inicializar la Base de Datos

#### Opción A: Via CLI de CKAN

Agregar comando CLI a `ckanext/pages/cli.py`:

```python
import click
from ckan.model import meta

@click.group(short_help="Data Stories commands")
def data_stories():
    """Data Stories management commands."""
    pass

@data_stories.command()
def init_db():
    """Initialize Data Stories database tables."""
    from ckanext.pages.data_stories.db.migrations import upgrade

    try:
        upgrade()
        click.echo("✅ Data Stories tables created successfully")
    except Exception as e:
        click.echo(f"❌ Error creating tables: {str(e)}", err=True)
        raise

# Registrar en get_commands() de plugin.py
```

Luego ejecutar:

```bash
ckan -c ckan.ini data-stories init-db
```

#### Opción B: Durante la migración de CKAN

Agregar a setup.py entry_points:

```python
[ckan.alembic_migrations]
pages = ckanext.pages.migration:AlembicConfig
```

Crear `ckanext/pages/migration/alembic/versions/xxx_add_data_stories.py`:

```python
"""Add Data Stories tables

Revision ID: xxx
Revises: yyy
Create Date: 2025-11-10

"""
from alembic import op
import sqlalchemy as sa
from ckanext.pages.data_stories.db.migrations import upgrade, downgrade

revision = 'xxx'
down_revision = 'yyy'
branch_labels = None
depends_on = None

def upgrade():
    from ckanext.pages.data_stories.db.migrations import upgrade as ds_upgrade
    ds_upgrade()

def downgrade():
    from ckanext.pages.data_stories.db.migrations import downgrade as ds_downgrade
    ds_downgrade()
```

### 2. Registrar Actions y Auth en Plugin

Editar `ckanext/pages/plugin.py`:

```python
# Importaciones al inicio del archivo
from ckanext.pages.data_stories import actions as ds_actions
from ckanext.pages.data_stories import auth as ds_auth

class PagesPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)

    # ... métodos existentes ...

    def get_actions(self):
        """Register Data Stories actions."""
        actions = {
            # ... existing pages actions ...

            # Data Stories - Create
            'data_story_create': ds_actions.data_story_create,
            'data_story_section_create': ds_actions.data_story_section_create,

            # Data Stories - Read
            'data_story_show': ds_actions.data_story_show,
            'data_story_list': ds_actions.data_story_list,
            'data_story_section_show': ds_actions.data_story_section_show,
            'data_story_section_list': ds_actions.data_story_section_list,

            # Data Stories - Update
            'data_story_update': ds_actions.data_story_update,
            'data_story_section_update': ds_actions.data_story_section_update,
            'data_story_reorder_sections': ds_actions.data_story_reorder_sections,

            # Data Stories - Delete
            'data_story_delete': ds_actions.data_story_delete,
            'data_story_section_delete': ds_actions.data_story_section_delete,

            # Data Stories - Workflow
            'data_story_submit': ds_actions.data_story_submit,
            'data_story_review': ds_actions.data_story_review,
            'data_story_approve': ds_actions.data_story_approve,
            'data_story_request_changes': ds_actions.data_story_request_changes,

            # Data Stories - Datasets
            'data_story_link_dataset': ds_actions.data_story_link_dataset,
            'data_story_unlink_dataset': ds_actions.data_story_unlink_dataset,
            'data_story_datasets': ds_actions.data_story_datasets,

            # Data Stories - Comments
            'data_story_comment_create': ds_actions.data_story_comment_create,
            'data_story_comment_list': ds_actions.data_story_comment_list,
            'data_story_comment_update': ds_actions.data_story_comment_update,
            'data_story_comment_delete': ds_actions.data_story_comment_delete,
            'data_story_comment_resolve': ds_actions.data_story_comment_resolve,

            # Data Stories - Stats
            'data_story_record_view': ds_actions.data_story_record_view,
            'data_story_stats': ds_actions.data_story_stats,
        }
        return actions

    def get_auth_functions(self):
        """Register Data Stories auth functions."""
        auth_functions = {
            # ... existing pages auth ...

            # Data Stories auth
            'data_story_create': ds_auth.data_story_create,
            'data_story_show': ds_auth.data_story_show,
            'data_story_list': ds_auth.data_story_list,
            'data_story_update': ds_auth.data_story_update,
            'data_story_delete': ds_auth.data_story_delete,
            'data_story_section_create': ds_auth.data_story_section_create,
            'data_story_section_show': ds_auth.data_story_section_show,
            'data_story_section_list': ds_auth.data_story_section_list,
            'data_story_section_update': ds_auth.data_story_section_update,
            'data_story_section_delete': ds_auth.data_story_section_delete,
            'data_story_reorder_sections': ds_auth.data_story_reorder_sections,
            'data_story_submit': ds_auth.data_story_submit,
            'data_story_review': ds_auth.data_story_review,
            'data_story_approve': ds_auth.data_story_approve,
            'data_story_request_changes': ds_auth.data_story_request_changes,
            'data_story_link_dataset': ds_auth.data_story_link_dataset,
            'data_story_unlink_dataset': ds_auth.data_story_unlink_dataset,
            'data_story_datasets': ds_auth.data_story_datasets,
            'data_story_comment_create': ds_auth.data_story_comment_create,
            'data_story_comment_list': ds_auth.data_story_comment_list,
            'data_story_comment_update': ds_auth.data_story_comment_update,
            'data_story_comment_delete': ds_auth.data_story_comment_delete,
            'data_story_comment_resolve': ds_auth.data_story_comment_resolve,
            'data_story_stats': ds_auth.data_story_stats,
        }
        return auth_functions
```

### 3. Configuración en ckan.ini

Agregar al archivo de configuración:

```ini
# ===========================================
# Data Stories Configuration
# ===========================================

## Enable/disable data stories
ckanext.data_stories.enabled = true

## Workflow settings
# Require review before publishing
ckanext.data_stories.require_review = true

# Auto-assign reviewers based on organization
ckanext.data_stories.auto_assign_reviewers = false

## Content settings
# Maximum number of sections per story
ckanext.data_stories.max_sections = 20

# Allow external contributors (non-CKAN users)
ckanext.data_stories.allow_external_contributors = true

## Display settings
# Number of featured stories on homepage
ckanext.data_stories.featured_count = 3

# Default story visibility when created
ckanext.data_stories.default_visibility = private

## Terria Integration
ckanext.data_stories.terria_base_url = https://terria.water-data.org
ckanext.data_stories.terria_catalog_url = https://terria.water-data.org/catalog.json
ckanext.data_stories.terria_enable_embed = true

## Media settings
# Maximum image upload size (MB)
ckanext.data_stories.max_image_size = 5

# Allowed image formats
ckanext.data_stories.allowed_image_formats = png,jpg,jpeg,gif,webp

## Export settings
ckanext.data_stories.enable_pdf_export = false
ckanext.data_stories.enable_markdown_export = true

## Email notifications
ckanext.data_stories.notify_on_submit = true
ckanext.data_stories.notify_on_review = true
ckanext.data_stories.notify_on_publish = true

## Analytics
ckanext.data_stories.track_views = true
```

### 4. Probar la Integración

#### Test 1: Verificar que las tablas existen

```python
from ckan import model

# Verificar que las tablas existen
engine = model.meta.engine
assert engine.has_table('data_stories')
assert engine.has_table('data_story_sections')
assert engine.has_table('data_story_datasets')
assert engine.has_table('data_story_contributors')
assert engine.has_table('data_story_comments')
assert engine.has_table('data_story_revisions')

print("✅ All Data Stories tables exist")
```

#### Test 2: Verificar que las actions están registradas

```python
import ckan.plugins.toolkit as tk

# Verificar que las actions están disponibles
actions = [
    'data_story_create',
    'data_story_show',
    'data_story_list',
    'data_story_update',
    'data_story_delete',
]

for action_name in actions:
    try:
        action = tk.get_action(action_name)
        print(f"✅ {action_name} registered")
    except KeyError:
        print(f"❌ {action_name} NOT registered")
```

#### Test 3: Crear una historia de prueba

```python
import ckan.plugins.toolkit as tk

context = {'user': 'admin', 'ignore_auth': True}

# Crear historia
story = tk.get_action('data_story_create')(context, {
    'title': 'Test Story',
    'abstract': 'This is a test story',
})

print(f"✅ Created story: {story['id']}")
print(f"   Title: {story['title']}")
print(f"   Slug: {story['slug']}")
print(f"   Status: {story['status']}")

# Agregar sección
section = tk.get_action('data_story_section_create')(context, {
    'story_id': story['id'],
    'section_type': 'introduction',
    'title': 'Introduction',
    'content': 'This is the introduction section',
    'order_index': 0,
})

print(f"✅ Created section: {section['id']}")
print(f"   Type: {section['section_type']}")
print(f"   Title: {section['title']}")

# Listar historias
stories = tk.get_action('data_story_list')(context, {})

print(f"✅ Found {stories['count']} stories")

# Limpiar
tk.get_action('data_story_delete')(context, {
    'id': story['id'],
    'hard_delete': True,
})

print("✅ Cleaned up test data")
```

### 5. Monitoreo y Logs

Para debugging, verificar logs de CKAN:

```bash
# Ver logs en tiempo real
tail -f /var/log/ckan/ckan.log | grep DATA_STORY
```

Los logs incluyen:
- `[DATA_STORY_CREATE]` - Creación de historias
- `[DATA_STORY_UPDATE]` - Actualizaciones
- `[DATA_STORY_SECTION_CREATE]` - Creación de secciones
- `[DATA_STORY_LINK_DATASET]` - Vinculación de datasets
- Etc.

### 6. Verificar Permisos

```python
import ckan.plugins.toolkit as tk

context = {'user': 'testuser'}

# Verificar permiso para crear
can_create = tk.check_access('data_story_create', context, {})
print(f"User 'testuser' can create stories: {can_create}")

# Verificar permiso para ver historia
can_show = tk.check_access('data_story_show', context, {
    'id': 'story-id-here'
})
print(f"User 'testuser' can view story: {can_show}")
```

---

## Troubleshooting

### Error: "Table 'data_stories' doesn't exist"

**Solución**: Ejecutar las migraciones:

```bash
ckan -c ckan.ini data-stories init-db
```

### Error: "Action 'data_story_create' not found"

**Solución**: Verificar que las actions están registradas en `plugin.py` y reiniciar CKAN:

```bash
supervisorctl restart ckan-uwsgi:*
```

### Error: "Not authorized to create stories"

**Solución**: Verificar que el usuario está autenticado y tiene permisos:

```python
# Modo de prueba - ignorar auth
context = {'user': 'admin', 'ignore_auth': True}
```

### Error: "Cannot transition from 'draft' to 'published'"

**Solución**: Seguir el flujo correcto:

```python
# 1. Draft (default)
story = create_story()

# 2. Submit
submit_story(story['id'])

# 3. Review
review_story(story['id'])

# 4. Approve/Publish
approve_story(story['id'])
```

---

## Próximos Pasos Después de la Integración

1. **Crear Blueprint para Web UI**
   - Rutas: `/data-stories`, `/data-stories/new`, `/data-stories/<slug>`
   - Views para renderizar templates

2. **Crear Templates**
   - Lista de historias
   - Vista de historia individual
   - Editor de historias

3. **Agregar Helpers de Terria**
   - Parser de share links
   - Validación de configuración
   - Embed component

4. **Tests**
   - Unit tests para actions
   - Integration tests para workflow
   - API tests

5. **Documentación de Usuario**
   - Guía de creación de historias
   - Guía de revisión
   - FAQ

---

## Contacto y Soporte

Para preguntas sobre Data Stories:

- **Documentación**: Ver archivos `DATA_STORIES_*.md` en el root del proyecto
- **Issues**: Reportar en GitHub issues del proyecto
- **Email**: [Tu email de contacto]

---

**¡Data Stories está listo para ser integrado en tu CKAN!** 🚀
