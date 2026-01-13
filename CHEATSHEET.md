# 🚀 SEIA Monitor - Cheat Sheet

## 📦 Instalación Inicial (Solo una vez)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt
playwright install chromium

# 2. Configurar entorno
cp .env.example .env
# Editar .env con tus configuraciones

# 3. Primera ejecución
python3 -m seia_monitor run --once
```

---

## ⏰ Configurar Cron (Ejecución automática)

```bash
# Instalar cron automáticamente
./cron_setup.sh

# Verificar instalación
crontab -l

# Ver logs de cron
tail -f logs/cron.log
```

---

## 🎮 Comandos Principales

### Ejecución
```bash
# Ejecutar una vez
python3 -m seia_monitor run --once

# Ejecutar en dry-run (no guarda)
python3 -m seia_monitor run --once --dry-run

# Scheduler interno (no recomendado)
python3 -m seia_monitor schedule start
```

### Monitoreo
```bash
# Estado del sistema
python3 -m seia_monitor status

# Verificar configuración
python3 -m seia_monitor config-check

# Verificar instalación
python3 verify.py
```

### Testing
```bash
# Test de Teams
python3 -m seia_monitor test-teams

# Test de cron
./test_cron.sh

# Ejecutar tests unitarios
pytest tests/
```

---

## 📊 Base de Datos

### Consultas SQLite
```bash
# Ver proyectos actuales
sqlite3 data/seia_monitor.db "SELECT * FROM projects_current LIMIT 10;"

# Ver historial de cambios
sqlite3 data/seia_monitor.db "SELECT * FROM project_history ORDER BY changed_at DESC LIMIT 10;"

# Ver estadísticas de ejecuciones
sqlite3 data/seia_monitor.db "SELECT * FROM runs ORDER BY started_at DESC LIMIT 5;"

# Contar proyectos por estado
sqlite3 data/seia_monitor.db "SELECT estado, COUNT(*) FROM projects_current GROUP BY estado;"
```

---

## 📝 Logs

### Ver logs en tiempo real
```bash
# Log principal de la app
tail -f logs/seia_monitor.log

# Log de cron
tail -f logs/cron.log

# Ver últimas 50 líneas
tail -50 logs/seia_monitor.log

# Buscar errores
grep -i "error\|exception" logs/seia_monitor.log
```

---

## 🔧 Cron

### Gestión de cron jobs
```bash
# Ver cron jobs
crontab -l

# Editar cron jobs
crontab -e

# Eliminar TODOS los cron jobs
crontab -r

# Eliminar solo SEIA Monitor
crontab -l | grep -v "seia_monitor" | crontab -
```

### Horarios útiles
```bash
# Diario 8 AM (lun-vie)
0 8 * * 1-5 cd '/ruta/proyecto' && python3 -m seia_monitor run --once >> 'logs/cron.log' 2>&1

# Cada hora 9-18 (lun-vie)
0 9-18 * * 1-5 cd '/ruta/proyecto' && python3 -m seia_monitor run --once >> 'logs/cron.log' 2>&1

# Cada 30 min 9-18 (lun-vie)
*/30 9-18 * * 1-5 cd '/ruta/proyecto' && python3 -m seia_monitor run --once >> 'logs/cron.log' 2>&1
```

---

## 🔑 Variables de Entorno (.env)

```bash
# Teams (opcional)
TEAMS_WEBHOOK_URL=https://...

# SEIA
SEIA_BASE_URL=https://seia.sea.gob.cl/busqueda/buscarProyecto.php

# Scraping
SCRAPE_MODE=auto                    # auto, requests, playwright
REQUEST_TIMEOUT=30
PLAYWRIGHT_HEADLESS=true
MAX_PAGES=50

# Sistema
DB_PATH=data/seia_monitor.db
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR
TIMEZONE=America/Santiago
```

---

## 🐛 Troubleshooting

### El scraper falla
```bash
# 1. Verificar instalación
python3 verify.py

# 2. Ver logs detallados
tail -100 logs/seia_monitor.log | grep ERROR

# 3. Probar manualmente
python3 -m seia_monitor run --once --dry-run

# 4. Ver HTML capturado
ls -lh data/debug/
```

### El cron no funciona
```bash
# 1. Verificar que está instalado
crontab -l

# 2. Ver logs de cron
tail -50 logs/cron.log

# 3. Probar comando manualmente
./test_cron.sh

# 4. Verificar permisos
ls -la cron_setup.sh test_cron.sh
```

### Teams no envía notificaciones
```bash
# 1. Verificar webhook
python3 -m seia_monitor config-check

# 2. Probar webhook
python3 -m seia_monitor test-teams

# 3. Ver errores en logs
grep -i "teams\|webhook" logs/seia_monitor.log
```

---

## 📁 Estructura de Archivos

```
Proyecto SEA/
├── seia_monitor/          # Código fuente
│   ├── config.py          # Configuración
│   ├── scraper.py         # Scraping principal
│   ├── parser.py          # Parsing HTML
│   ├── storage.py         # Base de datos
│   ├── diff.py            # Detección de cambios
│   ├── notifier_teams.py  # Notificaciones Teams
│   └── runner.py          # Orquestador principal
├── tests/                 # Tests unitarios
├── data/                  # Base de datos y debug
├── logs/                  # Logs de ejecución
├── .env                   # Configuración (NO subir a git)
├── requirements.txt       # Dependencias Python
├── README.md              # Documentación completa
├── CRON_GUIDE.md          # Guía de cron
├── cron_setup.sh          # Instalador de cron
├── test_cron.sh           # Test de cron
└── verify.py              # Verificador de sistema
```

---

## 🔗 Links Útiles

- **Crontab Guru**: https://crontab.guru/ (verificador de sintaxis cron)
- **SEIA**: https://seia.sea.gob.cl/
- **Playwright Docs**: https://playwright.dev/python/

---

## 📚 Documentación

| Archivo | Descripción |
|---------|-------------|
| `README.md` | Documentación completa del proyecto |
| `CRON_GUIDE.md` | Guía detallada de configuración de cron |
| `INSTALL.md` | Guía de instalación paso a paso |
| `QUICKSTART.md` | Inicio rápido en 5 minutos |
| `PRODUCCION.md` | Guía de despliegue en producción |
| `CHANGELOG.md` | Historial de cambios |
| `CHEATSHEET.md` | Esta guía rápida |

---

## ⚡ Quick Reference

```bash
# Instalación completa desde cero
pip install -r requirements.txt && playwright install chromium && cp .env.example .env

# Primera ejecución
python3 -m seia_monitor run --once

# Instalar cron
./cron_setup.sh

# Verificar todo
python3 verify.py && crontab -l && tail -20 logs/seia_monitor.log
```

---

**Última actualización**: 2026-01-08


