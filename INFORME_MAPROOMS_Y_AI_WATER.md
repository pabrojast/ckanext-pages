# Informe MapRooms y AI Water

Fecha: 2026-03-27

## Objetivo

Este documento resume como estan implementados `MapRooms` y `AI Water Tools` dentro de `ckanext-pages`, con foco en arquitectura, persistencia, rutas, permisos, frontend, workflow editorial y hallazgos tecnicos observables en el codigo.

La documentacion principal del repo sigue viviendo en `docs/obsidian-vault/`. Este informe funciona como documento de trabajo puntual en el root y se apoya en esa vault y en la implementacion actual.

## Resumen Ejecutivo

`MapRooms` y `AI Water Tools` no siguen la misma arquitectura.

- `MapRooms` pertenece al modulo opcional `featured_viewers`.
- `MapRooms` usa tablas propias, acciones propias, auth propio y blueprint propio bajo `/featured-viewers`.
- `MapRooms` no es un subtipo de `Page`; es un agregado que agrupa varios `FeaturedViewer`.
- `AI Water Tools` si es un subtipo del CMS base.
- `AI Water Tools` se implementa como `page_type='ai-water-tools'` dentro de la tabla compartida `ckanext_pages`.
- `AI Water Tools` reutiliza el flujo generico de `pages`, con schema NAVL extendido, `extras` JSON, templates dedicados y dashboard admin propio.

## 1. Implementacion de MapRooms

### 1.1 Ubicacion y activacion

- El modulo vive en `ckanext/pages/featured_viewers/`.
- Se activa por configuracion con `ckanext.featured_viewers.enabled`.
- Cuando esta activo, `PagesPlugin` registra el blueprint Flask de `featured_viewers`, las acciones CKAN `featured_viewer_*` y `map_room_*`, las auth functions del modulo, los helpers de frontend y la inicializacion de tablas con `init_featured_viewers_tables(...)`.

Archivos clave:

- `ckanext/pages/plugin.py`
- `ckanext/pages/featured_viewers/blueprint/routes.py`
- `ckanext/pages/featured_viewers/actions/`
- `ckanext/pages/featured_viewers/auth/permissions.py`
- `ckanext/pages/featured_viewers/db/models.py`
- `ckanext/pages/featured_viewers/db/utils.py`

### 1.2 Modelo de datos

`MapRooms` usa persistencia separada del CMS base.

Tablas involucradas:

- `featured_viewers`
- `map_rooms`
- `map_room_viewers`

Relaciones:

- `MapRoom` representa una coleccion tematica.
- `MapRoomViewer` es una tabla de union entre una sala y varios `FeaturedViewer`.
- Un `MapRoom` no guarda configuracion Terria propia.
- La integracion Terria esta en cada `FeaturedViewer`, via `terria_share_link`, `terria_config` y `map_layers`.

Campos principales de `map_rooms`:

- `id`
- `title`
- `slug`
- `description`
- `thumbnail_url`
- `category`
- `initiative`
- `status`
- `is_featured`
- `order_index`
- `author_id`
- `created_at`
- `updated_at`

Campos principales de `map_room_viewers`:

- `id`
- `room_id`
- `viewer_id`
- `order_index`
- `created_at`

### 1.3 Schema y validacion

La validacion de `MapRoom` es acotada y vive en `ckanext/pages/featured_viewers/logic/schema.py`.

Campos validados:

- `title`
- `slug`
- `description`
- `thumbnail_url`
- `category`
- `initiative`

Tambien se reutiliza la generacion y validacion de slugs:

- `generate_slug(title)`
- `validate_slug(slug)`

### 1.4 Rutas web

Todas las rutas van bajo el prefijo `/featured-viewers`.

Rutas de `MapRooms`:

- `/featured-viewers/rooms/`
- `/featured-viewers/rooms/new`
- `/featured-viewers/rooms/<slug>`
- `/featured-viewers/rooms/<slug>/edit`
- `/featured-viewers/rooms/<slug>/delete`
- `/featured-viewers/rooms/<slug>/add-viewer`
- `/featured-viewers/rooms/<slug>/remove-viewer`

Comportamiento principal:

- `rooms_index()` lista salas publicadas.
- `rooms_create()` crea la sala y luego sincroniza viewers seleccionados.
- `rooms_show()` muestra la sala con sus viewers.
- `rooms_edit()` actualiza la sala y vuelve a sincronizar la composicion.
- `rooms_delete()` elimina la sala.

### 1.5 Acciones CKAN

Las acciones dedicadas son:

- `map_room_create`
- `map_room_show`
- `map_room_list`
- `map_room_update`
- `map_room_delete`
- `map_room_add_viewer`
- `map_room_remove_viewer`
- `sync_room_viewers`

Puntos importantes del flujo:

- `map_room_create` crea la entidad base.
- `sync_room_viewers` agrega y quita enlaces en `map_room_viewers` para reflejar la seleccion final.
- `map_room_show` devuelve la sala y agrega la lista de viewers asociados.
- `map_room_list` soporta `status`, `category`, `initiative`, `limit` y `offset`.

### 1.6 Permisos

La auth de `MapRooms` esta en `ckanext/pages/featured_viewers/auth/permissions.py`.

Reglas observadas:

- crear: sysadmin o admin de alguna organizacion
- editar: mismas reglas que crear
- borrar: solo sysadmin
- ver y listar: permitido, pero las salas no publicadas quedan protegidas por chequeos adicionales en la ruta `rooms_show`

Observacion:

- La funcion `map_room_show` de auth devuelve acceso abierto.
- La proteccion de drafts/no publicados se completa en la ruta Flask, que obliga permiso de update cuando `status != 'published'`.

### 1.7 Frontend

Templates principales:

- `ckanext/pages/theme/templates_main/featured_viewers/rooms/list.html`
- `ckanext/pages/theme/templates_main/featured_viewers/rooms/edit.html`
- `ckanext/pages/theme/templates_main/featured_viewers/rooms/show.html`

Caracteristicas visibles:

- listado en cards
- portada con imagen o placeholder
- categoria y destacado visual
- formulario de edicion con datos base, categoria, iniciativa, imagen de portada, estado, prioridad y asociacion de viewers publicados
- pagina de detalle que renderiza la descripcion y luego los viewers asociados

### 1.8 Relacion con Featured Viewers y Terria

Arquitectonicamente, `MapRooms` es un contenedor de viewers, no un viewer especial.

- La experiencia cartografica real vive en `FeaturedViewer`.
- Cada viewer puede embeber Terria desde `terria_share_link`.
- La sala solo agrupa y presenta viewers ya existentes.
- Por eso `MapRooms` depende del modulo `featured_viewers`, no del CMS base `pages`.

### 1.9 Hallazgos tecnicos observados en MapRooms

- El listado `rooms_index()` lee `q` desde query string y lo pasa a `map_room_list`.
- `map_room_list` no usa `q`, por lo que la busqueda de texto en salas no parece implementada de extremo a extremo.
- No se encontro una suite de tests dedicada a `featured_viewers` o `map_rooms` en el repo.

## 2. Implementacion de AI Water Tools

### 2.1 Ubicacion y arquitectura

`AI Water Tools` no es un modulo independiente con tablas propias. Es una especializacion del CMS base.

Se implementa como:

- `page_type='ai-water-tools'`
- tabla base `ckanext_pages`
- campos estructurados en `extras`
- workflow editorial sobre columnas compartidas como `submission_status`, `ihp_organization`, `submitted_at`, `reviewed_at`, `reviewed_by`

Archivos clave:

- `ckanext/pages/blueprint.py`
- `ckanext/pages/utils.py`
- `ckanext/pages/actions.py`
- `ckanext/pages/auth.py`
- `ckanext/pages/db.py`
- `ckanext/pages/logic/schema.py`
- `ckanext/pages/theme/templates_main/ckanext_pages/ai-water-tools*.html`
- `ckanext/pages/public/js/ai-water-tools.js`
- `ckanext/pages/public/css/ai-water-tools.css`

### 2.2 Rutas web

Rutas principales:

- `/ai-water-tools`
- `/ai-water-tools/<page>`
- `/ai-water-tools/<page>/revisions`
- `/ai-water-tools/<page>/revisions/<revision>`
- `/ai-water-tools/<page>/revisions/<revision>/restore`
- `/ai-water-tools_edit`
- `/ai-water-tools_edit/<page>`
- `/ai-water-tools_delete/<page>`

Rutas admin:

- `/ai-water-admin`
- `/ai-water-admin/approve/<page>`
- `/ai-water-admin/reject/<page>`
- `/ai-water-admin/change-org/<page>`

Las vistas de estas rutas no implementan un CRUD aislado; delegan al flujo generico de `pages`:

- `pages_list_pages('ai-water-tools')`
- `pages_show(..., page_type='ai-water-tools')`
- `pages_edit(..., 'ai-water-tools')`
- `pages_delete(..., page_type='ai-water-tools')`

### 2.3 Modelo de datos y persistencia

`AI Water Tools` comparte la tabla `ckanext_pages` con otros verticales.

Campos de columna usados directamente:

- `title`
- `name`
- `content`
- `private`
- `page_type`
- `publish_date`
- `submission_status`
- `ihp_organization`
- `submitted_at`
- `reviewed_at`
- `reviewed_by`

Campos especificos guardados en `extras`:

- `ai_technique`
- `water_application`
- `maturity_level`
- `scalability`
- `ai_model_type`
- `training_data_type`
- `output_type`
- `accuracy_metrics`
- `data_requirements`
- `reference_publications`
- `developer_organization`
- `water_application_category`
- `technology_readiness_level`
- `ethical_compliance`
- `data_sources`
- `spatial_scale`
- `temporal_scale`
- `open_science_compliance`
- `reference_doi`
- `limitations`

Tambien reutiliza campos que ya existian para Open Source / catalogos:

- `repository_url`
- `website_url`
- `documentation_url`
- `software_license`
- `development_status`
- `platform`
- `programming_language`
- `version`
- `release_date`
- `header_display_mode`
- `logo_image`
- `uploaded_images`

### 2.4 Validacion y serializacion

La validacion vive en `ckanext/pages/logic/schema.py` dentro del schema general de pages.

Comportamiento observado:

- los campos base van a columnas directas
- los campos adicionales se serializan dentro de `extras`
- si un valor de `extras` llega como JSON string y representa lista o dict, `pages_update` lo deserializa antes de volver a guardar
- cada actualizacion registra revision en `revisions`

Esto significa que `AI Water Tools` no tiene un modelo SQLAlchemy dedicado; depende de la combinacion `Page` + `page_type` + `extras`.

### 2.5 Workflow editorial

El flujo real pasa por `utils.pages_edit()` y `actions._pages_update()`.

Reglas observadas:

- usuario no admin no puede publicar directo
- si intenta publicar, el backend degrada la accion a `submit`
- `draft` deja el contenido privado
- `submit` deja el contenido privado y lo marca como `pending`
- `publish` lo marca `approved`, lo hace publico y completa metadatos de revision
- al crear contenido nuevo de `ai-water-tools`, un usuario no sysadmin parte como `private=True`

Dashboard admin:

- `ai_water_admin_dashboard()` lista pendientes
- `ai_water_admin_approve()` aprueba y publica
- `ai_water_admin_reject()` rechaza
- `ai_water_admin_change_org()` cambia la organizacion asignada

### 2.6 Organizacion y permisos

La auth principal esta en `ckanext/pages/auth.py`.

Reglas observadas para actualizacion:

- sysadmin puede operar
- autor original puede editar
- si el contenido pertenece a `water-news`, `water-events`, `water-publications`, `open-source-software` o `ai-water-tools`, tambien puede editar un miembro activo de la organizacion `ihp_organization`

Ademas, durante `pages_edit()` y `pages_update()`:

- `organization_id` del form se mapea a `ihp_organization`
- si no se envia organizacion y el usuario tiene organizaciones, el sistema intenta asignar una por defecto
- para usuarios no admin, si la organizacion enviada no pertenece a sus memberships, se reemplaza por una valida del usuario

### 2.7 Listado, filtros y helpers

`AI Water Tools` reutiliza `ckanext_pages_list` y la query `Page.pages(...)`.

Filtros especificos implementados en `db.Page.pages(...)`:

- `ai_technique`
- `water_application`
- `maturity_level`
- `scalability`
- `ai_model_type`
- `development_status`
- `water_application_category`
- `technology_readiness_level`
- `spatial_scale`
- `temporal_scale`

Helpers relevantes en `plugin.py`:

- `get_recent_ai_water_tools`
- `get_ai_technique_class`
- `count_ai_tools_by_technique`
- `count_ai_tools_by_application`

Comportamiento relevante:

- `get_recent_ai_water_tools` solo devuelve entradas `approved` y `private=False`
- la vista de listado usa conteos de resumen y filtros visuales

### 2.8 Frontend

Templates principales:

- `ckanext/pages/theme/templates_main/ckanext_pages/ai-water-tools_list.html`
- `ckanext/pages/theme/templates_main/ckanext_pages/ai-water-tools.html`
- `ckanext/pages/theme/templates_main/ckanext_pages/ai-water-tools_edit.html`
- `ckanext/pages/theme/templates_main/ckanext_pages/ai-water-admin-dashboard.html`

Assets:

- `ckanext/pages/public/js/ai-water-tools.js`
- `ckanext/pages/public/css/ai-water-tools.css`

Capacidades visibles en frontend:

- listado con filtros unificados y resumen estadistico
- ficha detalle con secciones extensas para overview, tecnica, framework UNESCO, enlaces, publicaciones y herramientas relacionadas
- formulario de edicion grande, con checkboxes sincronizados a hidden inputs, manejo de galeria, logo, organizacion, member states y acciones de workflow
- dashboard admin con cambio de organizacion y acciones de approve/reject

### 2.9 Seed e importacion

Existe un pipeline de carga inicial via CLI:

- comando: `pages import-ai-tools`
- implementacion: `ckanext/pages/commands/import_ai_tools.py`
- fuente: `ckanext/pages/data/ai_water_tools_seed.json`

Comportamiento observado:

- lee un JSON local con entradas ya armadas
- crea o actualiza paginas usando `ckanext_pages_update`
- fuerza `publish_date='2025-01-01'`
- fuerza `submission_action='publish'`
- soporta `--dry-run`
- soporta `--update-existing`

### 2.10 Hallazgos tecnicos observados en AI Water Tools

- La implementacion backend espera el campo `water_application`.
- El template de edicion usa `water_application_domain` y `water_application_domain_cb` en varias partes del formulario y del JS inline.
- La vista detalle y los filtros del listado leen `water_application`, no `water_application_domain`.
- Eso sugiere una inconsistencia real entre frontend de edicion y backend de persistencia/filtro.
- `AI Water Tools` tiene rutas web y dashboard admin, pero no aparece como parte de la API publica `ckanext_water_family_*`.

## 3. Diferencias Arquitectonicas Clave

`MapRooms`:

- modulo opcional
- blueprint separado
- tablas propias
- acciones propias
- auth propia
- agrupa `FeaturedViewer`
- Terria vive en el viewer, no en la sala

`AI Water Tools`:

- vertical sobre el CMS base
- usa `page_type`
- comparte tabla `ckanext_pages`
- guarda variabilidad en `extras`
- reutiliza actions/auth/utils genericos
- agrega templates, filtros, schema y dashboard admin especificos

## 4. Conclusiones Practicas

Si hay que tocar `MapRooms`, el punto de entrada correcto suele ser `featured_viewers`:

- modelos
- acciones
- auth
- rutas `/featured-viewers/rooms/*`
- templates `featured_viewers/rooms/*`

Si hay que tocar `AI Water Tools`, el punto de entrada correcto suele estar repartido entre:

- `blueprint.py` para rutas
- `utils.py` para flujo web y dashboard admin
- `actions.py` para persistencia y workflow
- `db.py` para filtros
- `logic/schema.py` para validacion
- templates y assets dedicados

En otras palabras:

- `MapRooms` es un subproducto del modulo `featured_viewers`
- `AI Water Tools` es un vertical del CMS base `pages`

## 5. Fuentes Revisadas

- `docs/obsidian-vault/Index.md`
- `docs/obsidian-vault/Arquitectura.md`
- `docs/obsidian-vault/Modulos.md`
- `docs/obsidian-vault/Rutas y Entrypoints.md`
- `docs/obsidian-vault/Flujos Importantes.md`
- `docs/obsidian-vault/Frontend y Plantillas.md`
- `docs/obsidian-vault/Testing.md`
- `ckanext/pages/plugin.py`
- `ckanext/pages/blueprint.py`
- `ckanext/pages/utils.py`
- `ckanext/pages/actions.py`
- `ckanext/pages/auth.py`
- `ckanext/pages/db.py`
- `ckanext/pages/logic/schema.py`
- `ckanext/pages/commands/import_ai_tools.py`
- `ckanext/pages/data/ai_water_tools_seed.json`
- `ckanext/pages/featured_viewers/blueprint/routes.py`
- `ckanext/pages/featured_viewers/actions/create.py`
- `ckanext/pages/featured_viewers/actions/read.py`
- `ckanext/pages/featured_viewers/actions/update.py`
- `ckanext/pages/featured_viewers/actions/delete.py`
- `ckanext/pages/featured_viewers/auth/permissions.py`
- `ckanext/pages/featured_viewers/db/models.py`
- `ckanext/pages/featured_viewers/db/utils.py`
- `ckanext/pages/theme/templates_main/featured_viewers/rooms/list.html`
- `ckanext/pages/theme/templates_main/featured_viewers/rooms/edit.html`
- `ckanext/pages/theme/templates_main/featured_viewers/rooms/show.html`
- `ckanext/pages/theme/templates_main/ckanext_pages/ai-water-tools_list.html`
- `ckanext/pages/theme/templates_main/ckanext_pages/ai-water-tools.html`
- `ckanext/pages/theme/templates_main/ckanext_pages/ai-water-tools_edit.html`
- `ckanext/pages/theme/templates_main/ckanext_pages/ai-water-admin-dashboard.html`
- `ckanext/pages/public/js/ai-water-tools.js`
- `ckanext/pages/public/css/ai-water-tools.css`
