# 🚀 Guía de Deployment en DigitalOcean

## 📋 Checklist Pre-Deployment

Antes de empezar, asegúrate de tener:

- [ ] Cuenta de DigitalOcean creada
- [ ] Cuenta de GitHub creada
- [ ] Código subido a GitHub (repo privado recomendado)
- [ ] Método de pago configurado en DigitalOcean

---

## Paso 1: Subir Código a GitHub (10 minutos)

### 1.1 Crear Repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre del repo: `seia-monitor` (o el que prefieras)
3. Descripción: "Sistema de monitoreo SEIA - Proyectos ambientales Chile"
4. **⚠️ IMPORTANTE:** Selecciona **PRIVATE** (no público)
5. NO marques "Add README" (ya tienes uno)
6. Click en **"Create repository"**

### 1.2 Subir tu Código

En tu Mac, ejecuta:

```bash
cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA'

# Inicializar git (si no está)
git init

# Agregar todos los archivos
git add .

# Hacer commit
git commit -m "Initial commit - SEIA Monitor"

# Conectar con GitHub (reemplaza TU-USUARIO)
git remote add origin https://github.com/TU-USUARIO/seia-monitor.git

# Subir código
git branch -M main
git push -u origin main
```

**🔑 Si te pide autenticación:**
- Username: tu usuario de GitHub
- Password: usa un **Personal Access Token** (no tu password)
  - Crear token: https://github.com/settings/tokens
  - Permisos necesarios: `repo` (full control)

✅ **Código subido a GitHub**

---

## Paso 2: Crear Droplet en DigitalOcean (5 minutos)

### 2.1 Acceder a DigitalOcean

1. Ve a https://www.digitalocean.com/
2. Click en **"Sign Up"** o **"Log In"**
3. Si es nueva cuenta, puedes obtener **$200 de crédito gratis**

### 2.2 Crear Nuevo Droplet

1. Click en **"Create"** → **"Droplets"**

2. **Choose Region:**
   - Recomendado: **Toronto** (cercano a Chile)
   - Alternativa: **New York** o **San Francisco**

3. **Choose an image:**
   - Distributions → **Ubuntu 22.04 (LTS) x64**

4. **Choose Size:**
   - **Droplet Type:** Basic
   - **CPU Options:** Regular (SSD)
   - **Plan:** $6/month
     - 1 GB RAM
     - 1 vCPU
     - 25 GB SSD
     - 1000 GB transfer

5. **Choose Authentication:**
   
   **Opción A - SSH Key (MÁS SEGURO - Recomendado):**
   ```bash
   # En tu Mac, generar SSH key si no tienes:
   ssh-keygen -t ed25519 -C "tu@email.com"
   
   # Ver tu clave pública:
   cat ~/.ssh/id_ed25519.pub
   
   # Copiar el contenido completo
   ```
   - Click "New SSH Key"
   - Pegar tu clave pública
   - Nombre: "Mi Mac" o "SEIA Monitor"
   
   **Opción B - Password (MÁS SIMPLE):**
   - Seleccionar "Password"
   - Elegir password fuerte

6. **Finalize Details:**
   - Hostname: `seia-monitor`
   - Tags: `production, seia` (opcional)
   - Backups: OFF (para ahorrar, puedes activar después)

7. Click en **"Create Droplet"**

⏳ **Espera 1 minuto** mientras se crea el servidor...

✅ **Droplet creado**

---

## Paso 3: Conectar al Servidor (2 minutos)

### 3.1 Obtener IP del Droplet

En el panel de DigitalOcean, verás la **IP pública** de tu Droplet.
Ejemplo: `164.90.123.45`

### 3.2 Conectar por SSH

**Si usaste SSH Key:**
```bash
ssh root@TU_IP_AQUI
# Ejemplo: ssh root@164.90.123.45
```

**Si usaste Password:**
```bash
ssh root@TU_IP_AQUI
# Te pedirá el password que configuraste
```

**Primera vez:** Te preguntará si confías en el servidor, escribe `yes`

✅ **Conectado al servidor**

---

## Paso 4: Instalar el Sistema (5 minutos)

### 4.1 Descargar Script de Instalación

En el servidor (ya conectado por SSH):

```bash
# Descargar script
wget https://raw.githubusercontent.com/TU-USUARIO/seia-monitor/main/deploy_digitalocean.sh

# Dar permisos de ejecución
chmod +x deploy_digitalocean.sh

# Ejecutar instalación
./deploy_digitalocean.sh
```

**⚠️ NOTA:** Reemplaza `TU-USUARIO` con tu usuario de GitHub

El script te pedirá la URL de tu repositorio:
```
URL del repo: https://github.com/TU-USUARIO/seia-monitor.git
```

⏳ **La instalación toma ~3-5 minutos**

Verás algo como:
```
[1/9] Actualizando sistema...
[2/9] Instalando dependencias base...
[3/9] Instalando Playwright y Chromium...
...
✅ INSTALACIÓN COMPLETADA
```

✅ **Sistema instalado**

---

## Paso 5: Configurar Variables de Entorno (2 minutos)

### 5.1 Editar .env

```bash
cd ~/seia-monitor
nano .env
```

Configurar:
```bash
# SEIA
SEIA_BASE_URL=https://seia.sea.gob.cl/busqueda/buscarProyecto.php
FECHA_DESDE=01/01/2025

# SCRAPING
SCRAPE_MODE=auto
REQUEST_TIMEOUT=45
PLAYWRIGHT_HEADLESS=true
MAX_PAGES=50

# BASE DE DATOS
DB_PATH=data/seia_monitor.db
LOG_LEVEL=INFO

# TEAMS (Opcional - configurar después)
# TEAMS_WEBHOOK_URL=https://...

# TIMEZONE
TIMEZONE=America/Santiago
```

**Guardar:** `Ctrl + X` → `Y` → `Enter`

✅ **Configuración lista**

---

## Paso 6: Ejecutar Primera Vez (3 minutos)

### 6.1 Prueba en Dry-Run

```bash
cd ~/seia-monitor
python3 -m seia_monitor run --once --dry-run
```

Deberías ver:
```
⚠ Modo DRY RUN - No se guardarán cambios
Iniciando monitoreo SEIA...
✓ Scraping completado: 494 proyectos, 5 páginas
```

### 6.2 Ejecución Real (Primera)

```bash
python3 -m seia_monitor run --once
```

Esto creará el snapshot inicial con los 494 proyectos.

✅ **Sistema funcionando**

---

## Paso 7: Verificar Cron Job (1 minuto)

### 7.1 Ver Cron Configurado

```bash
crontab -l
```

Deberías ver:
```
0 8 * * * cd /root/seia-monitor && /usr/bin/python3 -m seia_monitor run --once >> /root/seia-monitor/logs/cron.log 2>&1
```

### 7.2 Ajustar Hora (Opcional)

Si quieres cambiar la hora de ejecución:
```bash
crontab -e
```

Ejemplos:
- `0 8 * * *` - 08:00 AM diario
- `0 18 * * *` - 06:00 PM diario
- `0 8 * * 1-5` - 08:00 AM lunes a viernes

✅ **Cron configurado**

---

## Paso 8: Monitorear el Sistema

### 8.1 Ver Estado

```bash
cd ~/seia-monitor
./monitorear.sh
```

### 8.2 Ver Logs en Tiempo Real

```bash
tail -f ~/seia-monitor/logs/seia_monitor.log
```

### 8.3 Ver Base de Datos

```bash
sqlite3 ~/seia-monitor/data/seia_monitor.db

# Dentro de sqlite:
SELECT COUNT(*) FROM projects_current;
SELECT * FROM projects_current WHERE estado_normalizado='aprobado' LIMIT 5;

# Salir:
.quit
```

---

## 🎉 ¡Listo! Sistema Funcionando 24/7

Tu sistema ahora:

✅ Se ejecuta automáticamente todos los días a las 08:00 AM
✅ Monitorea 494 proyectos desde enero 2025
✅ Detecta cuando proyectos pasan a "Aprobado"
✅ Extrae detalles completos automáticamente
✅ Guarda todo en base de datos

---

## 🔧 Comandos Útiles

### Conectarse al Servidor
```bash
ssh root@TU_IP_DIGITALOCEAN
```

### Ver Logs
```bash
# Logs del sistema
tail -f ~/seia-monitor/logs/seia_monitor.log

# Logs del cron
tail -f ~/seia-monitor/logs/cron.log
```

### Ejecutar Manualmente
```bash
cd ~/seia-monitor
python3 -m seia_monitor run --once
```

### Actualizar Código
```bash
cd ~/seia-monitor
git pull
pip3 install -r requirements.txt
```

### Reiniciar Servidor
```bash
sudo reboot
# Esperar 1 minuto y reconectar
```

### Hacer Backup
```bash
# Backup de BD
cp ~/seia-monitor/data/seia_monitor.db ~/backup_$(date +%Y%m%d).db

# Descargar a tu Mac
# En tu Mac (no en el servidor):
scp root@TU_IP:~/backup_*.db ~/Desktop/
```

---

## 🔐 Seguridad (Opcional pero Recomendado)

### Crear Usuario No-Root

```bash
# Crear usuario
adduser seia
usermod -aG sudo seia

# Copiar SSH key
rsync --archive --chown=seia:seia ~/.ssh /home/seia

# Probar login
# En tu Mac:
ssh seia@TU_IP
```

### Configurar Firewall

```bash
# Permitir SSH
sudo ufw allow OpenSSH
sudo ufw enable
```

---

## ❓ Troubleshooting

### El cron no se ejecuta

```bash
# Verificar que cron esté corriendo
sudo systemctl status cron

# Ver logs de cron
grep CRON /var/log/syslog
```

### Playwright da error

```bash
# Reinstalar dependencias
sudo playwright install-deps chromium
```

### Espacio en disco lleno

```bash
# Ver uso de disco
df -h

# Limpiar logs antiguos
cd ~/seia-monitor/logs
rm *.log.1 *.log.2
```

### Actualizar el sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

---

## 💰 Costos

- **Droplet $6/mes:** ~$0.20/día
- **Bandwidth:** Incluido (1TB/mes - más que suficiente)
- **Backups (opcional):** +20% ($1.20/mes)

**Total estimado:** $6-8 USD/mes

---

## 📞 Soporte

Si tienes problemas:

1. **Ver logs:** `tail -f ~/seia-monitor/logs/seia_monitor.log`
2. **Verificar estado:** `./monitorear.sh`
3. **Revisar cron:** `crontab -l`
4. **Documentación DigitalOcean:** https://docs.digitalocean.com/

---

## 🎯 Checklist Final

- [ ] Código subido a GitHub
- [ ] Droplet creado en DigitalOcean
- [ ] Sistema instalado y configurado
- [ ] Primera ejecución exitosa
- [ ] Cron job funcionando
- [ ] Logs verificados
- [ ] Sistema monitoreando 24/7

**¡Felicidades! Tu sistema está en producción 🎉**


