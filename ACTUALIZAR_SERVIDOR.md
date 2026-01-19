# 🚀 Actualizar Servidor con Notificaciones por Email

## Resumen de Cambios

El sistema ahora usa la **API de Bye.cl** para enviar emails en lugar de SMTP. Ya no necesita conectarse a servidores internos.

## ⚙️ Pasos para Actualizar

### 1. Conectar al Servidor

```bash
ssh root@159.203.19.75
# Usar la contraseña: 07&!_p2Dh7jS
```

### 2. Navegar al Directorio del Proyecto

```bash
cd ~/seia-monitor
```

### 3. Actualizar el Código desde GitHub

```bash
git pull origin main
```

### 4. Actualizar el Archivo .env

Editar el archivo `.env` con las nuevas variables:

```bash
nano .env
```

**Reemplazar todo el contenido con:**

```env
# ==============================================================================
# CONFIGURACIÓN SEIA MONITOR
# ==============================================================================

# URL base del sistema SEIA
SEIA_BASE_URL=https://seia.sea.gob.cl/busqueda/buscarProyectoResumen.php

# Modo de scraping: auto|requests|playwright
SCRAPE_MODE=auto

# ==============================================================================
# EMAIL NOTIFICATIONS (Bye.cl API)
# ==============================================================================

# Habilitar notificaciones por email
EMAIL_ENABLED=true

# Base URL de la API de Bye.cl
EMAIL_API_BASE_URL=https://app.bye.cl/api

# Credenciales de API
EMAIL_API_USER=usertech@bye.cl
EMAIL_API_PASSWORD=user$T26.#

# Destinatarios (separados por comas)
EMAIL_TO=rfernandezdelrio@bye.cl,operaciones@bye.cl,finanzas@bye.cl

# ==============================================================================
# DATABASE
# ==============================================================================

# Ruta de la base de datos SQLite
DB_PATH=data/seia_monitor.db

# ==============================================================================
# SCRAPING CONFIGURATION
# ==============================================================================

# Timeout para requests (segundos)
REQUEST_TIMEOUT=30

# Playwright en modo headless
PLAYWRIGHT_HEADLESS=true

# Número máximo de páginas a scrapear (1 = solo primera página con 100 proyectos)
MAX_PAGES=1

# Número máximo de proyectos por ejecución
MAX_PROJECTS_PER_RUN=10000

# User Agent para requests
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36

# ==============================================================================
# SCHEDULER
# ==============================================================================

# Zona horaria
TIMEZONE=America/Santiago

# Hora de ejecución diaria (HH:MM)
SCHEDULE_TIME=08:00

# ==============================================================================
# LOGGING
# ==============================================================================

# Nivel de log: DEBUG|INFO|WARNING|ERROR
LOG_LEVEL=INFO

# Archivo de log
LOG_FILE=logs/seia_monitor.log
```

**Guardar y salir:**
- Presionar `Ctrl + O` (guardar)
- Presionar `Enter` (confirmar)
- Presionar `Ctrl + X` (salir)

### 5. Instalar Dependencias Actualizadas

```bash
pip3 install requests --break-system-packages
```

### 6. Probar el Sistema

```bash
python3 -m seia_monitor run --once
```

**Deberías ver:**
```
✓ Email enviado exitosamente a 3 destinatario(s) con X proyecto(s)
```

### 7. Verificar los Emails

Revisar las bandejas de entrada de:
- rfernandezdelrio@bye.cl
- operaciones@bye.cl
- finanzas@bye.cl

## 📧 Formato del Email

Los emails tendrán:
- **Asunto**: 🎉 X Nuevo(s) Proyecto(s) Aprobado(s) - SEIA
- **Formato**: HTML profesional con todos los detalles del proyecto
- **Contenido**: Nombre, titular, región, tipo, fecha, estado, link al detalle

## ✅ Verificaciones

Una vez actualizado, verificar:

1. **El código se actualizó correctamente:**
   ```bash
   git log -1 --oneline
   # Debería mostrar: "feat: reemplazar SMTP por API de Bye.cl..."
   ```

2. **El .env tiene las nuevas variables:**
   ```bash
   grep EMAIL_API_ .env
   # Debería mostrar las 3 variables: BASE_URL, USER, PASSWORD
   ```

3. **El cron está activo:**
   ```bash
   crontab -l
   # Debería mostrar: 0 8 * * * cd /root/seia-monitor && ...
   ```

4. **El sistema funciona:**
   ```bash
   python3 -m seia_monitor run --once
   # Debería ejecutarse sin errores y enviar emails
   ```

## 🔧 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'requests'"

```bash
pip3 install requests --break-system-packages
```

### Error: "EMAIL_API_USER no configurado"

Verificar que el .env tiene todas las variables:
```bash
cat .env | grep EMAIL
```

### No llegan los emails

1. Verificar que `EMAIL_ENABLED=true` en .env
2. Verificar que los destinatarios están correctos en `EMAIL_TO`
3. Revisar los logs:
   ```bash
   tail -50 logs/seia_monitor.log
   ```

## 📝 Cambios Técnicos

- **Eliminado**: SMTP y todas las variables EMAIL_HOST, EMAIL_PORT, EMAIL_TLS
- **Agregado**: API REST de Bye.cl con autenticación JWT
- **Nuevo flujo**: 
  1. Login a API → obtener token
  2. Usar token para enviar email
  3. Soporta múltiples destinatarios

## 🎉 Ventajas

✅ No depende de servidores internos (apprelay.lanbye.cl)  
✅ Funciona desde internet público  
✅ Más simple y confiable  
✅ API moderna con autenticación JWT  

