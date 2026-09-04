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
- admin de disaster types (tipos de desastre) en `/admin/disaster-types`

Disaster Types:

- sistema independiente de los event types de Water Events
- tipos por defecto: Tropical Cyclone, Earthquake, Tsunami, Flood, Wildfire, Volcanic Eruption, Drought, Armed Conflict, Man-made Disaster
- almacenados en config `ckanext.pages.disaster_types` como JSON
- acciones CRUD: `disaster_types_list`, `disaster_types_show`, `disaster_types_create`, `disaster_types_update`, `disaster_types_delete`
- helpers: `get_disaster_types()`, `get_disaster_type_by_id()`
- templates admin: `admin/disaster_types_admin.html`, `admin/disaster_types_edit.html`, `admin/disaster_types_delete.html`

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

### Water Events: extras específicas

- **Vista calendario** (`/water-events/calendar`): se renderiza con FullCalendar 6 cargado vía CDN (`cdn.jsdelivr.net`). Lee `publish_date` y `event_end_date` y los serializa con `tojson` en el template para evitar inyecciones. La controladora respeta los filtros `q`, `event_type`, `initiative`, `member_state` y `source`.
- **Eventos destacados** (`featured`): columna boolean en `ckanext_pages` (migración `4b5c6d7e8f9a`), expuesta en el listado como sección "Featured Events" en la primera página. El toggle es solo `sysadmin` y vive en `POST /water-events/<page>/feature`. El campo `featured` se descarta del payload del formulario regular en `_pages_update` para usuarios no admin (defensa en profundidad).
- **Distinción IHP / Community**: el helper `is_ihp_event(page)` (`plugin.py`) resuelve en este orden: (1) flag explícito `ihp_official` (extra JSON, sólo editable por sysadmin desde el formulario de edición de water-events; valores `True`/`False` ganan a la heurística); (2) heurística legacy: `ihp_organization` no vacío, o creador sysadmin (cache de IDs sysadmin de 60 s). Con la heurística vacía vuelve al fallback. El campo `ihp_official` se descarta del payload para no-sysadmin en `_pages_update` (defensa en profundidad, mismo patrón que `featured`). Hay un tab-filter (All / IHP / Community) tanto en lista como en calendario, y un badge por tarjeta.

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
- import/export individual y bulk (sysadmin-only)
- comandos CLI para export/import (útil para migración con `kubectl`)
- tests propios
- dos modos de visualización por story (`display_mode`): `classic` (secciones apiladas, default) y `storymap` (scrollytelling tipo ArcGIS StoryMaps con un único iframe Terria sticky reutilizado entre escenas)

Modo `storymap`:

- template `data_stories/show_storymap.html` + `public/js/data-stories-storymap.js` + `public/css/data-stories-storymap.css`
- helpers en `data_stories/helpers/storymap.py` (`build_terria_scene_url`, `get_storymap_scenes`, `get_storymap_config`, `resolve_terria_share`)
- mecanismo de escenas con autodetección: si el build de Terria postea `"ready"` al padre (bridge postMessage), el iframe carga Terria sin share y las escenas se aplican vía postMessage con las `stories` embebidas eliminadas (así el panel nativo de story de Terria nunca se abre dentro del embed); si no hay bridge, fallback a fragment navigation (`#clean&share=...`, sin recargar Terria). El timeout del bridge es 12 s (un boot frío de Terria tarda ~10 s en postear `"ready"`) y un `"ready"` tardío estando ya en modo hash hace upgrade a bridge — sin esto los steps quedaban muertos toda la sesión cuando Terria arrancaba lento
- cada sección puede tener varios tabs Terria (`#share` o `#start`), mostrados como fuentes de mapa dentro del mismo capítulo; elegir un tab fija (pin) esa fuente hasta salir de la sección. Los shares de TODAS las fuentes se resuelven en servidor (pool de hilos ≤4 cuando hay varias frías; fallos con warning `[STORYMAP] Steps unavailable for share <id>` y sin cachear, se auto-reparan al siguiente render) y los steps de cada capítulo se aplanan en orden de fuente: cada step lleva `source_index`/`step_index` local/`step_total`/`source_title`, el template los marca con `data-source-index` (con un divisor visual al cambiar de fuente) y el scroll avanza de un mapa al siguiente dentro del capítulo, sincronizando el highlight de tabs
- las stories nativas de Terria se expanden en "steps" aunque contengan una sola Story Slide: cada slide se renderiza dentro de la tarjeta con su título y HTML, incluidas imágenes; al activarse la tarjeta el mapa salta a la primera slide y luego avanza por los steps al hacer scroll
- los enlaces `#start` se decodifican y normalizan a `startData` en servidor. Tanto esos datos como los shares pasan por el único mensaje postMessage `applyScene` (replaceStratum, reemplazo limpio de capas), solo mientras el build lo confirme con el ack `sceneApplied`. Un ack perdido degrada SOLO ese apply a fragment navigation; dos misses consecutivos durante la fase de probe latchean el modo hash, y un `"ready"` posterior (boot nuevo) re-arma el probe. El bookkeeping usa `appliedKey` (confirmado en el mapa) e `inFlightKey` (esperando ack): las keys solo se promueven con el ack, así un apply fallido queda reintentable. No se reintroduce el mensaje genérico `updateFromStartData`, que no renderiza capas COG en builds estándar de Terria (TypeError `'buffer'` en los workers de geotiff)
- el ack `sceneApplied` llega en dos fases desde el fork de terriajs (`pabrojast/terriajs`): `received` inmediato (prueba de capacidad, evita que escenas pesadas disparen el fallback por timeout) y `complete` al terminar `applyInitData`; builds con el handler antiguo mandan un único ack sin `phase` (tratado como completion). El handler además limpia `terria.stories` residuales de una carga hash previa
- los embeds llevan `hideStory=1` y `hideWelcomeMessage=1` (además de `hideWorkbench=1&hideExplorerPanel=1`): el primero suprime la apertura automática del panel nativo de story (solo fork de terriajs), el segundo el modal de bienvenida (soportado por terriajs estándar); builds que no los conocen los ignoran
- preview sin convertir la story: `/data-stories/<slug>?layout=storymap`
- resolución de shares: el API base se deriva del propio share link (`{origin}{path}/api/v1/share/`), tanto en el render (expansión de steps) como en el navegador (fetch directo, el API de shares de Terria envía CORS abierto) — no depende de `ckanext.pages.terria_base_url`. El endpoint `/data-stories/api/terria-scene/<share_id>` (proxy cacheado contra la instancia configurada) queda como fallback del navegador
- durante el cambio de escena se muestra un pill "Loading scene…" y un veil tinte+blur sobre el mapa (clase `is-switching`) con timing asimétrico (entra rápido 0.2s, sale lento 0.55s) que hace de crossfade — los píxeles de un iframe cross-origin no se pueden capturar, así que el veil ES la transición; respeta `prefers-reduced-motion`. Se oculta con el ack `sceneApplied` o por timeout; un token `switchSeq` evita que timers viejos (hash swaps anteriores, failsafes) apaguen el veil de un apply más nuevo
- carga anticipada: el iframe se carga de inmediato al abrir la página (no lazy — el boot frío de Terria ~10 s corre mientras se lee el hero) y, al activarse el bridge, se pre-calientan los share JSON de todas las escenas (`warmShares`). La banda de activación del observer es asimétrica (`-45% 0px -35%`): bajando, las escenas se aplican ~10vh antes
- una sección sin ningún tab Terria válido se renderiza automáticamente a ancho completo y oculta el panel sticky; el siguiente capítulo con mapa lo vuelve a mostrar y aplica su propia escena, sin heredar visualmente el mapa anterior. El fallback al `terria_share_link` de sección está acotado: solo aplica en secciones legacy (sin `blocks_metadata` usable) o cuando existe un bloque terria cuyos tabs no parsean — si `blocks_metadata` existe y no tiene bloque terria, el autor quitó el mapa y un link stale NO lo resucita (el editor además limpia el hidden al borrar el bloque, y el server lo fuerza a `''` en el extract del form)
- bloques `image` (tipo en `blocks_metadata`: `{type:'image', url, alt, caption}`): en una sección con mapa la tarjeta muestra un thumbnail-trigger y, mientras es el stop activo, el panel sticky muestra la imagen sobre el mapa; en una sección sin mapa se presenta como imagen editorial a ancho completo. En classic se hornea como `<figure class="story-image">`. Limitación: no se puede intercalar una imagen independiente entre steps de un mismo share (los steps vienen de Terria). El editor tiene botón "Image" con upload (mismo pipeline comprimir+`/pages_upload` que las imágenes inline de Quill)
- navegación directa por bloque: botones ▲/▼ junto a los dots y flechas del teclado (solo cuando el storymap cruza la línea media del viewport, sin foco en inputs y con el lightbox cerrado) saltan al stop anterior/siguiente (steps, triggers de imagen y tarjetas sin steps)
- las secciones de cola (publicación, datasets, galería, contributors) van a ancho completo del container, igual que el hero
- los scripts `data-stories-storymap.js`, `data-stories-edit.js` y el CSS de storymap se incluyen con `?v=` (cache-bust manual — subirlo al cambiarlos; el editor con JS viejo descartaría silenciosamente tipos de bloque desconocidos al guardar)

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
- map rooms (colecciones de viewers)
- acciones CRUD y publish/review
- campo `initiative` en viewers y map rooms para organizar por iniciativa (CRIDA, FRIEND, etc.)
- campos `organization_id` y `countries` (JSONB) en viewers y map rooms
- selección de viewers al crear o editar un map room mediante checkboxes (sin flujo multi-paso)
- filtros por iniciativa, member state y organización en listados de viewers y map rooms

Landing unificada (`/featured-viewers/`):

- hero compacto con buscador unificado (filtra rooms y viewers)
- category tabs al tope (filtran AMBAS secciones: rooms y viewers)
- dropdowns searchable de iniciativa, member state y organización
- sección prominente de Map Rooms (cards grandes, máx 6, con conteo de viewers)
- sección de viewers individuales con paginación
- sección My Drafts colapsable al final (solo para creadores)
- componente `room_card.html` diferenciado de `viewer_card.html`

Formularios de edición (viewers y rooms):

- initiative, organization y countries (member states) en ambos formularios
- countries almacenado como JSONB array de `{name, display_name}`

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
