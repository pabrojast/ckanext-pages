# Plan de Trabajo: Corrección de Problemas en Open Source Admin

## Problemas Identificados

### Problema 1: Cambio de Organización no se Aplica
**Síntoma**: Cuando se cambia de grupo/organización en open source admin, el servidor no da error y la página se actualiza, pero el grupo no se reasigna.

**Causa Raíz**: 
- En el archivo `utils.py`, función `open_source_admin_change_org()` (línea 1357-1410)
- El problema está en que después de actualizar `ihp_organization`, NO se está guardando en la base de datos
- La función `_pages_update()` en `actions.py` espera que `ihp_organization` esté en los `items` que se procesan, pero este campo se guarda en `extras` no en campos directos de la tabla

**Ubicación del código**:
- `/home/pabrojast/Proyectos/ckanext-pages/ckanext/pages/utils.py` líneas 1357-1410
- `/home/pabrojast/Proyectos/ckanext-pages/ckanext/pages/actions.py` líneas 218-385 (función `_pages_update`)

**Solución Propuesta**:
1. Verificar que `ihp_organization` esté incluido en el `data_dict` correctamente
2. Asegurar que `ihp_organization` se guarde en la tabla `ckanext_pages` (columna directa, no en extras JSON)
3. Forzar un commit explícito después de la actualización
4. Agregar logging detallado para diagnóstico

### Problema 2: Entrada Aprobada no se Muestra a Usuarios No Registrados
**Síntoma**: Cuando se aprueba una entrada en open source admin, desaparece del panel (correcto), pero no se muestra a usuarios no registrados en `/open-source-software`.

**Causa Raíz**:
- En el archivo `utils.py`, función `pages_list_pages()` (línea 90-173)
- Línea 138: `data_dict['submission_status'] = 'approved'` - CORRECTO para filtrar
- En el archivo `actions.py`, función `open_source_admin_approve()` (línea 1246-1293)
- Líneas 1271-1272: Se establece `submission_status = 'approved'` y `private = False` - CORRECTO
- **PROBLEMA**: En `_pages_list()` (actions.py líneas 83-205), cuando se filtra por `submission_status`, puede estar usando el campo de la base de datos que no se actualiza correctamente

**Ubicación del código**:
- `/home/pabrojast/Proyectos/ckanext-pages/ckanext/pages/utils.py` líneas 128-138
- `/home/pabrojast/Proyectos/ckanext-pages/ckanext/pages/actions.py` líneas 83-205 (función `_pages_list`)
- `/home/pabrojast/Proyectos/ckanext-pages/ckanext/pages/db.py` líneas 108-357 (función `Page.pages`)

**Análisis Detallado**:
1. Cuando un admin aprueba, se llama `open_source_admin_approve()` que actualiza:
   - `submission_status = 'approved'`
   - `private = False`
2. Cuando un usuario no registrado visita `/open-source-software`:
   - Se llama `pages_list_pages('open-source-software')` 
   - Línea 138 filtra: `data_dict['submission_status'] = 'approved'`
   - Se llama `_pages_list()` que luego llama `db.Page.pages(**search)`
3. En `db.Page.pages()` (db.py línea 129):
   - `submission_status = kw.pop('submission_status', None)`
   - Línea 135-136: `if submission_status: query = query.filter(cls.submission_status == submission_status)`
   - **ESTE DEBERÍA FUNCIONAR** si el campo `submission_status` se actualiza correctamente en la BD

**Solución Propuesta**:
1. Verificar que cuando se aprueba, el campo `submission_status` en la BD se actualiza correctamente
2. Agregar logging en `_pages_update()` para confirmar que se guarda `submission_status`
3. Verificar que el campo esté en la lista `items` de `_pages_update()` (línea 256-258)
4. Confirmar que después de aprobar, se hace commit explícito
5. Agregar logging en `_pages_list()` y `db.Page.pages()` para ver qué filtros se aplican

## Plan de Implementación

### Paso 1: Diagnóstico Detallado
1. Agregar logging extensivo en:
   - `open_source_admin_approve()` - confirmar valores antes y después de actualizar
   - `open_source_admin_change_org()` - confirmar valores antes y después de actualizar
   - `_pages_update()` - confirmar qué campos se procesan y guardan
   - `_pages_list()` - confirmar qué filtros se aplican
   - `db.Page.pages()` - confirmar la query SQL generada

### Paso 2: Corrección del Cambio de Organización
1. En `open_source_admin_change_org()`:
   - Verificar que `ihp_organization` está en el `data_dict` correctamente
   - Asegurar que se pasa al action correctamente
   - Forzar un refresh/commit explícito después de actualizar
   - Agregar verificación post-actualización

### Paso 3: Corrección de Aprobación y Visibilidad
1. En `open_source_admin_approve()`:
   - Verificar que todos los campos críticos se actualizan:
     - `submission_status = 'approved'`
     - `private = False` 
     - `reviewed_at`, `reviewed_by`, etc.
   - Forzar un commit explícito
   - Agregar verificación post-actualización para confirmar que se guardó

2. En `_pages_update()`:
   - Confirmar que `submission_status` está en la lista `items` (línea 256-258)
   - Confirmar que se procesa correctamente
   - Agregar logging específico para este campo

3. En `_pages_list()`:
   - Agregar logging para confirmar qué filtros se aplican
   - Verificar que el filtro de `submission_status` se pasa correctamente a `db.Page.pages()`

### Paso 4: Testing
1. Crear entrada de prueba
2. Probar cambio de organización
3. Probar aprobación
4. Verificar visibilidad como usuario no autenticado
5. Verificar que aparece en listado público

### Paso 5: Cleanup
1. Ajustar nivel de logging a WARNING para producción
2. Documentar cambios en CHANGELOG.md
3. Crear tests unitarios si es posible

## Archivos a Modificar

1. `/home/pabrojast/Proyectos/ckanext-pages/ckanext/pages/utils.py`
   - Función `open_source_admin_change_org()` (línea ~1357)
   - Función `open_source_admin_approve()` (línea ~1246)

2. `/home/pabrojast/Proyectos/ckanext-pages/ckanext/pages/actions.py`
   - Función `_pages_update()` (línea ~218)
   - Función `_pages_list()` (línea ~83)

## Campos Críticos en Base de Datos

Según `db.py`, la tabla `ckanext_pages` tiene estas columnas directas (no en JSON extras):
- `id`
- `title`
- `name`
- `content`
- `lang`
- `order`
- `private`
- `group_id`
- `user_id`
- `publish_date`
- `page_type`
- `created`
- `modified`
- `extras` (JSON)
- `revisions` (JSONB)
- `submission_status` ← CAMPO DIRECTO
- `ihp_organization` ← CAMPO DIRECTO  
- `submitted_at`
- `reviewed_at`
- `reviewed_by`

**IMPORTANTE**: Tanto `submission_status` como `ihp_organization` son columnas directas en la tabla, NO están en el JSON `extras`. Por lo tanto, deben procesarse como campos normales en `_pages_update()`.

## Verificación de que están en items[]

En `actions.py` línea 256-258:
```python
items = ['title', 'content', 'name', 'private',
         'order', 'page_type', 'publish_date', 'submission_status',
         'ihp_organization', 'submitted_at', 'reviewed_at', 'reviewed_by']
```

✅ AMBOS CAMPOS ESTÁN EN LA LISTA - Esto está correcto.

## Conclusión

Los campos están correctamente definidos en el código. El problema probablemente es:

1. **Para cambio de organización**: 
   - Falta commit explícito o hay algún problema con la transacción
   - Posible problema con el contexto de sesión de SQLAlchemy

2. **Para visibilidad de aprobados**:
   - Posible problema de caché
   - Posible problema con la transacción/commit
   - Verificar que el filtro `private = False` se está aplicando correctamente además de `submission_status = 'approved'`

La solución incluirá:
- Agregar commits explícitos
- Agregar verificaciones post-actualización
- Agregar logging detallado para diagnóstico
- Posible flush() antes del commit para forzar escritura
