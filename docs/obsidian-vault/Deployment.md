# Deployment

Tags: #deployment #operacion
Actualizado: 2026-09-11

Relacionadas: [[Setup Local]], [[Variables de Entorno]], [[Testing]], [[Datos y Persistencia]]

## Lo que sí está documentado por el repo

El despliegue conocido de la extensión consiste en:

1. instalar el paquete en el entorno CKAN
2. habilitar `pages` en `ckan.plugins`
3. ejecutar migraciones `db upgrade -p pages`
4. activar módulos opcionales por config si corresponde
5. reiniciar CKAN

## Secuencia mínima

```bash
pip install -r requirements.txt
pip install -e .
ckan -c /etc/ckan/default/ckan.ini db upgrade -p pages
```

En `ckan.ini`:

```ini
ckan.plugins = pages
```

Opcional:

```ini
ckanext.data_stories.enabled = true
ckanext.featured_viewers.enabled = true
```

## Particularidades de inicialización

### Módulo base

El plugin ejecuta `ensure_pages_table_exists()` al cargar. Eso sugiere un doble mecanismo:

- migraciones Alembic
- auto-verificación/auto-reparación en startup

### Módulos opcionales

`data_stories` y `featured_viewers` inicializan tablas en `configure()` mediante `init_tables(...)`.

Eso implica que parte del esquema puede crearse en runtime si el módulo se habilita.

## CI/CD detectado

Solo se encontró:

- `.github/workflows/test.yml`

Qué hace:

- lint con `flake8`
- matrix sobre CKAN 2.9, 2.10 y 2.11
- usa contenedores CKAN oficiales en GitHub Actions
- corre migraciones `pages`
- ejecuta tests del directorio `ckanext/pages/tests`

## Lo que no aparece en el repo

- Dockerfiles
- docker-compose
- Helm
- manifests de Kubernetes
- Terraform
- scripts de release

## Recomendación operativa mínima

- tratar `db upgrade -p pages` como paso obligatorio de despliegue
- validar endpoints críticos después del restart
- si habilitas módulos opcionales, validar sus rutas y tablas explícitamente

## Pendiente por confirmar

- pipeline de build/release del equipo

## Inferencia

La extensión está diseñada para integrarse dentro de una plataforma CKAN ya operativa; este repo no describe el entorno productivo completo.

## Conversión reversible de imágenes de Rapid Response

Este cambio no requiere migración de esquema. Los comandos usan la configuración de la instancia y el uploader CKAN configurado; no deben usarse URLs de almacenamiento de otro entorno.

```bash
# Solo auditoría; también permite --page <slug>
ckan -c /srv/app/production.ini pages optimize-rapid-response-images

# Después de verificar un respaldo completo fuera del pod
ckan -c /srv/app/production.ini pages optimize-rapid-response-images --apply --backup-dir /tmp/rr-media-backup

# Simular la reversión; añadir --apply para ejecutarla
ckan -c /srv/app/production.ini pages optimize-rapid-response-images --restore /tmp/rr-media-backup/manifest.json
```

El directorio contiene registros completos comprimidos, originales y un manifiesto con hashes y URLs de las versiones optimizadas. Exportarlo fuera del pod inmediatamente después de la operación. Los archivos temporales del contenedor no constituyen un respaldo durable. Antes de aplicar en producción, exportar además los registros completos fuera del pod.

El comando verifica cada archivo subido antes de actualizar la página, deduplica las imágenes repetidas en contenido/extras/revisiones y conserva identificadores, autores, fechas y estados. El historial recibe únicamente referencias de imagen equivalentes. Una edición concurrente impide sobrescribir la página. La reversión comprueba hashes y rechaza sobrescribir ediciones posteriores; conserva los archivos subidos para no romper referencias compartidas. Un fallo en una página se informa con salida no cero y no invalida las páginas ya convertidas; consultar el manifiesto y reintentar con un directorio nuevo si hubo edición posterior.

Entornos verificados el 2026-09-11: producción usa contexto Kubernetes `ckan`, namespace `ckan`, un HPA CKAN con mínimo de cuatro y máximo de doce réplicas, y `https://ihp-wins.unesco.org`; dev usa contexto `default`, namespace `ckan` y `https://data.dev-wins.com`. Especificar siempre ambos parámetros. La readiness de CKAN empieza a los 300 s; esperar el rollout y comprobar los assets en cada réplica.

Aplicar el parche a la imagen que ya usa cada entorno; sus versiones difieren. Conservar los digests anteriores para rollback de código y usar el manifiesto para rollback del contenido. Validar primero con copias aisladas en dev, después la URL pública, imágenes y mapas en producción.

La operación del 2026-09-11 usa `kubectl set image deployment/ckan` y espera el rollout. El uploader configurado en ambas instancias devuelve URLs de Azure Blob Storage; verificar siempre la configuración efectiva antes de migrar. Los respaldos de esta operación están fuera del clúster en `output/rapid-response/20260911/`, excluidos de Git, con originales, manifiesto, hashes y un `RUNBOOK.md` de reversión. Esta ubicación es una entrega local de la operación, no una política general de backups del equipo.

La URL pública presenta `Cache-Control: public, max-age=30, stale-while-revalidate=180`, pero el VCL de producción fija para contenido anónimo general un TTL de cinco minutos y un grace efectivo de 25 minutos. Hay tres pods Varnish. Durante el rollout pueden devolver HTML anterior. Verificar por pod, usar una URL con parámetro único para comprobar el origen y, después de completar el rollout, invalidar únicamente las rutas públicas del módulo en cada pod Varnish antes de medir la URL canónica:

```bash
kubectl --context ckan -n ckan exec <pod-varnish> -c varnish-cache -- varnishadm ban 'req.url ~ "^(/[a-z]{2})?/rapid-response([/?]|$)"'
```

Resultado verificado el 2026-09-11: cuatro eventos auditados, dos convertidos y cero imágenes inline restantes, incluyendo revisiones. Se conservaron los metadatos; los otros dos registros quedaron idénticos. Nueve réplicas de producción y una de dev saludables, con siete archivos del cambio comprobados por SHA-256 en cada pod. Se eliminaron las dos copias de ensayo y la cuenta temporal de dev, conservando intactos sus eventos originales.

Imágenes finales (sobre la imagen anterior de cada entorno, sin sincronizar extensiones ajenas al cambio):

- Producción: `pabrojast/ckan-base210:rapid-response-prod-20260911-r7@sha256:265ba67ef40ba444a8a90965addc7975ef8b58160493e5558951a6590235d351`.
- Dev: `pabrojast/ckan-base210:rapid-response-dev-20260911-r7@sha256:c8e2e024617704eda92358ce70c584a5932918d9d5d0ce23cffec3ec54dd37bc`.

En cinco descargas completas de la URL canónica de Nepal, HTML de 42.572 bytes y mediana TTFB de 0,639 s, frente a 52.870.351 bytes y aproximadamente 7,3 s antes del cambio. Prueba de navegador: DOMContentLoaded a 1,00 s, fases con formato, imágenes cargadas, sin overflow a 390 px y navegación de mapas iniciada automáticamente al acercarse. Estos tiempos son mediciones de esa sesión, no una garantía para todas las redes o capas de Terria.
