# Flujos Importantes

Tags: #onboarding #backend #operacion
Actualizado: 2026-05-06

Relacionadas: [[Arquitectura]], [[Modulos]], [[Datos y Persistencia]], [[Troubleshooting]]

## 1. Crear o editar una página base

Flujo:

`route Flask` -> `utils.pages_edit()` -> `ckanext_pages_update` -> `actions._pages_update()` -> `db.Page` -> redirect a show

Puntos relevantes:

- si falta `name`, se deriva del `title`
- la validación pasa por `logic/schema.py`
- campos extra se serializan dentro de `extras`
- se registra una revisión en `revisions`

## 2. Render de una página

Flujo:

`/pages/<slug>` o equivalente -> `utils.pages_show()` -> `ckanext_pages_show` -> validación de privacidad -> render Jinja

Puntos relevantes:

- contenido privado no es visible al público
- autor y sysadmin sí pueden ver ciertos contenidos privados
- se inyectan resource views en el HTML si corresponde

## 3. Workflow Water Family

Aplica a:

- `water-news`
- `water-events`
- `water-publications`

Flujo esperado para usuario no admin:

`crear` -> `draft` o `pending` -> `water_admin_dashboard` -> `approve/reject`

Regla importante:

- si un no-admin intenta `publish`, el sistema lo degrada a `submit/pending`

## 4. Creación / edición de Water Publication con dataset CKAN

Flujo:

guardar `water-publication` (create o edit) -> `_maybe_create_documents_dataset()` -> `package_create` + `resource_create` -> persistir `download_url` y `associated_dataset_url` en la página

Se dispara si el formulario trae:

- flag de creación de dataset
- archivo (`dataset_upload`)
- o link de dataset/documento (`dataset_url`)

Si ninguno está presente, la helper hace early-return y la página se guarda igual.

Puntos relevantes:

- en creación de `water-publications`, el `name` se vuelve a derivar del título actual en cada intento para no arrastrar slugs ocultos viejos entre reintentos del formulario
- el bloque que invoca `_maybe_create_documents_dataset()` corre tanto en crear como en editar; antes era solo creación, lo que dejaba al usuario sin manera de re-adjuntar un PDF cuando el primer intento fallaba en silencio (la página quedaba con `dataset_title` pero sin `download_url` ni dataset asociado, y `/documents` no listaba nada)
- cuando ese flujo necesita hacer un segundo `ckanext_pages_update()` para persistir `download_url` / `associated_dataset_url`, reutiliza el slug real de la página (`page` o `name`) incluso en el create path; sin eso, el segundo save podía reentrar como alta nueva y chocar con la validación `Page name already exists in database`
- los errores de la helper se loguean con `log.warning(... exc_info=True)` además del `flash_error`, que ahora aplana `error_dict` (cuando es `ValidationError`) en `field: msg | field: msg` para que el editor vea cuál campo del schema scheming rechazó el payload, no un `{'campo': ['mensaje']}` confuso
- `notes_translated.en` cae al `dataset_title` cuando el formulario no aporta descripción, porque el preset `schemingdcat_fluent_notes_translated` rechaza valores vacíos en lenguajes requeridos. Sin este fallback la creación del dataset documents falla silenciosamente cuando el usuario sólo subía un PDF y no rellenaba la descripción, dejando la publicación sin `download_url`.
- el campo `publication_type` del formulario se mapea al `document_type` del dataset documents (mismo vocabulario que `schemingdcat/unesco/documents.yaml`: `scientific_paper`, `technical_report`, `policy_brief`, …) para que página y dataset queden alineados
- la creación del dataset usa `package_create(..., context['return_id_only']=True)` y luego hace un `package_show(ignore_auth=True)` aparte. Esto evita un fallo observado en producción donde plugins encadenados sobre `package_show` (`ckanext-terria-view`) disparaban `NotFound` al final de `package_create`, dejando la publicación sin dataset aunque el formulario trajera PDF/link válido
- cuando el formulario resuelve una organización, la helper la incluye en `package_create` desde el inicio. La validación core de CKAN exige `owner_org` para usuarios no-sysadmin (`{'owner_org': ['An organization must be provided']}`), así que el intento previo de "crear sin org y asignarla con `package_owner_org_update` después" hacía fallar TODA creación de dataset y empujaba cada upload al fallback de `page_images` — quedando ausente en `/documents`. Las dos carreras reales que sí necesitamos esquivar (insert in-hook de `ckanext-doi` y `package_show` encadenado) están cubiertas por `_skip_doi_create` y `return_id_only` en el contexto.
- si `_maybe_create_documents_dataset()` falla (típicamente por permisos de `create_dataset` o por validaciones del schema scheming), `_fallback_upload_publication_file()` sube el archivo vía `ckanext_water_family_upload` (`/uploads/page_images/...`) y lo guarda como `download_url`, para que la página tenga al menos un archivo visible en lugar de quedarse silenciosa. La plantilla `water-publications.html` reconoce esa ruta como inline-viewable vía `is_ckan_download_url`, incluyendo el caso en que el storage backend reescribe la URL al object store configurado (Azure blob, S3, CDN).
- el segundo guardado que persiste `download_url` / `associated_dataset_url` normaliza `featured=None` a `False` o preserva el valor existente. Sin esto, el fallback podía subir el archivo correctamente pero fallar al guardar la página por la restricción `ckanext_pages.featured NOT NULL`.
- la plantilla `water-publications.html` muestra un aviso "No file or link is attached" a editores cuando `doc_url` está vacío, para que los autores no asuman que el upload tuvo éxito sólo porque la página existe
- en re-edición con archivo nuevo, si ya existe un dataset para esta publicación, `_generate_unique_dataset_name` añadirá sufijo `-1`, `-2`… y se creará un dataset adicional (no se sobrescribe el existente). Pendiente por confirmar si conviene atachar el resource al dataset existente vía `resource_create(package_id=...)` en lugar de crear uno nuevo.

## 5. Workflow Open Source Software

Flujo:

autor crea entrada -> `submission_status=pending` -> sysadmin revisa en `/open-source-admin` -> aprueba o rechaza

Características:

- el sistema intenta fijar `ihp_organization`
- el admin puede cambiar organización al aprobar o después

## 6. Workflow AI Water Tools

Muy parecido al de Open Source Software:

autor crea -> pending -> sysadmin revisa en `/ai-water-admin` -> approve/reject/change-org

## 7. Rapid Response

Flujo principal:

crear contenido `rapid-response` -> usar filtros/event types -> render lista y detalle

Características:

- filtros por país, severidad, actividad y tipo de evento
- administración de event types desde `/admin/event-types`

## 8. CRIDA

Flujo funcional:

seed desde archivos locales -> páginas `crida-case-study` -> listado web -> APIs JSON/GeoJSON -> dashboard admin para moderación

Entradas asociadas:

- comando `seed-crida`
- rutas `/crida/*`
- acciones `ckanext_crida_case_study_*`

## 9. Data Stories

Flujo editorial observado:

`draft` -> `submitted` -> `under_review` -> `published`

Capacidades:

- secciones ordenadas
- vínculo a datasets CKAN
- comentarios
- import/export
- integración Terria

Persistencia y visualización:

- el selector de datasets tiene autocomplete (GET `package_search`, debounce 300 ms) y conserva el flujo pega-URL exacto vía `POST package_show` (el GET de `package_show` está bloqueado en el deployment — algún plugin lo encadena sin `side_effect_free`); normaliza cada entrada con el identificador canónico retornado por CKAN y muestra el error en el propio formulario
- el campo `datasets_data` distingue "payload ausente/corrupto" (sentinel `_KEEP_DATASETS`: se conservan los vínculos existentes) de "el autor vació la lista" (`''`/`'null'`/`'[]'`); el JS serializa la lista vacía como `'[]'`
- create/edit valida todos los datasets antes de mutar la story; los datasets se sincronizan ANTES que las secciones para que un error de validación de secciones no pierda los vínculos; la sincronización agrega, reordena y elimina en una sola transacción
- en modo `storymap`, cada sección normaliza todos sus tabs `#share`/`#start` como fuentes seleccionables; las Story Slides nativas de TODAS las fuentes se convierten en steps (aplanados en orden de fuente, con `source_index` para que el scroll cambie de mapa), incluso cuando solo existe una
- las secciones sin fuente Terria válida usan layout editorial completo y ocultan el mapa sticky; una sección posterior con mapa reactiva el iframe y aplica su propia fuente
- las imágenes pueden provenir del HTML de una Story Slide Terria o de bloques `image` independientes guardados por el editor CKAN

## 10. Featured Viewers

Flujo editorial observado:

`draft` -> `submitted` -> `under_review` -> `published` -> `archived`

Capacidades:

- viewers por categoría
- map rooms
- datasets vinculados
- APIs auxiliares para Terria

## 11. Uploads

Dos rutas principales:

- `pages_upload`
- `water_family_upload`

Particularidades:

- validación por tipo de archivo
- soporte de logos procesados con Pillow
- fallback al uploader base de CKAN si falla el plugin uploader

## Pendiente por confirmar

- flujo real de aprobación usado por negocio para cada vertical
- si `data_stories` en producción requiere review siempre o puede autopublicar según config

## Inferencia

El patrón transversal más importante del repo es: “autor aporta contenido privado o pendiente, admin lo valida y recién entonces pasa a público”.
