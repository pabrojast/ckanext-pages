# Datos y Persistencia

Tags: #datos #backend
Actualizado: 2026-03-26

Relacionadas: [[Arquitectura]], [[Modulos]], [[Flujos Importantes]], [[Troubleshooting]]

## Tabla base `ckanext_pages`

Definida en `ckanext/pages/db.py`.

Campos relevantes:

- `id`
- `title`
- `name`
- `content`
- `private`
- `group_id`
- `user_id`
- `publish_date`
- `page_type`
- `extras`
- `revisions`
- `submission_status`
- `ihp_organization`
- `submitted_at`
- `reviewed_at`
- `reviewed_by`
- `featured` (Boolean, default `false`) — Flag admin-only para destacar contenido en listados (en uso por `water-events`).

## Modelo de datos real del módulo base

El contenido especializado no se modela con columnas dedicadas en la tabla principal. La mayor parte vive en:

- `page_type` para diferenciar dominio
- `extras` para campos adicionales serializados como JSON texto
- `revisions` para histórico de contenido

Consecuencia práctica:

- agregar campos suele implicar tocar `logic/schema.py`, forms y lectura desde `extras`
- consultas y filtros complejos dependen de búsquedas `ilike(...)` sobre JSON serializado

## Migraciones del módulo base

Migraciones detectadas:

1. `a756dbd73ead_add_ckanext_pages_table.py`
2. `1725892d1d94_create_revisions_table.py`
3. `3a4b5c6d7e8f_add_submission_workflow_columns.py`
4. `4b5c6d7e8f9a_add_featured_column.py` — añade `featured` (Boolean, server_default `false`).

## Inicialización adicional de DB

`plugin.configure()` llama `ensure_pages_table_exists()` desde `db_init.py`.

Eso hace:

- crear la tabla si no existe
- verificar columnas faltantes
- intentar reparar problemas de tabla

## Data Stories

Tablas detectadas en `ckanext/pages/data_stories/db/models.py`:

- `data_stories`
- `data_story_sections`
- `data_story_datasets`
- `data_story_contributors`
- `data_story_comments`
- `data_story_revisions`

Estas tablas se crean mediante `init_tables(model.meta.engine)`, no por migraciones Alembic visibles en este repo.

Columna relevante agregada en 2026-06: `data_stories.display_mode` (`classic` | `storymap`, `NULL` se trata como `classic`). Se agrega de forma idempotente en `data_stories/db/migrations.py` (patrón `column_exists` + `op.add_column`).

## Featured Viewers

Tablas detectadas en `ckanext/pages/featured_viewers/db/models.py`:

- `featured_viewers` — columnas incluyen `initiative` (String(100), nullable, indexada), `organization_id` (FK a `group.id`), `countries` (JSONB, array de `{name, display_name}`)
- `viewer_datasets`
- `map_rooms` — columnas incluyen `initiative` (String(100), nullable, indexada), `organization_id` (FK a `group.id`, nullable), `countries` (JSONB, nullable)
- `map_room_viewers`

También se crean con `init_tables(model.meta.engine)`.

Las columnas nuevas se agregan mediante `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` dentro de `init_tables()` para compatibilidad con bases de datos existentes (sin Alembic).

## Event Types y Disaster Types

Los tipos se dividen en dos sistemas independientes:

### Event Types (Water Events)

Acciones: `ckanext_event_types_*`. Config: `ckanext.pages.event_types`.

- Tipos por defecto: Conference, Workshop, Seminar, Webinar, Training, etc.
- Usados por el módulo Water Events (`water-events`)

### Disaster Types (Rapid Response)

Acciones: `ckanext_disaster_types_*`. Config: `ckanext.pages.disaster_types`.

- Tipos por defecto: Tropical Cyclone, Earthquake, Tsunami, Flood, Wildfire, Volcanic Eruption, Drought, Armed Conflict, Man-made Disaster
- Usados por el módulo Rapid Response (`rapid-response`)
- Admin UI: `/admin/disaster-types`
- Helpers: `get_disaster_types()`, `get_disaster_type_by_id()`

Hallazgo importante (aplica a ambos):

- el código intenta leerlos desde su config key respectiva
- las operaciones create/update/delete tienen el guardado comentado
- no se observó persistencia real en base de datos

Esto implica que el CRUD de ambos tipos parece incompleto o dependiente de una capa externa no presente en el repo.

## Water Publications y datasets CKAN

Al crear una `water-publication`, `utils.py` puede generar un dataset CKAN tipo documento si el formulario trae metadatos o archivo.

Configuración relevante:

- `ckanext.pages.documents_dataset_type`
- fallback alternativo: `ckanext.pages.document_dataset_type`

## Historial de revisiones

El contenido base mantiene snapshots en `revisions`:

- el estado actual se marca con `current`
- el límite depende de `ckanext.pages.revisions_limit`
- puede forzarse con `ckanext.pages.revisions_force_limit`

## Pendiente por confirmar

- Estrategia de migración formal para `data_stories` y `featured_viewers`.
- Si en producción existe una persistencia externa para `event_types` y `disaster_types`.

## Inferencia

El módulo base prioriza flexibilidad y compatibilidad sobre normalización. Los módulos opcionales más nuevos se ven más modelados y explícitos.
