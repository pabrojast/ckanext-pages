# Frontend y Plantillas

Tags: #frontend #arquitectura
Actualizado: 2026-03-30

Relacionadas: [[Estructura del Repo]], [[Modulos]], [[Flujos Importantes]]

## Organización del frontend

### Templates Jinja

Directorios principales:

- `ckanext/pages/theme/templates_main/ckanext_pages/`
- `ckanext/pages/theme/templates_main/data_stories/`
- `ckanext/pages/theme/templates_main/featured_viewers/`
- `ckanext/pages/theme/templates_main/macros/`
- `ckanext/pages/theme/templates_main/snippets/`

Además existen overrides específicos para:

- organizaciones: `theme/templates_organization/`
- header principal: `theme/templates_main/header.html`

## Qué vive dónde

### `ckanext_pages/`

Templates del módulo base y verticales sobre `ckanext_pages`, por ejemplo:

- `page.html`, `page_edit.html`
- `blog*.html`
- `rapid-response*.html`
- `water-news*.html`
- `water-events*.html`
- `water-publications*.html`
- `open-source-software*.html`
- `ai-water-tools*.html`
- `crida*.html`
- dashboards admin

### `data_stories/`

Templates propios del módulo opcional:

- list
- create/edit
- show
- review
- pending_review
- import
- componentes de secciones

### `featured_viewers/`

Templates propios del módulo opcional:

- list
- show
- edit
- pending review
- rooms
- componentes de cards y paneles

## Assets públicos detectados

### JS en `ckanext/pages/public/js/`

- `ai-water-tools.js`
- `crida.js`
- `crida-edit.js`
- `data-stories-edit.js`
- `featured-viewers.js`
- `open-source-software.js`
- `open-source-software-edit.js`
- `rapid-response-edit.js`
- `terria-tabs-display.js`
- `water-form-enhancements.js`

### CSS en `ckanext/pages/public/css/`

- `ai-water-tools.css`
- `data-stories-edit.css`
- `featured-viewers.css`
- `open-source-software.css`
- `rapid-response-edit.css`
- `water-form-enhancements.css`

### Theme public

También existen assets en `ckanext/pages/theme/public/`, incluyendo:

- `js/data-stories.js`
- `css/data-stories.css`

## Editor WYSIWYG

Hay dos caminos visibles:

- editor configurable por `ckanext.pages.editor` con soporte `medium` o `ckeditor`
- resource view `textboxview` con assets en `ckanext/pages/textbox/`

El repo incluye vendor assets de CKEditor tanto en `assets/vendor/ckeditor/` como bajo `textbox/theme/vendor/ckeditor/`.

## Pistas prácticas para tocar UI

- Si cambias formularios del módulo base, probablemente tocarás `utils.py`, schema y `ckanext_pages/*_edit.html`.
- Si cambias comportamiento JS de formularios enriquecidos, revisar `public/js/*-edit.js` y `water-form-enhancements.js`.
- Si cambias listados o cards de módulos opcionales, tocar sus templates dedicados en `templates_main/data_stories` o `templates_main/featured_viewers`.

## Notas de interacción

- `ckanext_pages/open-source-software_list.html` usa dropdowns custom de filtros (`.unified-dropdown` y `.unified-dropdown-menu`) controlados por `public/js/open-source-software.js`.
- Inferencia: estos filtros deben permanecer desacoplados de `Bootstrap` (`.dropdown`, `.dropdown-menu`, `data-toggle="dropdown"`) para no interferir con el menú principal de navegación.
- `ckanext_pages/open-source-software.html` reutiliza `public/js/open-source-software.js` y `public/css/open-source-software.css` para normalizar listas ordenadas partidas por el editor y mantener la tipografía de listas consistente con el texto del bloque.
- `ckanext_pages/ai-water-tools_list.html` usa el mismo patrón de dropdown custom para filtros y depende de `public/js/ai-water-tools.js` más reglas de stacking en `public/css/ai-water-tools.css` bajo el contenedor real `.ai-water-filters`.
- `ckanext_pages/ai-water-tools_list.html` calcula los contadores de resumen desde el resultado filtrado completo antes de paginar; en `/ai-water-tools?page=N` no deben colapsar al número de items visibles de esa página.
- `featured_viewers/list.html` encapsula sus dropdowns custom de iniciativa, member state y organización en `public/css/featured-viewers.css`; los labels deben neutralizar pseudo-elementos globales del theme y la barra de acciones usa layout flex para alinear `Create Viewer`, `Create Map Room` y `Pending Review`.
- `featured_viewers/show.html` envuelve el iframe de Terria y su action bar en `#fv-map-shell`; el fullscreen se maneja desde `public/js/featured-viewers.js` con la Fullscreen API y fallback CSS, y el botón principal no debe reutilizar la clase genérica `primary` porque el theme puede sobreescribirla.
- `ckanext_pages/water-news_edit.html`, `ckanext_pages/water-events_edit.html` y `ckanext_pages/water-publications_edit.html` llevan JS inline para sincronizar `uploaded_images`, `country_groups` e `initiative_groups` como JSON; cuando no hay selección se normalizan a `[]` y el selector de member states incluye una opción de “All member states”.
- `ckanext_pages/water-events_edit.html` detecta si `agenda_document` es PDF o imagen antes de subirlo y envía `asset_role=agenda_document`; en backend ese adjunto acepta ambos formatos con tope de `20MB`.
- `ckanext_pages/water-publications.html` usa `download_url` o `publication_url` para el viewer del documento y `associated_dataset_url` para enlazar la página del dataset CKAN; si esos extras quedaron vacíos pero existe un dataset `documents` con el mismo título, `utils.py` intenta recuperar el recurso y la URL del dataset al renderizar o editar la página. Cuando el recurso es una imagen subida, el preview depende de guardar o recuperar una URL pública de descarga del recurso.
- En `water-publications.html` el tipo de viewer (PDF.js / image preview / file card) se decide a partir de la extensión real del `doc_url` cuando es una extensión conocida, y solo se cae a `c.page.document_format` cuando la URL no tiene extensión reconocible (p. ej. links opacos tipo `unesdoc.unesco.org/ark:/…`). Antes se confiaba primero en `document_format`, lo que provocaba que un recurso reemplazado por un CSV/imagen siguiera abriéndose en PDF.js y reventara con `Invalid PDF structure` en consola.
- El embed inline (PDF.js o `<img>`) en `water-publications.html` solo se monta cuando `h.is_ckan_download_url(doc_url)` es `True`. Esa helper acepta tres formas como same-origin: `/dataset/<x>/resource/<y>/download/<file>` (flujo normal de documents dataset), `/uploads/page_images/<file>` (fallback de `_fallback_upload_publication_file()` cuando la creación del dataset falla) y URLs absolutas a un object store configurado (Azure blob, S3, CDN). Para no aceptar hosts arbitrarios, `_trusted_storage_origins()` arma la lista de orígenes válidos desde, en orden: `ckan.site_url`; el backend de `ckanext-asset-storage` (introspección duck-typed sobre `_svc_client.url` para Azure y `_bucket.client.api_endpoint` para Google Cloud — en este deploy Azure lo expone como `https://ihpwinsdata.blob.core.windows.net/`); el resultado de `helpers.url_for_static('uploads/page_images/_probe', qualified=True)` (útil sólo cuando un plugin override la helper, ya que CKAN core la resuelve a `site_url`); y la config opcional `ckanext.pages.trusted_storage_hosts` (lista CSV de `scheme://host`) como override manual. Importante: el primer fix que sólo derivaba el origin desde `url_for_static` no funcionó en este deploy porque el AssetUploader genera la URL del blob directamente con `BlobClient.url`, no vía `url_for_static`. Para links externos (UNESDOC `ark:/…` y similares) se renderiza un panel "Preview not available" y se delega a los botones Read Online / Download, porque PDF.js cross-origin termina recibiendo HTML wrapper y rompe el visor. La helper `is_ckan_download_url` está expuesta desde `plugin.get_helpers` y es un wrapper público sobre `utils._is_ckan_download_url`.
- `water-publications_edit.html` y `water-publications_quick.html` exponen un select `publication_type` con el mismo vocabulario que `schemingdcat/unesco/documents.yaml` (`scientific_paper`, `technical_report`, `policy_brief`, …); ese valor se persiste en los extras de la página y, si la creación del dataset documents tiene éxito, se manda como `document_type` al `package_create`. El select `document_format` queda como "File format" — sólo la extensión del archivo, autodetectada al subir.
- `water-publications.html` muestra un alert "No file or link is attached" cuando `doc_url` está vacío y el visitante puede editar la publicación (`h.check_access('ckanext_water_publications_update')`). Sirve como señal explícita cuando la creación del dataset documents falló en silencio y no hubo fallback usable, en lugar de dejar la sección Document oculta sin diagnóstico.
- `utils._recover_water_publication_dataset_links` solo busca paquetes cuyo `name` matchee `document-{slug}%` (el prefijo que escribe `_maybe_create_documents_dataset`). Antes también caía a `name == plain_name` y `title == dataset_title`, lo que producía falsos positivos: una publicación con título genérico (p. ej. "test") heredaba en silencio el resource de cualquier `/dataset/test` preexistente — incluso datasets privados que el visitante anónimo no podía abrir. Si el editor quiere enlazar un dataset externo debe poblar `dataset_url` o `associated_dataset_url` desde el formulario.
- `ckanext_pages/water-news.html` y `ckanext_pages/water-events.html` reutilizan el enriquecimiento de grupos de `utils._enrich_publication_display()` para mostrar initiatives y member states con cards enlazadas, igual que `water-publications.html`.
- `ckanext_pages/water-news.html` y `ckanext_pages/water-events.html` renderizan la galería subida y las asociaciones desde `extras`; los templates deben tolerar tanto JSON string como listas ya parseadas por `table_dictize()`.
- `ckanext_pages/water-news.html` usa `object-fit: cover` en la grilla de miniaturas y `object-fit: contain` en el modal de preview; no conviene reutilizar el layout del thumbnail para la vista ampliada.
- `ckanext_pages/water-news.html` y `ckanext_pages/water-events.html` cierran el modal de galería con handlers explícitos para el botón `X` y el backdrop; no dependen sólo del `data-dismiss` de Bootstrap.
- Las plantillas de display que renderizan contenido editado en Quill (`water-news.html`, `water-events.html`, `rapid-response.html`, `water-publications.html`) incluyen reglas CSS para las clases `ql-align-*` (centrar/justificar texto e imágenes) y un bloque JS que: (a) extrae cualquier `<iframe>` envuelto por Quill en `<pre class="ql-syntax">` (su botón "code block") y (b) si el iframe no trae `height` explícito copia el `style.height` del `<div>` ascendente más cercano. Sin esto, las imágenes con `<p class="ql-align-center">` no se centran y los embeds pegados como bloque de código se ven recortados.
- `ckanext_pages/crida.html` renderiza los avatares de `group_members` con la URL ya normalizada desde backend; cuando `user.image_url` viene como nombre de archivo de CKAN debe resolverse a `/uploads/user/...`, y si no hay imagen usa Gravatar o inicial.
- `ckanext_pages/crida.html` usa iconos de Font Awesome ya presentes en el theme para los empty states del hub; en `Events` el estado vacío usa `fa-calendar` para evitar glifos faltantes con el bundle activo.
- `data_stories/edit.html` ofrece autocomplete de datasets (dropdown sobre GET `package_search`, filas construidas con `.text()` para evitar inyección) además del flujo pega-URL vía `POST /api/3/action/package_show` (URL, slug o UUID); conserva en `datasets_data` la metadata canónica devuelta por CKAN (`'[]'` cuando el autor vació la lista) y el feedback de carga, duplicado o error vive en un contenedor `aria-live` del formulario.
- `data_stories/show_storymap.html` recibe desde `helpers/storymap.py` un layout por sección (`split` o `full`) y una lista de fuentes Terria con steps por fuente (`data-source-index` en cada step); `data-stories-storymap.js` reutiliza un solo iframe, avanza de fuente en fuente con el scroll (los tabs siguen el scroll y un clic los fija), y aplica tanto shares como `startData` normalizado a través del bridge `applyScene`. Los assets de storymap usan cache-bust manual `?v=` (actual: `20260904-1`).
- una sección storymap `full` ocupa ambas columnas y oculta temporalmente el panel sticky; sus bloques `image` se muestran en el flujo editorial. Una sección `split` mantiene el comportamiento de mapa/overlay.

## Pendiente por confirmar

- Estrategia oficial de empaquetado de assets en producción.
- Si todos los assets listados están realmente conectados a templates activos.

## Inferencia

La capa frontend fue creciendo por feature; eso explica que los assets estén repartidos entre `public/`, `theme/public/`, `assets/` y `textbox/`.
