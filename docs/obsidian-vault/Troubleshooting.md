# Troubleshooting

Tags: #operacion #onboarding
Actualizado: 2026-09-24

Relacionadas: [[Setup Local]], [[Deployment]], [[Testing]], [[Datos y Persistencia]]

## La ruta existe pero devuelve 401 o 403

Revisar:

- que el usuario tenga sesión iniciada
- que el permiso correcto exista para ese `page_type`
- si el contenido está privado o pendiente
- si el módulo opcional está habilitado por config

## El plugin carga pero faltan tablas

Pasos:

1. ejecutar `ckan -c test.ini db upgrade -p pages`
2. revisar logs del arranque del plugin
3. confirmar que `plugin.configure()` no está fallando

El código también intenta auto-crear o reparar `ckanext_pages`, pero no conviene depender solo de eso.

## `data_stories` o `featured_viewers` no aparecen

Revisar flags:

- `ckanext.data_stories.enabled = true`
- `ckanext.featured_viewers.enabled = true`

Sin esos flags, los blueprints opcionales no se registran.

## Los event types no persisten

Hallazgo del código:

- el CRUD de event types lee de `ckanext.pages.event_types`
- pero create/update/delete tienen el guardado comentado

Si cambias event types y desaparecen, esa es la primera sospecha.

## Un contenido enviado por autor no se vuelve público

Revisar:

- `submission_status`
- `private`
- `reviewed_by`
- `reviewed_at`

El contenido público esperado suele requerir:

- `submission_status = approved`
- `private = false`

## Water Publication no crea dataset

Revisar:

- si el formulario envió archivo, link o metadata suficiente
- `ckanext.pages.documents_dataset_type`
- permisos del usuario para crear datasets
- logs de `utils._maybe_create_documents_dataset()`

Hallazgo productivo confirmado:

- si el traceback cae en `ckan.logic.action.create.package_create()` y luego en `package_show()` con `NotFound`, revisar plugins encadenados sobre `package_show` como `ckanext-terria-view`
- el fix en este repo fuerza `context['return_id_only']=True` para `package_create` y hace el `package_show(ignore_auth=True)` después, evitando que el flujo de Water Publications dependa del `package_show` interno de CKAN
- si el traceback cae en `resource_create()` -> `package_show()` con `ckan.logic.NotFound` justo después de logs de `ckanext-schemingdcat` / `_autofill_author_from_org`, revisar si un `package_patch` en `after_dataset_create` hizo rollback del package. El flujo actual evita ese caso creando primero sin `owner_org` y asignando la organización con `package_owner_org_update` después del commit.
- si aparece `psycopg2.errors.NotNullViolation: null value in column "featured"`, revisar payloads de re-guardado que traigan `featured=None`; `_pages_update()` debe preservar el valor existente o caer a `False`.

## Problemas de DB intermitentes

El repo incluye utilidades para:

- retry de operaciones
- rollback seguro
- recreación de sesión
- chequeo/reparación de tabla

Archivos relevantes:

- `db_utils.py`
- `db_init.py`

## Upload falla

Revisar:

- tamaño del archivo
- extensión permitida
- tipo de upload
- permisos del usuario

Para Water Family, además revisar:

- `water_content_type`
- `file_type`

## CI falla por `test.ini`

La workflow modifica el path de `test-core.ini` dentro del contenedor. Si replicas CI fuera de ese entorno, revisa el valor de:

- `use = config:...`

## Discrepancias de configuración Terria

Se observó una discrepancia:

- README de `data_stories` menciona `ckanext.data_stories.terria_base_url`
- el código usa `ckanext.pages.terria_base_url`

Si Terria no resuelve URLs, revisar primero ese punto.

## Bloques o mapas de Rapid Response no se pueden editar tras guardar

Síntoma: al reabrir la edición de una página `rapid-response`, las secciones de bloques aparecen colapsadas en un solo bloque de texto, los bloques "Maps & Media" desaparecen como bloques editables, y un segundo guardado destruye la estructura (y puede vaciar timeline y galería).

Causa: desde `a954592`, `actions.py` guarda extras JSON-parseables como listas/dicts nativos. El form de edición renderizaba esas listas crudas (repr de Python, no JSON) y el JS fallaba en `JSON.parse`, cayendo a un fallback destructivo.

Fix: `utils.pages_edit` re-serializa los campos de `RAPID_RESPONSE_JSON_FORM_FIELDS` a strings JSON antes de renderizar (ver `utils._serialize_json_fields_for_form`).

Para reparar páginas ya dañadas (metadata colapsada con iframes dentro de un único bloque de texto):

```
ckan -c <ini> pages fix-rapid-response-blocks           # dry-run
ckan -c <ini> pages fix-rapid-response-blocks --apply
```

Timeline/galería/países ya vaciados a `[]` no son recuperables (revisions solo guarda `content`); el comando los reporta.

## Mapa de Data Story (classic) a 100% no llena la pantalla / no entra en fullscreen

Síntoma: el campo Width del bloque Terria/Media está en `100%` pero el mapa queda estrecho (columna + sidebar) y el fullscreen de Terria no abre a ventana completa.

Causa: `100%` era el 100% de `.col-md-9` dentro de `.container`, y los iframes horneados no traían `allow="fullscreen"` (solo el atributo viejo `allowfullscreen`).

Fix (sep-2026): las secciones classic van a full-bleed; `100%`/`100vw` usan el viewport; hay un botón Full Screen en `.ds-map-shell`. Si un mapa viejo sigue sin fullscreen, recargar con cache-bust (`terria-tabs-display.js?v=`) o re-guardar la story. El botón del shell no depende del botón interno de Terria.

## Data story no publicada devolvía 500 a anónimos (corregido sep-2026)

Síntoma: `/data-stories/<slug>` de una story no publicada devolvía Error 500 a visitantes anónimos (en vez de 403). Causa: `tk.abort(403)` lanza una `HTTPException` de werkzeug que el `except Exception` genérico de `show()` tragaba y re-lanzaba como 500. Fix: el access-check vive fuera del try de fetch y el handler re-lanza `HTTPException`. Si reaparece un 500 "Error loading story", revisar que ningún `except Exception` nuevo envuelva un `tk.abort`.

## Storymap sin Story Slides (steps) en un capítulo

Buscar en logs `[STORYMAP] Steps unavailable for share <id>`: significa que la resolución del share JSON falló (timeout 5s, red, 404). Los fallos NO se cachean — el siguiente render reintenta solo. Verificar a mano: `curl <terria>/api/v1/share/<id>` y el proxy `/data-stories/api/terria-scene/<id>`. Desde sep-2026 los steps se resuelven para TODAS las fuentes del capítulo, no solo la primera.

## Desaparecieron los datasets de una story al guardar

Desde sep-2026 no debería pasar: un `datasets_data` ausente o corrupto conserva los vínculos existentes (sentinel `_KEEP_DATASETS` en `routes.py`); solo `''`/`'null'`/`'[]'` explícitos los vacían, y los datasets se sincronizan antes que las secciones. Si se reporta pérdida, buscar en logs `[EXTRACT_FORM] Unparseable datasets_data`.

## Code smell útil de recordar

`utils.py` contiene dos definiciones de `crida_admin_reseed()`. Si haces cambios allí, revisa cuál definición termina vigente.

## Pendiente por confirmar

- logs y observabilidad productiva
- almacenamiento real de uploads
- mecanismos de rollback productivo

## Slides organizadas y mapas lentos

Si una fuente ya organizada cambia, usar Update slides from Terria y guardar. Una advertencia de slide sin correspondencia conserva la copia anterior para revisión. Un fallo del mapa permite Retry; una recepción confirmada no debe activar el fallback de hash a los 2,5 segundos. El límite de aplicación es 90 segundos; una solicitud anterior no confirma una escena posterior.

Si buscar un lugar solo ofrece el catálogo, comprobar `parameters.searchProviders` en la configuración pública y en `terria-terriamap-config-client`; cambiar solo el archivo local no cambia el despliegue activo.

Si desaparecen bloques al guardar contenido que contiene `&quot;`, revisar la versión de `_parse_json_field`: debe leer JSON antes de decodificar entidades HTML. Los metadatos no vacíos e inválidos deben rechazar el formulario antes de modificar registros; reconstruirlos desde HTML perdería snapshots y orden.

## Rapid Response tarda y muestra fases sin formato

Diagnóstico observado en producción el 2026-09-11: Nepal devolvía 52,87 MB de HTML por dos JPEG incrustados; los estilos del detalle aparecían después de las imágenes. El navegador podía quedar sin completar `DOMContentLoaded`. El historial también almacenaba base64.

Revisar tamaño del HTML, posición del CSS y ejecutar la auditoría `pages optimize-rapid-response-images`. La corrección combina CSS en cabecera, subida de imágenes desde el editor y conversión reversible del contenido existente; no basta con añadir `loading="lazy"` a una imagen que sigue incrustada en el HTML. Ver [[Deployment]].

## Story Map no cambia de escena en 1366×768

Los porcentajes de `rootMargin` en IntersectionObserver se calculan sobre el ancho: márgenes de 45% y 35% pueden eliminar toda la zona activa en una pantalla baja. El visor usa ahora una posición de lectura en píxeles de altura y una única selección de paso. Verificar avanzar, volver y saltar entre fuentes; no limitarse a probar Slides.

Si una historia importada abre Terria de otra instancia y cae al modo hash, revisar `ckanext.data_stories.terria_runtime_url`. En dev debe apuntar a `https://data.dev-wins.com/terria/`. Los enlaces originales permanecen como fuente para resolver shares y recursos; configurar el runtime no migra ni modifica las historias.

## Narrativas de Rapid Response

Si el nuevo compositor no carga o el documento es inválido, muestra el error y evita guardar un reemplazo vacío. No pasar HTML antiguo con iframes por Quill: el adaptador lo conserva como contenido original. La cabecera omite consultas de Stories cuando el módulo está desactivado, evitando transacciones fallidas por tablas ausentes. Ver [[Stories en Rapid Response]].

## Banner de Rapid Response recortado en móvil

Si el título o la descripción desaparecen parcialmente a 320 o 390 px, comprobar la altura fija de `.section-title` y el posicionamiento absoluto de `.section-title-content`. El listado y el editor ajustan la altura al texto en móvil. En el editor, verificar también la clase `.rr-story-edit-page` y la carga de `rapid-response-story.css?v=20260924-2`. No basta con comprobar que no haya scroll horizontal: comparar los límites del título y la descripción con los del banner. Ver [[Frontend y Plantillas]] y [[Testing]].
