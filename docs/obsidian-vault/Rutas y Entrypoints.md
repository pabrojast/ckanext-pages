# Rutas y Entrypoints

Tags: #arquitectura #backend
Actualizado: 2026-03-26

Relacionadas: [[Arquitectura]], [[Modulos]], [[Comandos Utiles]]

## Entry points de Python package

Según `setup.py`, el paquete expone:

- plugin CKAN `pages=ckanext.pages.plugin:PagesPlugin`
- resource view `textboxview=ckanext.pages.plugin:TextBoxView`

## Interfaces CKAN implementadas por `PagesPlugin`

- `IConfigurer`
- `ITemplateHelpers`
- `IActions`
- `IAuthFunctions`
- `IConfigurable`
- `IBlueprint`
- `IClick`
- `ITranslation`

## Blueprint base del módulo `pages`

Registrado desde `ckanext/pages/blueprint.py`.

### Rutas principales

- `/pages`
- `/pages/<page>`
- `/blog`
- `/blog/<page>`
- `/rapid-response`
- `/rapid-response/<page>`

### Water Family

- `/water-family`
- `/water-news`
- `/water-events`
- `/water-events/calendar` — vista calendario (FullCalendar vía CDN, lee `publish_date`/`event_end_date`).
- `/water-events/<page>/feature` (POST, sysadmin) — toggle del flag `featured` para destacar un evento en el listado.
- `/water-publications`
- `/water-admin`

### Open Source / AI

- `/open-source-tools`
- `/open-source-admin`
- `/ai-water-tools`
- `/ai-water-admin`

### Administración adicional

- `/admin/event-types` — CRUD de tipos de evento para Water Events
- `/admin/disaster-types` — CRUD de tipos de desastre para Rapid Response
- `/crida`
- `/crida/case-studies`
- `/crida/admin`
- `/crida/api/case-studies`
- `/crida/api/geojson`

### Uploads

- `/pages_upload`
- `/water_family_upload`

## Blueprints opcionales

### `data_stories`

Prefijo: `/data-stories`

Rutas detectadas:

- `/`
- `/list`
- `/pending-review`
- `/my-stories`
- `/new`
- `/import`
- `/<slug>`
- `/<slug>/edit`
- `/<slug>/delete`
- `/<slug>/submit`
- `/<slug>/publish`
- `/<slug>/review`
- `/<slug>/sections/create`
- `/<slug>/comments`
- `/<slug>/export`

### `featured_viewers`

Prefijo: `/featured-viewers`

Rutas detectadas:

- `/` — landing unificada: carga rooms (máx 6) + viewers paginados, initiative pills (JS), buscador que filtra ambos. Acepta filtros `category`, `initiative`, `q`, `sort`
- `/list`
- `/new`
- `/<slug>`
- `/<slug>/edit`
- `/<slug>/delete`
- `/<slug>/submit`
- `/<slug>/publish`
- `/<slug>/review`
- `/pending-review`
- `/rooms/` — listado de map rooms, acepta filtros `initiative`, `q`
- `/rooms/new` — creación de room con selección de viewers (checkboxes)
- `/rooms/<slug>`
- `/rooms/<slug>/edit` — edición de room con selección de viewers (checkboxes)
- `/rooms/<slug>/delete`
- `/rooms/<slug>/add-viewer` — API legacy, mantiene compatibilidad
- `/rooms/<slug>/remove-viewer` — API legacy, mantiene compatibilidad
- `/api/resolve-share-link`
- `/api/save-to-terria`
- `/api/search-terria-datasets`

Acciones CKAN relevantes:

- `sync_room_viewers` — sincroniza viewers de un room en una sola operación (agrega nuevos, elimina quitados)

## Acciones CKAN relevantes

### Base

- `ckanext_pages_show`
- `ckanext_pages_update`
- `ckanext_pages_delete`
- `ckanext_pages_list`
- `ckanext_pages_upload`

### APIs y verticales

- `ckanext_water_family_list`
- `ckanext_water_family_show`
- `ckanext_event_types_*`
- `ckanext_disaster_types_*`
- `ckanext_crida_case_study_*`
- `ckanext_crida_geojson`

### Opcionales

- `data_story_*`
- `featured_viewer_*`
- `map_room_*`

## CLI

`PagesPlugin` también registra un grupo click `pages` que agrega:

- `fix-datasets`
- `import-ai-tools`
- `seed-crida`

## Pendiente por confirmar

- Si existen rutas legacy todavía usadas por otras extensiones o templates externos.
- Si algún controlador Pylons legado sigue siendo necesario; se observan referencias antiguas en algunos templates.

## Inferencia

La superficie HTTP del plugin ya no es la de un CMS simple; es una mini plataforma de contenidos y visualización montada sobre CKAN.
