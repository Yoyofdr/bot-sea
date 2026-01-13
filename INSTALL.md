# Guía de Instalación Rápida - SEIA Monitor

## 🚀 Setup Automático (Recomendado)

### Linux/macOS

```bash
# Hacer el script ejecutable
chmod +x setup.sh

# Ejecutar
./setup.sh
```

### Windows

```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar Playwright
playwright install chromium

# Copiar .env
copy .env.example .env

# Editar .env con tu configuración
notepad .env
```

## 📝 Configuración del Webhook de Teams

### Paso 1: Crear Webhook en Teams

1. Abre Microsoft Teams
2. Ve al canal donde quieres recibir notificaciones
3. Click en `•••` (más opciones) junto al nombre del canal
4. Selecciona "Conectores" o "Connectors"
5. Busca "Incoming Webhook"
6. Click en "Configurar" o "Configure"
7. Dale un nombre: "SEIA Monitor"
8. Click en "Crear"
9. **Copia la URL completa** que aparece

### Paso 2: Configurar .env

Edita el archivo `.env`:

```bash
# En Linux/macOS
nano .env

# En Windows
notepad .env
```

Pega tu webhook URL:

```env
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/TU_URL_AQUI
```

Guarda el archivo.

### Paso 3: Probar

```bash
python -m seia_monitor test-teams
```

Si funciona, deberías ver un mensaje de prueba en Teams.

## ✅ Verificación

### 1. Verificar configuración

```bash
python -m seia_monitor config-check
```

### 2. Ejecutar en modo dry-run

```bash
python -m seia_monitor run --once --dry-run --verbose
```

Esto ejecutará el sistema sin guardar ni notificar, útil para verificar que todo funciona.

### 3. Primera ejecución real

```bash
python -m seia_monitor run --once
```

### 4. Ver estado

```bash
python -m seia_monitor status
```

## 🔄 Ejecución Automática

### Opción 1: Scheduler Interno

```bash
python -m seia_monitor schedule
```

El proceso quedará corriendo. Para detener: `Ctrl+C`

### Opción 2: Cron (Linux/macOS)

```bash
# Editar crontab
crontab -e

# Agregar línea (ajustar rutas):
0 8 * * * cd /ruta/completa/Proyecto\ SEA && /ruta/completa/venv/bin/python -m seia_monitor run --once >> logs/cron.log 2>&1
```

### Opción 3: Task Scheduler (Windows)

1. Abre "Programador de tareas"
2. Click en "Crear tarea básica"
3. Nombre: "SEIA Monitor"
4. Desencadenador: Diariamente a las 08:00
5. Acción: Iniciar programa
   - Programa: `C:\ruta\completa\venv\Scripts\python.exe`
   - Argumentos: `-m seia_monitor run --once`
   - Iniciar en: `C:\ruta\completa\Proyecto SEA`

## 🆘 Problemas Comunes

### "No module named 'seia_monitor'"

Asegúrate de:
1. Estar en el directorio correcto: `cd /ruta/a/Proyecto\ SEA`
2. Tener el entorno virtual activado: `source venv/bin/activate`

### "playwright._impl._api_types.Error: Executable doesn't exist"

```bash
playwright install chromium
```

### Webhook no funciona

1. Verifica que la URL esté completa en `.env`
2. Verifica que no tenga espacios ni saltos de línea
3. Regenera el webhook en Teams si es necesario

### Scraping retorna 0 proyectos

1. Verifica la fecha en `.env`: `FECHA_DESDE=01/01/2025`
2. Intenta con Playwright forzado: `SCRAPE_MODE=playwright`
3. Ejecuta en verbose: `python -m seia_monitor run --once --dry-run --verbose`
4. Revisa logs: `tail -f logs/seia_monitor.log`

## 📚 Más Información

Ver [README.md](README.md) para documentación completa.


