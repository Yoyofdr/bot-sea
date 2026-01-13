# Sistema de Monitoreo SEIA (Chile)

Sistema profesional y robusto en Python para monitorear diariamente la página oficial del SEIA (Sistema de Evaluación de Impacto Ambiental de Chile), detectando nuevos proyectos aprobados.

## 📋 Descripción

Este sistema automatiza el monitoreo del [SEIA](https://seia.sea.gob.cl/busqueda/buscarProyectoResumen.php) para:

- **Monitorear proyectos con estado "Aprobado"** (los 100 más recientes)
- **Detectar nuevos proyectos aprobados** que aparecen en la lista
- **Extraer información detallada** de proyectos aprobados:
  - Nombre, titular, región y tipo de proyecto
  - Monto de inversión y fecha de presentación
  - Estado y días transcurridos
- **Notificar automáticamente** a Microsoft Teams sobre nuevos proyectos aprobados
- **Ejecutarse automáticamente** una vez al día a una hora fija
- **Mantener historial completo** de todos los proyectos detectados

## 🎯 Características Principales

### Robustez en Producción

✅ **Scraping inteligente con fallback automático**
- Intenta primero con `requests` (rápido y eficiente)
- Si falla, automáticamente usa Playwright (navegador real)
- Maneja anti-bot, rate limiting y errores intermitentes

✅ **Tolerante a cambios de HTML**
- Fuzzy matching de columnas (no depende de índices fijos)
- Detecta tablas con múltiples selectores
- Si falta una columna, continúa con warnings

✅ **Prevención de corrupción de datos**
- No sobrescribe el snapshot si el scraping falla
- Valida que los resultados sean razonables
- Transacciones atómicas en SQLite

✅ **Identificador estable de proyectos**
- Extrae ID oficial desde URL de detalle (ej: `id_expediente=12345`)
- Fallback a hash SHA256 de campos duros (nombre + región + titular + fecha)
- Nunca usa la posición en tabla como ID

✅ **Manejo completo de errores**
- Reintentos con backoff exponencial
- Guardar HTML/screenshots de error para debugging
- Logs detallados con rotación automática

## 🏗️ Decisiones Técnicas Clave

### 1. Identificador de Proyecto

**Estrategia de dos niveles:**

1. **Prioridad 1**: Extraer ID desde URL de detalle
   ```python
   # Ejemplo: https://seia.sea.gob.cl/expediente/ficha.php?id_expediente=12345
   # → project_id = "seia_12345"
   ```

2. **Fallback**: Generar hash estable
   ```python
   # Hash SHA256 de: {nombre_normalizado}|{region}|{titular}|{fecha_ingreso}
   # → project_id = "hash_a1b2c3d4e5f6g7h8"
   ```

**Justificación**: El ID oficial es ideal cuando está disponible. El hash asegura estabilidad incluso si la página cambia.

### 2. Scraping AUTO (requests + Playwright)

**Modo AUTO (recomendado):**

```
┌─────────────────┐
│  Modo AUTO      │
└────────┬────────┘
         │
         ├─► Intenta requests (POST form)
         │   ├─► ✓ Éxito → Retorna proyectos
         │   └─► ✗ Falla → Continúa
         │
         └─► Fallback a Playwright
             ├─► Navega como navegador real
             └─► Llena formulario y extrae datos
```

**Justificación**: Maximiza velocidad (requests es ~10x más rápido) pero garantiza éxito con Playwright como respaldo.

### 3. Normalización de Estados

Todos los estados se normalizan antes de comparar:

```python
"En Admisión"              → "en_admision"
"EN CALIFICACIÓN (ACTIVO)" → "en_calificacion_activo"
"Aprobado"                 → "aprobado"
```

**Justificación**: Evita falsos positivos por diferencias de mayúsculas, tildes o espacios.

### 4. Estrategia de Monitoreo Simplificada

Monitorea directamente los **100 proyectos aprobados más recientes** (primera página del listado).

**Justificación**: Enfoque en proyectos recién aprobados, evitando complejidad de detectar cambios de estado.

## 📦 Instalación

### Requisitos

- Python 3.10 o superior
- pip o poetry

### Pasos

1. **Clonar el repositorio**
   ```bash
   cd /path/to/Proyecto\ SEA
   ```

2. **Crear entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Instalar navegador para Playwright**
   ```bash
   playwright install chromium
   ```

5. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tu configuración
   ```

## ⚙️ Configuración

### Variables de Entorno (.env)

Edita el archivo `.env` con tus valores:

```env
# SEIA Configuration
SEIA_BASE_URL=https://seia.sea.gob.cl/busqueda/buscarProyectoResumen.php
SCRAPE_MODE=auto  # auto|requests|playwright

# Teams Notification
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/YOUR_WEBHOOK_HERE

# Database
DB_PATH=data/seia_monitor.db

# Scraping Config
REQUEST_TIMEOUT=30
PLAYWRIGHT_HEADLESS=true
MAX_PAGES=1  # Solo primera página (100 proyectos aprobados más recientes)
MAX_PROJECTS_PER_RUN=10000

# Scheduler
TIMEZONE=America/Santiago
SCHEDULE_TIME=08:00

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/seia_monitor.log
```

### Configurar Webhook de Microsoft Teams

1. **Abrir Teams** → Ir al canal donde quieres recibir notificaciones

2. **Agregar conector**:
   - Click en `•••` (más opciones) del canal
   - Seleccionar "Conectores" o "Connectors"
   - Buscar "Incoming Webhook"
   - Click en "Configurar"

3. **Configurar el webhook**:
   - Dar un nombre: "SEIA Monitor"
   - Opcionalmente, subir una imagen
   - Click en "Crear"

4. **Copiar la URL**:
   - Se mostrará una URL larga que empieza con `https://outlook.office.com/webhook/...`
   - Copiar esta URL completa

5. **Pegar en .env**:
   ```env
   TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/[TU_URL_AQUI]
   ```

6. **Probar**:
   ```bash
   python -m seia_monitor test-teams
   ```

## 🚀 Uso

### Comandos Disponibles

```bash
# Ver todos los comandos
python -m seia_monitor --help

# Ejecutar una vez
python -m seia_monitor run --once

# Ejecutar en modo dry-run (sin guardar ni notificar)
python -m seia_monitor run --once --dry-run

# Modo verbose (debug)
python -m seia_monitor run --once --verbose

# Iniciar scheduler (ejecución continua)
python -m seia_monitor schedule

# Personalizar hora del scheduler
python -m seia_monitor schedule --time "09:30"

# Ver estado de la última corrida
python -m seia_monitor status

# Probar webhook de Teams
python -m seia_monitor test-teams

# Verificar configuración
python -m seia_monitor config-check
```

### Ejecución Manual (una vez)

```bash
python -m seia_monitor run --once
```

Esto ejecutará:
1. Scraping del SEIA (proyectos desde 01/01/2025)
2. Comparación con snapshot anterior
3. Detección de nuevos y cambios de estado
4. Guardado en base de datos
5. Notificación a Teams (si hay cambios)

### Ejecución Programada (Scheduler Interno)

**Opción 1: Scheduler interno** (el programa corre 24/7)

```bash
python -m seia_monitor schedule
```

El proceso quedará corriendo y ejecutará el monitoreo automáticamente a la hora configurada (default: 08:00).

Para detener: `Ctrl+C`

**Opción 2: Cron externo** (recomendado para servidores)

Editar crontab:
```bash
crontab -e
```

Agregar línea:
```bash
# Ejecutar todos los días a las 08:00 (hora Chile)
0 8 * * * cd /path/to/Proyecto\ SEA && /path/to/venv/bin/python -m seia_monitor run --once >> logs/cron.log 2>&1
```

**En Windows (Task Scheduler):**

1. Abrir "Programador de tareas"
2. Crear tarea básica
3. Nombre: "SEIA Monitor"
4. Desencadenador: Diariamente a las 08:00
5. Acción: Iniciar programa
   - Programa: `C:\path\to\venv\Scripts\python.exe`
   - Argumentos: `-m seia_monitor run --once`
   - Directorio: `C:\path\to\Proyecto SEA`

## 🔍 Monitoreo

### Ver Logs

```bash
# Ver logs en tiempo real
tail -f logs/seia_monitor.log

# Ver últimas 50 líneas
tail -50 logs/seia_monitor.log

# Buscar errores
grep ERROR logs/seia_monitor.log
```

### Ver Estadísticas

```bash
python -m seia_monitor status
```

Muestra:
- Estado de la última corrida (exitosa/fallida)
- Fecha y hora
- Duración
- Cantidad de proyectos
- Nuevos y cambios detectados
- Errores (si los hubo)

### Base de Datos

La base de datos SQLite se encuentra en `data/seia_monitor.db`.

**Tablas principales:**
- `projects_current`: Snapshot actual de proyectos
- `project_history`: Historial completo de cambios de estado
- `runs`: Estadísticas de cada corrida

**Consultar con SQL:**
```bash
sqlite3 data/seia_monitor.db

# Ver últimas corridas
SELECT * FROM runs ORDER BY timestamp DESC LIMIT 5;

# Ver proyectos nuevos
SELECT * FROM projects_current ORDER BY first_seen DESC LIMIT 10;

# Ver historial de cambios relevantes
SELECT * FROM project_history WHERE is_relevant = 1 ORDER BY timestamp DESC;
```

## 🛠️ Qué Pasa Si Falla

### Escenarios y Recuperación

#### 1. Scraping falla (timeout, 403, cambios HTML)

**Qué pasa:**
- Si modo=`auto`: Automáticamente intenta con Playwright
- Se guarda HTML/screenshot en `data/debug/` para análisis
- Se registra error en logs y tabla `runs`
- **NO se sobrescribe** el snapshot anterior

**Recuperación:**
```bash
# Ver último error
python -m seia_monitor status

# Revisar HTML de debug
ls -lt data/debug/

# Intentar manualmente con Playwright
# Editar .env: SCRAPE_MODE=playwright
python -m seia_monitor run --once --dry-run
```

#### 2. Base de datos corrupta o bloqueada

**Qué pasa:**
- Error al guardar proyectos
- Corrida se marca como fallida
- Datos anteriores NO se pierden

**Recuperación:**
```bash
# Verificar integridad
sqlite3 data/seia_monitor.db "PRAGMA integrity_check;"

# Si está corrupta, restaurar desde backup (si existe)
cp data/seia_monitor.db.backup data/seia_monitor.db

# O eliminar y empezar de cero
rm data/seia_monitor.db
python -m seia_monitor run --once
```

#### 3. Teams no recibe notificaciones

**Qué pasa:**
- Corrida continúa exitosamente
- Error se registra en logs
- Datos sí se guardan

**Recuperación:**
```bash
# Probar webhook
python -m seia_monitor test-teams

# Si falla, regenerar webhook en Teams
# Y actualizar .env con nueva URL
```

#### 4. Proceso scheduler se detiene

**Qué pasa:**
- No hay ejecuciones automáticas
- Última corrida queda registrada

**Recuperación:**
```bash
# Verificar si está corriendo
ps aux | grep seia_monitor

# Reiniciar scheduler
python -m seia_monitor schedule

# O ejecutar manualmente
python -m seia_monitor run --once
```

## 🧪 Tests

Ejecutar tests:

```bash
# Todos los tests
pytest

# Con coverage
pytest --cov=seia_monitor --cov-report=html

# Tests específicos
pytest tests/test_normalizer.py
pytest tests/test_diff.py -v
```

## 📁 Estructura del Proyecto

```
Proyecto SEA/
├── seia_monitor/           # Código fuente
│   ├── __init__.py
│   ├── __main__.py         # Punto de entrada
│   ├── config.py           # Configuración
│   ├── logger.py           # Sistema de logs
│   ├── models.py           # Modelos de datos
│   ├── normalizer.py       # Normalización de strings
│   ├── parser.py           # Parser HTML con fuzzy matching
│   ├── scraper_requests.py # Scraper con requests
│   ├── scraper_playwright.py # Scraper con Playwright
│   ├── scraper.py          # Fachada AUTO
│   ├── storage.py          # Capa de persistencia SQLite
│   ├── diff.py             # Motor de detección de cambios
│   ├── notifier_teams.py   # Notificador Teams
│   ├── runner.py           # Orquestador principal
│   ├── scheduler.py        # Scheduler interno
│   └── cli.py              # CLI con Typer
├── tests/                  # Tests con pytest
│   ├── test_normalizer.py
│   ├── test_diff.py
│   ├── test_parser.py
│   └── fixtures/
│       └── sample_html.html
├── data/                   # Datos (gitignored)
│   ├── seia_monitor.db     # Base de datos SQLite
│   └── debug/              # HTML/screenshots de errores
├── logs/                   # Logs (gitignored)
│   └── seia_monitor.log
├── .env                    # Variables de entorno (gitignored)
├── .env.example            # Plantilla de configuración
├── .gitignore
├── requirements.txt        # Dependencias
├── pyproject.toml          # Poetry config
└── README.md
```

## 🔒 Seguridad

- **No hacer commit de `.env`**: Contiene el webhook URL (secreto)
- **Webhook URL**: Cualquiera con la URL puede enviar mensajes al canal
- **Base de datos**: No contiene información sensible, pero mantener en privado
- **Logs**: Pueden contener URLs, revisar antes de compartir

## 🐛 Troubleshooting

### Error: "No module named 'seia_monitor'"

```bash
# Asegúrate de estar en el directorio correcto
cd /path/to/Proyecto\ SEA

# Y que el entorno virtual esté activado
source venv/bin/activate
```

### Error: "playwright._impl._api_types.Error: Executable doesn't exist"

```bash
# Instalar navegador de Playwright
playwright install chromium
```

### Scraping retorna 0 proyectos

```bash
# Verificar configuración
python -m seia_monitor config-check

# Intentar con dry-run verbose
python -m seia_monitor run --once --dry-run --verbose

# Ver HTML de debug
ls -lt data/debug/
```

### Teams no recibe mensajes

```bash
# Probar webhook
python -m seia_monitor test-teams

# Verificar que la URL en .env sea correcta
cat .env | grep TEAMS_WEBHOOK_URL

# Verificar en Teams que el webhook esté activo
```

## 📝 Criterios de Aceptación (Checklist)

✅ Dos corridas seguidas sin cambios → 0 notificaciones  
✅ Transición "En Admisión → En Calificación" detectada y notificada  
✅ Transición "En Calificación → Aprobado" detectada y notificada  
✅ Proyecto nuevo detectado correctamente  
✅ Historial completo guardado en `project_history`  
✅ Requests falla → Playwright funciona automáticamente  
✅ Corrida con error NO sobrescribe `projects_current`  
✅ Teams recibe mensaje formateado correctamente  
✅ CLI funciona con `--once` y `--dry-run`  
✅ Logs informativos con nivel configurable  
✅ Tests pasan con pytest  

## 📄 Licencia

[Especificar licencia según necesidad]

## 👥 Autor

[Tu nombre/organización]

## 🤝 Contribuir

[Instrucciones si aplica]

---

**¿Preguntas o problemas?** Revisar logs en `logs/seia_monitor.log` o contactar [email/contacto]

