# 🚀 Guía de Puesta en Producción - SEIA Monitor

**Fecha**: 8 de Enero 2025  
**Estado**: Sistema listo para producción ✅

---

## ✅ Setup Completado

El sistema está instalado y configurado. Solo faltan 2 pasos:

1. ✅ Python y dependencias instaladas
2. ✅ Estructura del proyecto creada
3. ✅ Directorios `data/` y `logs/` creados
4. ✅ Archivo `.env` creado
5. ⚠️ **PENDIENTE: Configurar webhook de Teams**
6. ⚠️ **PENDIENTE: Primera ejecución**

---

## 🔔 Paso 1: Configurar Microsoft Teams

### Obtener Webhook URL

1. Abre Microsoft Teams
2. Ve al canal donde quieres recibir las notificaciones
3. Click en `•••` (tres puntos) junto al nombre del canal
4. Selecciona **"Conectores"** o **"Connectors"**
5. Busca **"Incoming Webhook"**
6. Click en **"Configurar"**
7. Nombre: **"SEIA Monitor"**
8. Click en **"Crear"**
9. **COPIA LA URL COMPLETA** (empezará con `https://outlook.office.com/webhook/...`)

### Configurar en .env

```bash
# Editar .env
nano /Users/rodrigofernandezdelrio/Desktop/Proyecto\ SEA/.env

# Buscar la línea:
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/YOUR_WEBHOOK_URL_HERE

# Reemplazar con tu URL real:
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/[TU_URL_AQUI]

# Guardar: Ctrl+O, Enter, Ctrl+X
```

### Probar Webhook

```bash
cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA'
python3 -m seia_monitor test-teams
```

✅ Deberías ver un mensaje de prueba en el canal de Teams.

---

## 🧪 Paso 2: Prueba en Dry-Run

Antes de la primera ejecución real, prueba en modo dry-run (no guarda ni notifica):

```bash
cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA'
python3 -m seia_monitor run --once --dry-run --verbose
```

Esto:
- ✅ Hará scraping del SEIA (proyectos desde 01/01/2025)
- ✅ Mostrará cuántos proyectos encuentra
- ✅ Mostrará logs detallados
- ❌ NO guardará nada en la base de datos
- ❌ NO enviará notificaciones a Teams

**Espera ver**: Algo como "Parseados X proyectos del HTML"

---

## 🎯 Paso 3: Primera Ejecución Real

```bash
cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA'
python3 -m seia_monitor run --once
```

Esta primera ejecución:
- ✅ Hará scraping de todos los proyectos desde 01/01/2025
- ✅ Guardará el snapshot inicial en la base de datos
- ❌ NO enviará notificación (es la primera vez, no hay cambios)

**Esto es normal**: La primera ejecución solo crea el snapshot base.

---

## 📊 Paso 4: Ver Estado

```bash
cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA'
python3 -m seia_monitor status
```

Verás:
- Estado de la última corrida
- Cuántos proyectos se monitorearon
- Duración
- Errores (si los hubo)

---

## 🔄 Paso 5: Configurar Ejecución Automática

### Opción A: Cron (Recomendado para Servidores)

```bash
# Editar crontab
crontab -e

# Agregar esta línea (ejecuta todos los días a las 08:00):
0 8 * * * cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA' && /usr/bin/python3 -m seia_monitor run --once >> logs/cron.log 2>&1
```

**Verificar que funcione**:
- Espera hasta las 08:00 o ajusta la hora para probar
- O ejecuta manualmente: `python3 -m seia_monitor run --once`

### Opción B: Scheduler Interno

```bash
cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA'
python3 -m seia_monitor schedule
```

El proceso quedará corriendo en terminal. Para ejecutarlo en background:

```bash
# Ejecutar en background
nohup python3 -m seia_monitor schedule > logs/scheduler.log 2>&1 &

# Ver el proceso
ps aux | grep seia_monitor

# Detener (si es necesario)
pkill -f seia_monitor
```

---

## 📋 Comandos Útiles

### Ejecución Manual
```bash
cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA'

# Ejecutar una vez
python3 -m seia_monitor run --once

# Dry-run (prueba)
python3 -m seia_monitor run --once --dry-run

# Con logs detallados
python3 -m seia_monitor run --once --verbose
```

### Monitoreo
```bash
# Ver estado
python3 -m seia_monitor status

# Ver logs en tiempo real
tail -f logs/seia_monitor.log

# Ver últimas 50 líneas
tail -50 logs/seia_monitor.log

# Buscar errores
grep ERROR logs/seia_monitor.log
```

### Configuración
```bash
# Verificar configuración
python3 -m seia_monitor config-check

# Probar webhook Teams
python3 -m seia_monitor test-teams

# Ver versión
python3 -m seia_monitor version
```

---

## 🎯 Flujo Diario Esperado

### Primera Ejecución (Hoy)
1. Scraping → Encuentra X proyectos desde 01/01/2025
2. Guarda snapshot inicial
3. **No envía notificación** (no hay comparación previa)

### Segunda Ejecución (Mañana)
1. Scraping → Encuentra X proyectos
2. Compara con snapshot de ayer
3. Si hay **nuevos proyectos** o **cambios de estado relevantes** → **Envía notificación a Teams**
4. Actualiza snapshot

### Ejecuciones Siguientes
- Se repite el ciclo
- Solo notifica cuando hay cambios relevantes

---

## 🔍 Qué Monitorea

### Proyectos Nuevos
Cualquier proyecto que no existía en el snapshot anterior.

### Cambios de Estado Relevantes
1. **En Admisión** → **En Calificación (Activo)**
2. **En Calificación (Activo)** → **Aprobado**
3. **Cualquier estado** → **Aprobado**

Otros cambios se registran en el historial pero **no** se notifican.

---

## 📊 Base de Datos

Ubicación: `data/seia_monitor.db`

### Consultar con SQL

```bash
sqlite3 data/seia_monitor.db

# Ver últimas corridas
SELECT * FROM runs ORDER BY timestamp DESC LIMIT 5;

# Ver proyectos actuales
SELECT COUNT(*) FROM projects_current;

# Ver historial de cambios
SELECT * FROM project_history WHERE is_relevant = 1 ORDER BY timestamp DESC LIMIT 10;

# Salir
.quit
```

---

## 🛠️ Troubleshooting

### No recibo notificaciones en Teams

**Causa**: Webhook no configurado o incorrecto

**Solución**:
```bash
# Verificar configuración
grep TEAMS_WEBHOOK_URL .env

# Probar webhook
python3 -m seia_monitor test-teams
```

### Scraping retorna 0 proyectos

**Causa**: Posible cambio en la página del SEIA o problemas de conexión

**Solución**:
```bash
# Ver logs detallados
python3 -m seia_monitor run --once --dry-run --verbose

# Ver HTML de debug (si hay error)
ls -lt data/debug/
```

### Primera ejecución no notifica

**Esto es normal**: La primera ejecución solo crea el snapshot base. Las notificaciones empiezan en la segunda ejecución cuando hay algo con qué comparar.

### Cron no ejecuta

**Verificar**:
```bash
# Ver logs de cron
tail -f logs/cron.log

# Verificar sintaxis de crontab
crontab -l
```

---

## 📈 Monitoreo de Producción

### Checklist Diario
- [ ] Revisar logs: `tail -50 logs/seia_monitor.log`
- [ ] Verificar última corrida: `python3 -m seia_monitor status`
- [ ] Verificar que Teams recibe notificaciones (si hay cambios)

### Checklist Semanal
- [ ] Revisar base de datos: `sqlite3 data/seia_monitor.db`
- [ ] Verificar espacio en disco: `df -h`
- [ ] Backup de la base de datos:
  ```bash
  cp data/seia_monitor.db data/seia_monitor.db.backup
  ```

---

## 🎉 Sistema en Producción

Una vez completados todos los pasos, el sistema estará:

✅ Monitoreando proyectos SEIA desde 01/01/2025  
✅ Detectando nuevos proyectos automáticamente  
✅ Detectando cambios de estado relevantes  
✅ Notificando al canal de Teams  
✅ Ejecutándose automáticamente todos los días a las 08:00  
✅ Guardando historial completo en SQLite  
✅ Generando logs detallados  

---

## 📞 Soporte

**Logs**: `logs/seia_monitor.log`  
**Base de datos**: `data/seia_monitor.db`  
**Documentación**: `README.md`  

---

**¡Sistema listo para producción!** 🚀


