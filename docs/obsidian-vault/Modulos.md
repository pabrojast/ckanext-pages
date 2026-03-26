# Modulos

Tags: #arquitectura #backend
Actualizado: 2026-03-26

Relacionadas: [[Arquitectura]], [[Rutas y Entrypoints]], [[Flujos Importantes]], [[Datos y Persistencia]]

## Visión general

El repo contiene un módulo base y varios verticales funcionales.

## 1. Pages Core

Responsabilidad:

- CMS básico para páginas y blog dentro de CKAN.

Piezas clave:

- `plugin.py`
- `blueprint.py`
- `actions.py`
- `auth.py`
- `db.py`
- `logic/schema.py`
- `theme/templates_main/ckanext_pages/page*.html`

Persistencia:

- tabla `ckanext_pages`

## 2. Rapid Response

Responsabilidad:

- contenido tipo incidente o evento de emergencia con timeline, severidad, países afectados y bloques de contenido.

Señales en código:

- `page_type='rapid-response'`
- filtros por `country`, `activity_status`, `severity`, `event_type`
- admin de event types

## 3. Water Family

Responsabilidad:

- agrupa `water-news`, `water-events` y `water-publications`.

Características:

- dashboard admin de aprobación
- upload especializado
- filtros por iniciativa, member state, water type y publication type
- formularios enriquecidos

Particularidad:

- `water-publications` puede crear datasets CKAN tipo documento al momento de crear la página.

## 4. Open Source Software

Responsabilidad:

- catálogo de software open source con workflow editorial y asignación de organización.

Características:

- estado de envío `draft/pending/approved/rejected`
- dashboard admin propio
- cambio de organización desde dashboard

## 5. AI Water Tools

Responsabilidad:

- catálogo de herramientas de IA aplicadas al agua.

Características:

- muy parecido al flujo de Open Source Software
- comando de importación desde `ai_water_tools_seed.json`

## 6. CRIDA Case Studies

Responsabilidad:

- hub y catálogo de casos de estudio CRIDA con mapa GeoJSON y reseeding desde archivos de datos.

Características:

- `page_type='crida-case-study'`
- APIs públicas JSON y GeoJSON
- dashboard admin
- seed desde `ckanext/pages/data/`

## 7. Data Stories

Responsabilidad:

- storytelling estructurado con secciones, datasets vinculados, comentarios y embebidos Terria.

Ubicación:

- `ckanext/pages/data_stories/`

Características:

- tablas propias
- blueprint propio `/data-stories`
- workflow editorial completo
- import/export
- tests propios

Se activa con:

- `ckanext.data_stories.enabled`

## 8. Featured Viewers

Responsabilidad:

- viewers temáticos y map rooms con integración Terria.

Ubicación:

- `ckanext/pages/featured_viewers/`

Características:

- tablas propias
- blueprint `/featured-viewers`
- map rooms
- acciones CRUD y publish/review

Se activa con:

- `ckanext.featured_viewers.enabled`

## 9. TextBoxView

Responsabilidad:

- resource view CKAN `wysiwyg` para mostrar texto libre asociado a recursos.

Ubicación:

- `ckanext/pages/textbox/`

## Resumen de acoplamiento

- `Pages Core`, Rapid Response, Water Family, Open Source, AI Water Tools y CRIDA comparten tabla base `ckanext_pages`.
- `Data Stories` y `Featured Viewers` están mejor modularizados y usan tablas separadas.

## Pendiente por confirmar

- Si todos los módulos especializados están activos en la instancia objetivo.
- Si `featured_viewers` tiene una suite de pruebas fuera de este repo o aún no la tiene.
