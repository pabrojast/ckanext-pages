# Variables de Entorno

Tags: #operacion #referencia
Actualizado: 2026-03-26

Relacionadas: [[Setup Local]], [[Deployment]], [[Troubleshooting]]

## Hallazgo principal

No se detectó un contrato propio de variables de entorno consumidas directamente por el código de la extensión con `os.environ` o `getenv`.

La configuración real del plugin vive principalmente en settings CKAN leídos desde `tk.config`.

## Variables usadas en CI

En `.github/workflows/test.yml` se inyectan:

- `CKAN_SQLALCHEMY_URL`
- `CKAN_DATASTORE_WRITE_URL`
- `CKAN_DATASTORE_READ_URL`
- `CKAN_SOLR_URL`
- `CKAN_REDIS_URL`

Estas pertenecen al entorno CKAN de pruebas, no a la extensión en sí.

## Settings CKAN relevantes para esta extensión

### Núcleo `pages`

- `ckanext.pages.organization`
- `ckanext.pages.group`
- `ckanext.pages.about_menu`
- `ckanext.pages.group_menu`
- `ckanext.pages.organization_menu`
- `ckanext.pages.allow_html`
- `ckanext.pages.editor`
- `ckanext.pages.revisions_limit`
- `ckanext.pages.revisions_force_limit`
- `ckanext.pages.form`
- `ckanext.pages.recent_blog_cache_ttl`
- `ckanext.pages.documents_dataset_type`
- `ckanext.pages.document_dataset_type`
- `ckanext.pages.event_types`
- `ckanext.pages.terria_base_url`

### Módulos opcionales

- `ckanext.data_stories.enabled`
- `ckanext.featured_viewers.enabled`
- `ckanext.pages.data_stories.allow_direct_publish`
- `ckanext.pages.storymap_use_postmessage` — activa el cambio de escena vía postMessage (`applyScene`) en el modo `storymap` de data stories; requiere que el build de Terria desplegado incluya el bridge en `updateApplicationOnMessageFromParentWindow.js`. Default: off (se usa hash-swap).

## Settings CKAN ajenos al plugin pero consumidos como fallback

- `ckan.root_path`
- `ckan.site_title`
- `email_to`
- `ckan.version`

## Discrepancias detectadas

### Data Stories y Terria

`data_stories/README.md` menciona:

- `ckanext.data_stories.terria_base_url`

Pero el código leído usa:

- `ckanext.pages.terria_base_url`

### Review workflow

`data_stories/README.md` menciona:

- `ckanext.data_stories.require_review`

No se encontró lectura de ese flag en el código inspeccionado.

## Pendiente por confirmar

- Qué settings usa realmente la instancia productiva.
- Si existe otra capa de config externa que resuelva las discrepancias anteriores.

## Inferencia

Para esta extensión, “variables de entorno” en la práctica significa “configuración CKAN + env vars de CKAN core”, más que `.env` específicos del plugin.
