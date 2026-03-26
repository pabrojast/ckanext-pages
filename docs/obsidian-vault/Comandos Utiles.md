# Comandos Utiles

Tags: #operacion #onboarding
Actualizado: 2026-03-26

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
