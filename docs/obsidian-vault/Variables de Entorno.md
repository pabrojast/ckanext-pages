# Variables de Entorno

Tags: #operacion #referencia
Actualizado: 2026-10-26

Relacionadas: [[Setup Local]], [[Deployment]], [[Troubleshooting]]

## Hallazgo principal

Las suites PostgreSQL independientes leen `PAGES_IMPORT_TEST_URL` y `PAGES_SCHEMA_TEST_URL`. Deben apuntar a una base aislada de pruebas; crean y eliminan esquemas o tablas temporales. CI usa la base `ckan_test` y el rol `ckan_default`, sin requerir acceso de superusuario.

La configuración real del plugin vive principalmente en settings CKAN leídos desde `tk.config`.

## Variables usadas en CI

En `.github/workflows/test.yml` se inyectan:

- `CKAN_SITE_URL` (`http://test.ckan.net`; evita el puerto localhost heredado de la imagen, rechazado por el validador URL de CKAN 2.9)
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
Nota: el modo `storymap` de data stories no requiere configuración adicional — el uso de postMessage vs hash-swap se autodetecta según si el build de Terria postea `"ready"` al padre (bridge en `updateApplicationOnMessageFromParentWindow.js`). El setting `ckanext.pages.storymap_use_postmessage` existió brevemente durante el desarrollo y fue eliminado antes de desplegarse.

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

## Geocodificación de Data Stories

`ckanext.data_stories.geocoder_url`: URL del servicio Nominatim; default `https://nominatim.openstreetmap.org/search`. Solo se configura en servidor, nunca desde parámetros del visitante. Usa la conexión Redis de CKAN para caché de 24 horas y un cupo global de una consulta cada 1,1 segundos. Sin Redis responde 503; cupo agotado: 429 con Retry-After; error upstream: 502.

Configurar el proveedor Terria con URL `/data-stories/api/location-search`, búsqueda explícita (Enter/botón) y atribución OpenStreetMap. No habilitar autocompletado contra el servicio público. Ver https://operations.osmfoundation.org/policies/nominatim/.

`ckanext.data_stories.terria_runtime_url`: override opcional del visor embebido (por ejemplo, el Terria de dev); los enlaces y la resolución de shares siguen usando sus instancias originales. Sin override conserva la selección histórica por primer share.

## Personalización del portal (2026-10-26)

La integración de `node` incorpora estos settings de servidor:

| Setting | Comportamiento |
| --- | --- |
| `ckanext.pages.water_family.enabled` | `true` por defecto. Con `false` no se registran las rutas especializadas de Water Family, Rapid Response, Open Source, AI, CRIDA ni administración de tipos. Conserva páginas/blog y los módulos opcionales. |
| `ckanext.data_stories.hero_image` | Imagen de cabecera de Data Stories. Sin valor usa `/Landing_page/Content/IHPTITLE02DATASTORIES.jpg`. |
| `ckanext.featured_viewers.hero_image` | Imagen de cabecera de Featured Viewers. Sin valor usa `/Landing_page/Content/IHPTITLE04VIEWERS.jpg`. |
| `ckanext.featured_viewers.extra_terria_hosts` | Hosts adicionales, separados por espacios, permitidos para resolver/guardar shares; se añaden al host Terria configurado y al de `ckan.site_url`. |

`ckanext.pages.terria_base_url` conserva prioridad. Sin valor, Data Stories y el guardado de Featured Viewers usan `/terria` del propio `ckan.site_url`, en lugar de un host externo fijo. Los antiguos hosts de desarrollo ya no están autorizados implícitamente por Featured Viewers: si se necesitan, deben declararse en la configuración. El cambio de rutas se evalúa al importar el blueprint y requiere reiniciar el proceso. Este interruptor controla rutas; no elimina registros ni desactiva las acciones CKAN del dominio. Ver [[Rutas y Entrypoints]], [[Frontend y Plantillas]] y [[Deployment]].
