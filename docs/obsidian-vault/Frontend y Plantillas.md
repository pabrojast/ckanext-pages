# Frontend y Plantillas

Tags: #frontend #arquitectura
Actualizado: 2026-03-28

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
- `ckanext_pages/water-news_edit.html`, `ckanext_pages/water-events_edit.html` y `ckanext_pages/water-publications_edit.html` llevan JS inline para sincronizar `uploaded_images`, `country_groups` e `initiative_groups` como JSON; cuando no hay selección se normalizan a `[]` y el selector de member states incluye una opción de “All member states”.
- `ckanext_pages/water-news.html` y `ckanext_pages/water-events.html` renderizan la galería subida y las asociaciones desde `extras`; los templates deben tolerar tanto JSON string como listas ya parseadas por `table_dictize()`.

## Pendiente por confirmar

- Estrategia oficial de empaquetado de assets en producción.
- Si todos los assets listados están realmente conectados a templates activos.

## Inferencia

La capa frontend fue creciendo por feature; eso explica que los assets estén repartidos entre `public/`, `theme/public/`, `assets/` y `textbox/`.
