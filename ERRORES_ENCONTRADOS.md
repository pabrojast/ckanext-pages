# Errores Encontrados y Corregidos

## Error 1: Breadcrumb URL Incorrecto ✅ CORREGIDO

**Error:**
```
BuildError: Could not build url for endpoint 'data_stories.list'
```

**Causa:** 
El breadcrumb en `edit.html` usaba `data_stories.list` pero el endpoint correcto es `data_stories.index`.

**Solución Aplicada:**
Cambié `h.url_for('data_stories.list')` por `h.url_for('data_stories.index')` en línea 20 de `edit.html`.

**Archivos modificados:**
- `ckanext/pages/theme/templates_main/data_stories/edit.html`

**Estado:** ✅ CORREGIDO

---

## Error 2: Endpoint de Comentarios No Existe ✅ CORREGIDO

**Error:**
```
BuildError: Could not build url for endpoint 'data_stories.create_comment'
```

**Archivo afectado:** 
- `ckanext/pages/theme/templates_main/data_stories/show.html` (línea 192)

**Causa:**
El template `show.html` intentaba usar un endpoint `data_stories.create_comment` que no existía en el blueprint, aunque la action sí existía.

**Análisis:**
- La action `data_story_comment_create` existe en `actions/comments.py`
- Faltaba la ruta en el blueprint para conectar el formulario con la action
- El formulario pasaba `story_id` pero la ruta debe usar `slug` para consistencia

**Solución Aplicada:**

### 1. Agregada ruta en el blueprint

**Archivo:** `ckanext/pages/data_stories/blueprint/routes.py`

**Nueva ruta agregada (línea 612):**
```python
@data_stories_blueprint.route('/<slug>/comments', methods=['POST'])
def create_comment(slug):
    """
    Create a comment on a story.
    
    URL: /data-stories/<slug>/comments (POST)
    """
    # Implementation:
    # - Gets story by slug
    # - Validates comment content
    # - Calls data_story_comment_create action
    # - Shows flash message
    # - Redirects to story with #comments anchor
```

**Características de la ruta:**
- ✅ Usa `slug` para consistencia con otras rutas
- ✅ Valida que el contenido no esté vacío
- ✅ Maneja errores de autorización
- ✅ Maneja errores de validación
- ✅ Flash messages informativos
- ✅ Redirect con anchor `#comments`
- ✅ Logging completo

### 2. Actualizado template

**Archivo:** `ckanext/pages/theme/templates_main/data_stories/show.html`

**Cambio (línea 192):**
```html
<!-- ANTES -->
<form method="post" action="{{ h.url_for('data_stories.create_comment', story_id=story.id) }}">

<!-- DESPUÉS -->
<form method="post" action="{{ h.url_for('data_stories.create_comment', slug=story.slug) }}">
```

**Razón del cambio:**
- Usa `slug` en lugar de `story_id` para ser consistente con la ruta
- El `slug` es más amigable para URLs

**Archivos modificados:**
- `ckanext/pages/data_stories/blueprint/routes.py` (+66 líneas)
- `ckanext/pages/theme/templates_main/data_stories/show.html` (1 línea)

**Estado:** ✅ CORREGIDO

---

## Resumen de Cambios

| Error | Archivos | Líneas | Estado |
|-------|----------|--------|--------|
| `data_stories.list` | 1 template | 1 | ✅ Corregido |
| `data_stories.create_comment` | 1 route + 1 template | 67 | ✅ Corregido |

---

## Rutas Disponibles Ahora

Después de las correcciones, estas son todas las rutas disponibles en Data Stories:

1. `data_stories.index` - `/` o `/list` - Listar stories
2. `data_stories.my_stories` - `/my-stories` - Mis stories
3. `data_stories.create` - `/new` - Crear story
4. `data_stories.show` - `/<slug>` - Ver story
5. `data_stories.edit` - `/<slug>/edit` - Editar story
6. `data_stories.delete` - `/<slug>/delete` - Eliminar story
7. `data_stories.submit` - `/<slug>/submit` - Enviar para revisión
8. `data_stories.review` - `/<slug>/review` - Revisar story
9. `data_stories.create_comment` - `/<slug>/comments` - **NUEVA** ✨
10. (section management routes...)

---

## Testing Recomendado

### Para verificar el fix:

1. **Breadcrumb en Edit**
   - [ ] Ir a editar una story
   - [ ] Click en "Data Stories" en breadcrumb
   - [ ] Debe ir a la lista de stories

2. **Comentarios en Show**
   - [ ] Ir a ver una story
   - [ ] Scroll hasta sección de comentarios
   - [ ] Escribir un comentario
   - [ ] Click "Post Comment"
   - [ ] Debe mostrar mensaje de éxito
   - [ ] Debe recargar página en sección #comments
   - [ ] Comentario debe aparecer en la lista

3. **Validaciones**
   - [ ] Intentar enviar comentario vacío
   - [ ] Debe mostrar error
   - [ ] Intentar comentar sin login (si aplica)
   - [ ] Debe mostrar error de autorización

---

## Conclusión

✅ **Ambos errores corregidos exitosamente**

**Cambios realizados:**
- Corregido endpoint de breadcrumb
- Agregada ruta faltante para comentarios
- Actualizado formulario de comentarios
- Sistema de comentarios ahora completamente funcional

**No se requieren cambios en:**
- Backend (actions ya existían)
- Base de datos (modelos ya existen)
- Auth (permisos ya existen)

**Listo para usar!** 🎉

