# Biblioteca de Imagenes

Ver tambien: [[Index]], [[Flujos Importantes]], [[Testing]], [[Deployment]]

## Funcionamiento

El plugin `pages` proporciona una biblioteca personal para Terria y Data Stories, incluso si Data Stories esta desactivado. `/user/<id>/story-images` permite subir, buscar, editar texto alternativo/descripcion/creditos, copiar enlaces y archivar/restaurar. `/story-images/library` es el selector embebido. Solo el propietario y sysadmins pueden administrar o listar su biblioteca. Los archivos son publicos por enlace, incluso cuando se archivan.

La tabla `ckanext_pages_story_images` guarda propietario CKAN, nombre original, identificador de almacenamiento, formato, dimensiones, bytes, SHA-256, fecha y metadatos. No se crean datasets. Archivar no elimina archivos ni cambia las stories existentes. La eliminacion de usuarios conserva los archivos y deja su propietario nulo.

## Contrato

- `GET /story-images/upload`: sesion, token CSRF y limites; respuesta privada sin cache.
- `POST /story-images/upload`: multipart `upload`; devuelve `uploaded`, `id`, `url`, metadatos y `fileName`.
- Acciones `story_image_create`, `story_image_list` y `story_image_update`. Las escrituras HTTP requieren CSRF; el listado admite `q`, `offset`, `limit` (24 por defecto, maximo 100), `archived` y `owner_id` autorizado.
- `/story-images/<id>` es la URL permanente. Resuelve el backend configurado en cada acceso; una firma temporal de Azure nunca se persiste en la story ni se cachea su redireccion.

Se reutiliza `uploader.get_uploader('story_images')`: asset-storage configurado o almacenamiento local de CKAN. Un fallo de Azure no cae silenciosamente a disco local. JPEG/PNG/WebP/GIF se verifican decodificando el contenido. Limites: `ckan.max_image_size`, 25 millones de pixeles, 500 frames y 100 millones de pixeles acumulados en animaciones. Las imagenes estaticas se ajustan a 1600 px, conservando proporcion y transparencia. Las animaciones se conservan. El hash por usuario permite reintentos sin entradas duplicadas.

## Edicion y compatibilidad

Data Stories usa el mismo servicio en galeria, bloques de imagen, secciones y campos Resumen, Pregunta de investigacion y Area de estudio. El guardado espera las subidas y convierte las imagenes `data:` antiguas; si algo falla, conserva el borrador. Las acciones de escritura rechazan imagenes pendientes y la ruta valida las secciones antes de persistir la cabecera.

No se convierten stories al visitarlas ni se realiza migracion masiva. Los enlaces externos y `/pages_upload` se conservan. Cambiar metadatos de biblioteca afecta inserciones futuras. Las stories ya insertadas conservan su texto.

## Operacion y pruebas

Aplicar `ckan -c /app/production.ini db upgrade --plugin pages` (migracion `5c6d7e8f9a0b`). La imagen de produccion debe incluir el comando en `docker-afterinit.d/02_updatedb.sh`; el overlay de esta entrega serializa las migraciones con un bloqueo PostgreSQL para admitir varias replicas. Desplegar CKAN/tema antes de Terria. En TerriaMap configurar `storyImageUploadUrl: /story-images/upload` y `storyImageLibraryUrl: /story-images/library`, en el mismo origen; nunca por el proxy del mapa.

Pruebas focalizadas: `test_story_image_processing.py` y `test_story_images.py`, con pytest-ckan sobre una base aislada. Cubren raster real, limites, animaciones, transparencia, deduplicacion, permisos, archivo, CSRF, cache privado, descarga anonima y rechazo de imagenes pendientes. La verificacion de navegador debe incluir ambas superficies, conversion al guardar, reintento y ancho 390 px.

La entrega inicial se verifico en desarrollo (`data.dev-wins.com`, contexto `default`, namespace `ckan`). El backport de produccion parte de `61a4eab` y agrega solo la biblioteca; conserva el editor y Rapid Response de la imagen productiva. Los identificadores finales y evidencia de despliegue se registran en la nota de release del repositorio Docker.
