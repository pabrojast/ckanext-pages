# Comandos Utiles

Tags: #operacion #onboarding
Actualizado: 2026-09-04

Relacionadas: [[Setup Local]], [[Testing]], [[Deployment]]

## Instalación

```bash
pip install -r requirements.txt -r dev-requirements.txt
pip install -e .
```

## Lint

```bash
flake8 . --count --max-line-length=127 --exclude ckan
```

## Inicialización de DB para tests o local

```bash
ckan -c test.ini db init
ckan -c test.ini db upgrade -p pages
```

## Tests del módulo base

```bash
pytest --ckan-ini=test.ini --cov=ckanext.pages --cov-report=term-missing ckanext/pages/tests
```

## Tests de `data_stories`

```bash
pytest --ckan-ini=test.ini ckanext/pages/data_stories/tests
```

## Comandos CKAN expuestos por el plugin

### Reparación de datasets

```bash
ckan -c /etc/ckan/default/ckan.ini pages fix-datasets
ckan -c /etc/ckan/default/ckan.ini pages fix-datasets --dry-run
ckan -c /etc/ckan/default/ckan.ini pages fix-datasets --limit 10
ckan -c /etc/ckan/default/ckan.ini pages fix-datasets --dataset my-dataset-name
```

### Reparación de bloques de Rapid Response

Repara metadata de bloques/mapas colapsada por el bug de round-trip JSON del form de edición (ver [[Troubleshooting]]). Dry-run por defecto.

```bash
ckan -c /etc/ckan/default/ckan.ini pages fix-rapid-response-blocks
ckan -c /etc/ckan/default/ckan.ini pages fix-rapid-response-blocks --apply
ckan -c /etc/ckan/default/ckan.ini pages fix-rapid-response-blocks --page nombre-pagina
```

### Importación de AI tools

```bash
ckan -c /etc/ckan/default/ckan.ini pages import-ai-tools
ckan -c /etc/ckan/default/ckan.ini pages import-ai-tools --dry-run
ckan -c /etc/ckan/default/ckan.ini pages import-ai-tools --update-existing
```

### Seed de CRIDA

```bash
ckan -c /etc/ckan/default/ckan.ini pages seed-crida
ckan -c /etc/ckan/default/ckan.ini pages seed-crida --dry-run
ckan -c /etc/ckan/default/ckan.ini pages seed-crida --update-existing
```

### Data Stories export/import

Exportar todas las stories (stdout o archivo):

```bash
ckan -c /etc/ckan/default/ckan.ini pages data-stories-export
ckan -c /etc/ckan/default/ckan.ini pages data-stories-export --output /tmp/stories.json
ckan -c /etc/ckan/default/ckan.ini pages data-stories-export --status published --output /tmp/published.json
```

Importar stories desde archivo JSON (individual o bulk):

```bash
ckan -c /etc/ckan/default/ckan.ini pages data-stories-import /tmp/stories.json
ckan -c /etc/ckan/default/ckan.ini pages data-stories-import /tmp/stories.json --preserve-status --preserve-dates
ckan -c /etc/ckan/default/ckan.ini pages data-stories-import /tmp/stories.json --slug-conflict overwrite
ckan -c /etc/ckan/default/ckan.ini pages data-stories-import /tmp/stories.json --dry-run
```

Flujo de migración dev → prod con kubectl:

```bash
# Exportar desde dev
kubectl -n ckan exec -it <pod-dev> -- ckan -c /etc/ckan/default/ckan.ini pages data-stories-export --output /tmp/stories.json
kubectl -n ckan cp <pod-dev>:/tmp/stories.json ./stories.json

# Importar en prod
kubectl -n ckan cp ./stories.json <pod-prod>:/tmp/stories.json
kubectl -n ckan exec -it <pod-prod> -- ckan -c /etc/ckan/default/ckan.ini pages data-stories-import /tmp/stories.json --preserve-status --preserve-dates --slug-conflict overwrite
```

Nota: las imágenes referenciadas en `uploaded_images` y `image_url` de secciones deben estar accesibles en el bucket de destino. Si ambos entornos comparten bucket, no se necesita acción adicional.

## Scripts standalone en la raíz

```bash
python fix_broken_datasets_simple.py postgresql://user:password@localhost/ckan
python fix_broken_datasets.py -d postgresql://user:pass@localhost/ckan --dry-run
```

## Después de reparar datasets

```bash
ckan -c /etc/ckan/default/ckan.ini search-index rebuild
```

## Comandos útiles de inspección

```bash
rg --files ckanext/pages
rg -n "ckanext.pages" ckanext/pages
git status --short
```

## Pendiente por confirmar

- Si el equipo usa wrappers como `make`, `invoke`, `tox` o scripts shell externos; no fueron encontrados en este repo.
