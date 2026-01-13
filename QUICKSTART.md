# 🚀 Quick Start - SEIA Monitor

Guía rápida para tener el sistema funcionando en 5 minutos.

## 1️⃣ Instalación (2 minutos)

```bash
# Ejecutar script de setup
chmod +x setup.sh
./setup.sh
```

El script instalará automáticamente todas las dependencias.

## 2️⃣ Configurar Webhook de Teams (2 minutos)

### En Microsoft Teams:

1. Abre el canal donde quieres recibir notificaciones
2. Click en `•••` → "Conectores" → "Incoming Webhook"
3. Click "Configurar" → Dale nombre "SEIA Monitor" → "Crear"
4. **Copia la URL completa**

### En tu proyecto:

```bash
# Editar .env
nano .env

# Pegar la URL:
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/TU_URL_AQUI

# Guardar: Ctrl+O, Enter, Ctrl+X
```

## 3️⃣ Probar (1 minuto)

```bash
# Activar entorno virtual (si no está activo)
source venv/bin/activate

# Probar webhook
python -m seia_monitor test-teams
```

✅ Si funciona, verás un mensaje de prueba en Teams.

```bash
# Ejecutar en modo dry-run (no guarda ni notifica)
python -m seia_monitor run --once --dry-run
```

✅ Si funciona, verás logs de scraping y detección.

## 4️⃣ Primera Ejecución Real

```bash
python -m seia_monitor run --once
```

Esto:
- Hará scraping del SEIA (proyectos desde 01/01/2025)
- Guardará el snapshot inicial
- NO enviará notificación (es la primera vez, no hay cambios)

## 5️⃣ Automatizar

### Opción A: Scheduler Interno

```bash
# Ejecutará automáticamente todos los días a las 08:00
python -m seia_monitor schedule
```

Para detener: `Ctrl+C`

### Opción B: Cron (recomendado para servidores)

```bash
crontab -e
```

Agregar:
```
0 8 * * * cd /ruta/completa/a/Proyecto\ SEA && /ruta/completa/a/venv/bin/python -m seia_monitor run --once >> logs/cron.log 2>&1
```

**Obtener ruta completa:**
```bash
pwd  # Copiar el resultado
which python  # Dentro del venv activado
```

## 📊 Ver Estado

```bash
# Ver última corrida
python -m seia_monitor status

# Ver logs en tiempo real
tail -f logs/seia_monitor.log

# Ver últimas 50 líneas de log
tail -50 logs/seia_monitor.log
```

## 🎯 Comandos Útiles

```bash
# Ver todos los comandos
python -m seia_monitor --help

# Verificar configuración
python -m seia_monitor config-check

# Ejecutar una vez (producción)
python -m seia_monitor run --once

# Ejecutar en dry-run (prueba)
python -m seia_monitor run --once --dry-run

# Ver versión
python -m seia_monitor version
```

## ⚡ Flujo Típico de Uso

### Primera Vez (Setup)
```bash
./setup.sh
nano .env  # Configurar webhook
python -m seia_monitor test-teams
python -m seia_monitor run --once
```

### Uso Diario (Automático)
El sistema correrá solo con el scheduler o cron.

### Revisar Estado
```bash
python -m seia_monitor status
tail -f logs/seia_monitor.log
```

### Si Algo Falla
```bash
# Ver logs
tail -100 logs/seia_monitor.log | grep ERROR

# Ver debug HTML
ls -lt data/debug/

# Ejecutar manualmente con verbose
python -m seia_monitor run --once --dry-run --verbose
```

## 💡 Tips

1. **Primera ejecución**: No te preocupes si no recibes notificación, es normal (no hay cambios aún).

2. **Segunda ejecución**: Si hay proyectos nuevos desde ayer, los detectará.

3. **Dry-run**: Usa `--dry-run` para probar sin guardar cambios ni enviar notificaciones.

4. **Verbose**: Usa `--verbose` o `-v` para ver logs detallados.

5. **Timezone**: El sistema usa `America/Santiago` por defecto (configurable en .env).

6. **Webhook seguro**: No compartas tu webhook URL, cualquiera con ella puede enviar mensajes al canal.

## 🆘 Problemas Comunes

| Problema | Solución |
|----------|----------|
| "No module named 'seia_monitor'" | `source venv/bin/activate` |
| Playwright error | `playwright install chromium` |
| Webhook no funciona | Regenerar en Teams y actualizar .env |
| 0 proyectos scraped | Verificar `FECHA_DESDE` en .env |
| Tests fallan | Normal en primera instalación |

## 📚 Más Información

- **Instalación detallada**: [INSTALL.md](INSTALL.md)
- **Documentación completa**: [README.md](README.md)
- **Cambios y versiones**: [CHANGELOG.md](CHANGELOG.md)

---

¿Dudas? Revisa los logs: `tail -f logs/seia_monitor.log`


