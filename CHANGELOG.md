# Changelog

## [1.1.0] - 2025-01-08

### Enfoque en Proyectos Aprobados con Detalles Completos

#### Cambios Principales

**Detección de Cambios**
- ⚠️ **BREAKING**: Solo se detecta la transición "En Calificación (Activo) → Aprobado"
- ❌ Eliminadas transiciones: "En Admisión → En Calificación" y wildcard "* → Aprobado"
- ℹ️ Los proyectos nuevos siguen siendo detectados pero NO se notifican

**Extracción de Detalles de Proyectos**
- ✅ Nuevo módulo `scraper_detail.py` para scrapear páginas individuales de proyectos
- ✅ Extracción automática de información detallada cuando un proyecto pasa a "Aprobado":
  - Tipo de proyecto
  - Monto de inversión
  - Descripción completa del proyecto
  - Titular (nombre, domicilio, ciudad, teléfono, email)
  - Representante Legal (nombre, domicilio, teléfono, email)
- ✅ Nueva tabla `project_details` en SQLite para almacenar información extendida
- ✅ Nuevo modelo `ProjectDetails` con todos los campos detallados

**Notificaciones Teams**
- ✅ Mensajes enriquecidos con información detallada de proyectos aprobados
- ✅ Formato mejorado con tipo, monto (destacado), descripción resumida y contactos
- ✅ Manejo inteligente de descripciones largas (truncado a 500 caracteres)

#### Componentes Nuevos
- `scraper_detail.py` - Scraper de páginas de detalle de proyectos
- `ProjectDetails` - Modelo de datos para información extendida
- Funciones en `storage.py`: `save_project_details()`, `get_project_details()`

#### Componentes Modificados
- `diff.py` - Solo transición a "Aprobado" desde "En Calificación"
- `runner.py` - Extracción automática de detalles en paso 3.5
- `notifier_teams.py` - Formato enriquecido con detalles
- `models.py` - Nuevo campo `details` en `ChangeEvent`
- `parser.py` - Mejora en construcción de URLs absolutas

#### Tests Actualizados
- `test_diff.py` - Ajustados para nueva lógica de transiciones
- `test_scraper_detail.py` - Nuevos tests para extracción de detalles

#### Documentación
- README.md actualizado con nuevo enfoque
- CHANGELOG.md con detalles de cambios

### Notas de Migración

Si tienes datos existentes:
1. La tabla `project_details` se creará automáticamente en la próxima ejecución
2. Solo los nuevos proyectos que pasen a "Aprobado" tendrán detalles extraídos
3. Las transiciones antiguas guardadas en el historial permanecen sin cambios

## [1.0.0] - 2025-01-08

### Inicial Release

Sistema completo de monitoreo SEIA implementado con todas las características:

#### Características Principales
- ✅ Scraping inteligente con fallback automático (requests → Playwright)
- ✅ Detección de proyectos nuevos (desde 01/01/2025)
- ✅ Detección de cambios de estado relevantes
- ✅ Notificaciones automáticas a Microsoft Teams
- ✅ Scheduler interno con timezone America/Santiago
- ✅ Persistencia en SQLite con historial completo
- ✅ CLI completo con Typer
- ✅ Tests con pytest

#### Componentes Implementados
- `config.py` - Sistema de configuración con validación
- `logger.py` - Logging con rotación automática
- `models.py` - Modelos de datos (dataclasses)
- `normalizer.py` - Normalización robusta de strings y estados
- `parser.py` - Parser HTML con fuzzy column matching
- `scraper_requests.py` - Scraper con requests (reintentos + backoff)
- `scraper_playwright.py` - Scraper con Playwright (fallback)
- `scraper.py` - Fachada AUTO que combina ambos scrapers
- `storage.py` - Capa de persistencia SQLite con transacciones
- `diff.py` - Motor de detección de cambios
- `notifier_teams.py` - Notificador de Microsoft Teams
- `runner.py` - Orquestador principal con manejo de errores
- `scheduler.py` - Scheduler interno (APScheduler)
- `cli.py` - Interfaz de línea de comandos

#### Robustez
- Manejo completo de errores y reintentos
- Prevención de corrupción de datos
- Validaciones antes de guardar
- Debug info guardado en caso de fallo
- Rate limiting y backoff exponencial
- Tolerante a cambios de HTML

#### Documentación
- README.md completo con decisiones técnicas
- INSTALL.md con guía de instalación paso a paso
- Tests completos con cobertura
- Comentarios en código

#### Tests
- `test_normalizer.py` - Tests de normalización
- `test_diff.py` - Tests de detección de cambios
- `test_parser.py` - Tests de parsing HTML
- Fixtures de muestra para testing

#### Comandos CLI Disponibles
- `run --once` - Ejecutar una vez
- `run --once --dry-run` - Modo prueba
- `schedule` - Scheduler interno
- `status` - Ver última corrida
- `test-teams` - Probar webhook
- `config-check` - Verificar configuración
- `version` - Ver versión

### Configuración por Defecto
- Scraping: Modo AUTO (requests con fallback a Playwright)
- Filtro temporal: Desde 01/01/2025
- Timezone: America/Santiago
- Hora de ejecución: 08:00
- Max páginas: 100
- Max proyectos: 10,000
- Timeout: 30s
- Rate limit: 2.5s entre páginas

### Transiciones Relevantes Monitoreadas
1. En Admisión → En Calificación (Activo)
2. En Calificación (Activo) → Aprobado
3. Cualquier estado → Aprobado

### Criterios de Aceptación Cumplidos
✅ Dos corridas seguidas sin cambios → 0 notificaciones  
✅ Transiciones relevantes detectadas y notificadas  
✅ Proyectos nuevos detectados correctamente  
✅ Historial completo guardado  
✅ Fallback automático requests → Playwright  
✅ Corridas con error no corrompen datos  
✅ Teams recibe mensajes formateados  
✅ CLI funciona correctamente  
✅ Logs informativos  
✅ Tests pasan  

### Notas Técnicas
- Python 3.10+ requerido
- SQLite para persistencia
- BeautifulSoup4 + lxml para parsing
- Playwright para scraping con navegador
- APScheduler para ejecución programada
- Typer + Rich para CLI

