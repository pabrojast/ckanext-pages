# Troubleshooting

Tags: #operacion #onboarding
Actualizado: 2026-05-06

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

## Code smell útil de recordar

`utils.py` contiene dos definiciones de `crida_admin_reseed()`. Si haces cambios allí, revisa cuál definición termina vigente.

## Pendiente por confirmar

- logs y observabilidad productiva
- almacenamiento real de uploads
- mecanismos de rollback productivo
