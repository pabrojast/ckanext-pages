# Flujos Importantes

Tags: #onboarding #backend #operacion
Actualizado: 2026-03-28

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
- los errores de la helper se loguean con `log.warning(... exc_info=True)` además del `flash_error`, para que fallos silenciosos queden trazables en logs del servidor
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
