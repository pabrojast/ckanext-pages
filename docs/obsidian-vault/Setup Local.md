# Setup Local

Tags: #onboarding #operacion
Actualizado: 2026-03-26

Relacionadas: [[Comandos Utiles]], [[Variables de Entorno]], [[Testing]], [[Troubleshooting]]

## Qué necesitas antes

Este repo es una extensión CKAN, no una app autónoma. Para levantarlo localmente necesitas una instancia CKAN base ya funcional o un entorno de desarrollo CKAN compatible.

Compatibilidad observada:

- README: CKAN 2.9 y 2.10
- CI: CKAN 2.9, 2.10 y 2.11
- `setup.py`: Python 3.8, 3.9 y 3.10
- `AGENTS.md`: Python 3.9 a 3.10

## Instalación local mínima

```bash
pip install -r requirements.txt -r dev-requirements.txt
pip install -e .
```

## Habilitar el plugin

En tu `ckan.ini` o configuración equivalente:

```ini
ckan.plugins = pages
```

Opcional para tests de este repo:

```ini
ckan.plugins = pages image_view
```

## Configuración opcional frecuente

```ini
ckanext.pages.organization = true
ckanext.pages.group = true
ckanext.data_stories.enabled = true
ckanext.featured_viewers.enabled = true
```

## Inicialización de base de datos

Para CKAN 2.9+:

```bash
ckan -c test.ini db init
ckan -c test.ini db upgrade -p pages
```

## Verificación rápida

Después de instalar y migrar:

- abrir `/pages`
- abrir `/blog`
- si activaste módulos opcionales, probar `/data-stories` y `/featured-viewers`

## Setup recomendado para desarrollar

1. Instalar en editable.
2. Ejecutar migraciones `pages`.
3. Activar solo los módulos que vayas a tocar.
4. Correr tests del área afectada.
5. Revisar templates y assets asociados si el cambio tiene UI.

## Notas sobre módulos opcionales

### Data Stories

Activación observada en código:

```ini
ckanext.data_stories.enabled = true
```

### Featured Viewers

Activación observada en código:

```ini
ckanext.featured_viewers.enabled = true
```

## Pendiente por confirmar

- Procedimiento estándar del equipo para crear el entorno CKAN base.
- Si usan contenedores fuera de este repo para desarrollo local.
- Qué plugins complementarios se esperan además de `pages` e `image_view`.

## Inferencia

La forma más segura de levantar este repo localmente es reutilizar el mismo patrón que CI: CKAN ya instalado, `pip install -e .`, `db init`, `db upgrade -p pages`.
