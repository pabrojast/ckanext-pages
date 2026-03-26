# Deployment

Tags: #deployment #operacion
Actualizado: 2026-03-26

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

- mecanismo real de restart en producción
- pipeline de build/release del equipo
- estrategia de backup/rollback
- almacenamiento de uploads en producción

## Inferencia

La extensión está diseñada para integrarse dentro de una plataforma CKAN ya operativa; este repo no describe el entorno productivo completo.
