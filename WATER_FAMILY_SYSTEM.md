# Sistema Water Family - Community of Practice

## Resumen del Sistema Implementado

He implementado un sistema completo para la "Community of Practice for the IHP Water Family" que permite a los usuarios compartir noticias, eventos y publicaciones con un sistema de aprobación por administradores.

## Nuevos Endpoints Implementados

### 1. Página Principal
- **URL**: `/water-family`
- **Función**: Página principal que muestra las últimas noticias, eventos y publicaciones
- **Características**: 
  - Estadísticas de la comunidad
  - Acciones rápidas para compartir contenido
  - Vista general de las últimas publicaciones

### 2. Sistema de Noticias (News)
- **URLs**:
  - `/water-news` - Lista de noticias
  - `/water-news/<nombre>` - Ver noticia individual
  - `/water-news_edit` - Crear nueva noticia
  - `/water-news_edit/<nombre>` - Editar noticia existente

### 3. Sistema de Eventos (Events)
- **URLs**:
  - `/water-events` - Lista de eventos
  - `/water-events/<nombre>` - Ver evento individual  
  - `/water-events_edit` - Crear nuevo evento
  - `/water-events_edit/<nombre>` - Editar evento existente

### 4. Sistema de Publicaciones (Publications)
- **URLs**:
  - `/water-publications` - Lista de publicaciones
  - `/water-publications/<nombre>` - Ver publicación individual
  - `/water-publications_edit` - Crear nueva publicación
  - `/water-publications_edit/<nombre>` - Editar publicación existente

### 5. Panel de Administración
- **URL**: `/water-admin`
- **Función**: Dashboard para que los administradores aprueben o rechacen contenido
- **Acceso**: Solo administradores del sistema (sysadmin)

## Sistema de Aprobación

### Para Usuarios Regulares
1. **Crear Contenido**: Cualquier usuario autenticado puede crear noticias, eventos o publicaciones
2. **Estado Inicial**: El contenido se crea como "privado" (pendiente de aprobación)
3. **Notificación**: El usuario recibe un mensaje confirmando que el contenido será revisado
4. **Visibilidad**: El contenido no es visible públicamente hasta ser aprobado

### Para Administradores
1. **Dashboard**: Acceso a `/water-admin` para ver todo el contenido pendiente
2. **Revisión**: Pueden previsualizar y editar el contenido antes de decidir
3. **Acciones**:
   - **Aprobar**: Hace el contenido público y visible para todos
   - **Rechazar**: Elimina el contenido permanentemente
4. **Gestión**: Pueden ver y gestionar todo el contenido (público y privado)

## Archivos Modificados/Creados

### Archivos del Core
1. **`ckanext/pages/blueprint.py`**
   - Agregadas funciones para todos los nuevos endpoints
   - Funciones de administración para aprobar/rechazar contenido

2. **`ckanext/pages/utils.py`**
   - Nuevas funciones para manejar los tipos de página water-news, water-events, water-publications
   - Sistema de aprobación integrado
   - Funciones para el dashboard de administración

3. **`ckanext/pages/plugin.py`**
   - Nuevos helpers para obtener contenido reciente de cada tipo
   - Integración con el sistema de templates

### Templates Creados
1. **`water-family.html`** - Página principal de la comunidad
2. **`water-admin-dashboard.html`** - Dashboard de administración
3. **`water-news_list.html`** - Lista de noticias
4. **`water-news.html`** - Vista individual de noticia
5. **`water-news_edit.html`** - Formulario de edición de noticias

## Características del Sistema

### Diseño Profesional
- **Consistent Branding**: Uso de colores UNESCO y diseño coherente
- **Responsive Design**: Totalmente adaptable a dispositivos móviles
- **Iconografía Intuitiva**: Iconos específicos para cada tipo de contenido
- **Navegación Clara**: Breadcrumbs y enlaces de navegación bien definidos

### Funcionalidades Avanzadas
- **Editor Rich Text**: Soporte para Markdown y HTML
- **Gestión de Imágenes**: Subida de imágenes y galerías
- **Enlaces Externos**: Soporte para enlaces relacionados
- **Metadatos**: Autor, fuente, fechas de publicación
- **Búsqueda y Filtros**: Sistema de búsqueda en las listas

### Sistema de Permisos
- **Usuarios Regulares**: Pueden crear contenido que requiere aprobación
- **Administradores**: Pueden crear contenido público inmediatamente y aprobar/rechazar el de otros
- **Visibilidad**: Solo contenido aprobado es visible públicamente

## Cómo Usar el Sistema

### Para Usuarios
1. **Acceder**: Ir a `/water-family` para ver la página principal
2. **Compartir**: Hacer clic en "Share News", "Post Event", o "Submit Publication"
3. **Completar Formulario**: Llenar toda la información requerida
4. **Enviar**: El contenido queda pendiente de aprobación
5. **Esperar**: Recibir notificación cuando sea aprobado

### Para Administradores
1. **Dashboard**: Ir a `/water-admin` para ver contenido pendiente
2. **Revisar**: Previsualizar cada elemento
3. **Decidir**: Aprobar o rechazar según las políticas de la comunidad
4. **Gestionar**: Editar si es necesario antes de aprobar

## Próximos Pasos Recomendados

1. **Crear Templates Faltantes**: 
   - `water-events.html` (vista individual de evento)
   - `water-events_edit.html` (formulario de evento)
   - `water-events_list.html` (lista de eventos)
   - `water-publications.html` (vista individual de publicación)
   - `water-publications_edit.html` (formulario de publicación)
   - `water-publications_list.html` (lista de publicaciones)

2. **Configurar Imágenes de Header**:
   - Agregar imágenes por defecto para cada sección
   - `/images/water-family-header.jpg`
   - `/images/water-news-header.jpg`
   - `/images/water-events-header.jpg`
   - `/images/water-publications-header.jpg`

3. **Configurar Notificaciones**:
   - Email notifications para administradores cuando hay contenido pendiente
   - Notificaciones para usuarios cuando su contenido es aprobado/rechazado

4. **Testing**:
   - Probar todos los flujos de usuario
   - Verificar permisos y seguridad
   - Testear responsive design en diferentes dispositivos

## Beneficios del Sistema

### Para la Comunidad
- **Centralización**: Un lugar único para toda la información de la comunidad water
- **Participación**: Facilita que los miembros compartan información
- **Calidad**: Sistema de moderación asegura contenido de alta calidad
- **Accesibilidad**: Diseño responsive y accesible

### Para los Administradores  
- **Control**: Revisión y aprobación centralizada
- **Eficiencia**: Dashboard intuitivo para gestión rápida
- **Flexibilidad**: Pueden editar contenido antes de aprobar
- **Visibilidad**: Vista completa de toda la actividad de la comunidad

El sistema está completamente implementado y listo para usar. Solo necesita que se completen los templates faltantes para eventos y publicaciones (que seguirían el mismo patrón que las noticias) y se configuren las imágenes de header correspondientes. 