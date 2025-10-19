# Correcciones Implementadas para Open Source Admin

## Fecha: 2025-10-19

## Problemas Solucionados

### 1. Cambio de Organización no se Aplica
**Problema**: Cuando se cambiaba la organización de una entrada en el panel de administración de open source, el servidor no daba error pero la organización no se reasignaba.

**Causa**: Falta de commit explícito y verificación post-actualización en la transacción de base de datos.

**Solución Implementada**:
- Agregado `model.Session.flush()` y `model.Session.commit()` explícitos después de la actualización
- Agregado logging detallado para rastrear el proceso de actualización
- Agregado verificación post-actualización para confirmar que el cambio se guardó
- Agregado manejo de errores con rollback en caso de fallo
- Agregado mensajes de error informativos si la verificación falla

**Archivos Modificados**:
- `ckanext/pages/utils.py` - función `open_source_admin_change_org()` (líneas ~1357-1410)

**Cambios Específicos**:
```python
# Antes del cambio:
tk.get_action('ckanext_pages_update')(...)
tk.h.flash_success(...)

# Después del cambio:
tk.get_action('ckanext_pages_update')(...)
model.Session.flush()
model.Session.commit()
verified_page = tk.get_action('ckanext_pages_show')(...)
if verified_page.get('ihp_organization') != new_organization:
    log.error(...)
    tk.h.flash_error(...)
else:
    tk.h.flash_success(...)
```

### 2. Entrada Aprobada no se Muestra a Usuarios No Registrados
**Problema**: Cuando se aprobaba una entrada en el panel de administración, desaparecía del panel (comportamiento correcto), pero no se mostraba a usuarios no registrados en la lista pública de `/open-source-software`.

**Causa**: Falta de commit explícito después de actualizar `submission_status` y `private`, lo que podía causar que la transacción no se confirmara correctamente.

**Solución Implementada**:
- Agregado `model.Session.flush()` y `model.Session.commit()` explícitos después de la aprobación
- Agregado logging detallado para rastrear el estado antes y después de la aprobación
- Agregado verificación post-aprobación para confirmar que los campos se guardaron correctamente
- Agregado manejo de errores con rollback en caso de fallo
- Agregado mensajes de error informativos si la verificación falla

**Archivos Modificados**:
- `ckanext/pages/utils.py` - función `open_source_admin_approve()` (líneas ~1246-1293)

**Cambios Específicos**:
```python
# Antes del cambio:
tk.get_action('ckanext_pages_update')(...)
tk.h.flash_success(...)

# Después del cambio:
tk.get_action('ckanext_pages_update')(...)
model.Session.flush()
model.Session.commit()
verified_page = tk.get_action('ckanext_pages_show')(...)
if verified_page.get('submission_status') != 'approved' or verified_page.get('private') != False:
    log.error(...)
    tk.h.flash_error(...)
else:
    tk.h.flash_success(...)
```

## Mejoras Adicionales Implementadas

### 3. Logging Detallado para Diagnóstico
Agregado logging comprehensivo en múltiples puntos críticos del código para facilitar el diagnóstico de problemas futuros:

**Archivos Modificados**:
- `ckanext/pages/utils.py`:
  - Agregado import de `logging`
  - Agregado logging en `open_source_admin_approve()` y `open_source_admin_change_org()`
  
- `ckanext/pages/actions.py`:
  - Agregado logging en `_pages_update()` para campos críticos (submission_status, ihp_organization, private)
  - Agregado logging en `_pages_list()` para filtros aplicados y resultados
  
- `ckanext/pages/db.py`:
  - Agregado logging en `Page.pages()` para filtro de submission_status

**Puntos de Logging Agregados**:
1. Estado antes de actualizar (cambio de org / aprobación)
2. Intento de actualización con valores específicos
3. Estado después de actualizar (verificación)
4. Parámetros de filtrado en listado de páginas
5. Cantidad de resultados devueltos por queries
6. Configuración de campos críticos en `_pages_update()`
7. Estado final después de guardar en base de datos

### 4. Manejo Robusto de Errores
Implementado manejo de errores más robusto con:
- Try-except con logging detallado (incluyendo stack traces con `exc_info=True`)
- Rollback explícito de la sesión en caso de error
- Mensajes de error informativos para el usuario

## Flujo de Verificación Implementado

### Para Cambio de Organización:
1. Admin selecciona nueva organización y hace clic en "Set Organization"
2. Sistema obtiene la página actual
3. Sistema registra el estado actual en logs
4. Sistema actualiza `ihp_organization` con el nuevo valor
5. Sistema llama `ckanext_pages_update()` con `ignore_auth=True`
6. Sistema ejecuta `flush()` para forzar escritura a BD
7. Sistema ejecuta `commit()` para confirmar transacción
8. Sistema vuelve a obtener la página para verificar
9. Sistema compara el valor guardado con el esperado
10. Sistema muestra mensaje de éxito o error según verificación

### Para Aprobación de Entrada:
1. Admin hace clic en "Approve & Publish"
2. Sistema obtiene la página actual
3. Sistema registra el estado actual en logs
4. Sistema actualiza:
   - `submission_status = 'approved'`
   - `private = False`
   - `reviewed_at`, `reviewed_by`, `publish_date`, etc.
5. Sistema llama `ckanext_pages_update()` con `ignore_auth=True`
6. Sistema ejecuta `flush()` para forzar escritura a BD
7. Sistema ejecuta `commit()` para confirmar transacción
8. Sistema vuelve a obtener la página para verificar
9. Sistema compara los valores guardados con los esperados
10. Sistema muestra mensaje de éxito o error según verificación

## Cómo Verificar las Correcciones

### Test Manual - Cambio de Organización:
1. Acceder como sysadmin a `/open-source-admin`
2. Encontrar una entrada pendiente
3. Seleccionar una organización diferente del dropdown
4. Hacer clic en "Set Organization"
5. Verificar mensaje de éxito
6. Refrescar la página y verificar que la organización se muestra correctamente
7. Revisar logs del servidor para confirmar el flujo completo

### Test Manual - Aprobación:
1. Acceder como sysadmin a `/open-source-admin`
2. Encontrar una entrada pendiente
3. Hacer clic en "Approve & Publish"
4. Verificar mensaje de éxito
5. Verificar que la entrada desaparece del panel de admin
6. Abrir navegador en modo incógnito (sin login)
7. Acceder a `/open-source-software`
8. Verificar que la entrada aprobada aparece en la lista pública
9. Revisar logs del servidor para confirmar el flujo completo

### Revisión de Logs:
Buscar en los logs del servidor las siguientes líneas para cada operación:

**Para cambio de organización**:
```
[CHANGE_ORG] Before change - page: <name>, current_org: <old>, new_org: <new>
[CHANGE_ORG] Attempting to update ihp_organization to: <new>
[PAGES_UPDATE] Setting 'ihp_organization' attribute: <new>
[PAGES_UPDATE] Final state - submission_status: ..., private: ..., ihp_organization: <new>
[CHANGE_ORG] After change - ihp_organization: <new>
```

**Para aprobación**:
```
[APPROVE] Before approval - page: <name>, submission_status: pending, private: True
[APPROVE] Attempting to update - submission_status: approved, private: False
[PAGES_UPDATE] Setting 'submission_status' attribute: approved
[PAGES_UPDATE] Setting 'private' attribute: False
[PAGES_UPDATE] Final state - submission_status: approved, private: False, ihp_organization: ...
[APPROVE] After approval - submission_status: approved, private: False
```

**Para listado público**:
```
[PAGES_LIST] Filtering open-source-software - private: False, submission_status: approved
[PAGES_LIST] Executing query with search params: {'page_type': 'open-source-software', 'private': False, 'submission_status': 'approved', ...}
[DB.PAGES] Filtering by submission_status: approved
[PAGES_LIST] Query returned X results for open-source-software
```

## Notas Técnicas

### Campos Críticos en Base de Datos
Los siguientes campos son columnas directas en la tabla `ckanext_pages` (NO en JSON extras):
- `submission_status` - Estado de la submisión ('draft', 'pending', 'approved', 'rejected')
- `ihp_organization` - ID de la organización IHP WINS
- `private` - Si es visible públicamente (True/False)
- `reviewed_at` - Fecha/hora de revisión
- `reviewed_by` - Usuario que revisó

Estos campos se procesan en `_pages_update()` en la lista `items` (líneas 256-258 de actions.py).

### Filtrado para Usuarios No Registrados
Cuando un usuario no autenticado visita `/open-source-software`:
1. Se llama `pages_list_pages('open-source-software')` (utils.py línea 90)
2. Se detecta que el usuario no es sysadmin (línea 129-132)
3. Se aplican filtros: `private = False` y `submission_status = 'approved'` (líneas 132-138)
4. Se llama `_pages_list()` que pasa estos filtros a `db.Page.pages()`
5. La query SQL filtra por ambos campos para retornar solo entradas aprobadas y públicas

### Transacciones de Base de Datos
CKAN usa SQLAlchemy con transacciones automáticas, pero en algunos casos es necesario:
- `flush()` - Fuerza escritura a BD sin confirmar transacción
- `commit()` - Confirma la transacción y hace cambios permanentes
- `rollback()` - Deshace cambios en caso de error

Las correcciones implementadas usan ambos `flush()` y `commit()` para asegurar que los cambios se persistan correctamente.

## Archivos Modificados - Resumen

1. **ckanext/pages/utils.py**:
   - Agregado import de `logging`
   - Modificado `open_source_admin_approve()` con flush/commit y verificación
   - Modificado `open_source_admin_change_org()` con flush/commit y verificación

2. **ckanext/pages/actions.py**:
   - Agregado logging en `_pages_list()` para diagnóstico de filtros
   - Agregado logging en `_pages_update()` para campos críticos
   - Agregado logging del estado final después de guardar

3. **ckanext/pages/db.py**:
   - Agregado logging en `Page.pages()` para filtro de submission_status

## Compatibilidad

Las correcciones son compatibles con:
- Python 3.9-3.10
- CKAN 2.9+
- Versiones existentes de la base de datos (no requiere migración)

No se han realizado cambios que rompan compatibilidad hacia atrás.

## Próximos Pasos Recomendados

1. **Testing Inmediato**:
   - Probar cambio de organización en el panel de admin
   - Probar aprobación de entrada
   - Verificar visibilidad pública de entrada aprobada

2. **Monitoreo**:
   - Revisar logs del servidor para confirmar que no hay errores
   - Verificar que los mensajes de logging aparecen correctamente

3. **Si los Problemas Persisten**:
   - Revisar logs detallados para identificar dónde falla el proceso
   - Verificar permisos de base de datos
   - Verificar configuración de SQLAlchemy en CKAN
   - Considerar agregar tests unitarios para estos casos

4. **Mejoras Futuras** (opcionales):
   - Crear tests unitarios para `open_source_admin_approve()` y `open_source_admin_change_org()`
   - Agregar tests de integración para el flujo completo
   - Considerar agregar caché invalidation después de aprobar
   - Considerar agregar notificaciones por email al usuario cuando se aprueba su entrada

## Contacto para Soporte

Si los problemas persisten después de implementar estas correcciones:
1. Revisar los logs del servidor con los mensajes de diagnóstico agregados
2. Verificar el estado de la base de datos directamente con SQL
3. Verificar que no hay bloqueos o problemas de concurrencia en la BD
4. Considerar aumentar el nivel de logging a DEBUG temporalmente para más detalles
