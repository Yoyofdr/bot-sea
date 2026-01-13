# 🚀 GUÍA DE DEPLOYMENT - PASO A PASO (Simple)

**Tiempo estimado: 30 minutos**

---

## ✅ **PASO 1: Preparar Código en GitHub (10 min)**

### 1.1 Crear cuenta en GitHub (si no tienes)
- Ve a: https://github.com/signup
- Usa tu email corporativo si prefieres

### 1.2 Crear repositorio PRIVADO

1. Ve a: https://github.com/new
2. **Repository name:** `seia-monitor`
3. **Description:** "Monitor automático SEIA Chile"
4. **⚠️ IMPORTANTE:** Marca **Private** (privado)
5. **NO marques** "Add README" (ya tienes uno)
6. Click **"Create repository"**

### 1.3 Subir tu código

Abre la Terminal en tu Mac y ejecuta:

```bash
# Ir a tu proyecto
cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA'

# Inicializar git (si no está)
git init

# Agregar todos los archivos
git add .

# Hacer commit
git commit -m "Initial commit - SEIA Monitor"

# Conectar con GitHub (REEMPLAZA con tu usuario)
git remote add origin https://github.com/TU-USUARIO-GITHUB/seia-monitor.git

# Subir código
git branch -M main
git push -u origin main
```

**🔑 Si te pide usuario/password:**
- Usuario: tu nombre de usuario de GitHub
- Password: necesitas crear un **Personal Access Token**
  - Ve a: https://github.com/settings/tokens
  - Click "Generate new token (classic)"
  - Permisos: marca `repo` (control total)
  - Copia el token y úsalo como password

✅ **Código subido a GitHub**

---

## ✅ **PASO 2: Crear Servidor en DigitalOcean (5 min)**

### 2.1 Crear cuenta

1. Ve a: https://www.digitalocean.com/
2. Click **"Sign Up"**
3. **💰 PROMO:** Usa el código de $200 gratis:
   - https://try.digitalocean.com/freetrialoffer/

### 2.2 Crear Droplet

1. Click **"Create"** → **"Droplets"**

2. **Región:** 
   - Recomendado: **Toronto** (cercano a Chile)

3. **Image:**
   - **Ubuntu 22.04 (LTS) x64**

4. **Tamaño del Droplet:**
   - **$6/mes** (suficiente para tu caso)
   - 1 GB RAM
   - 1 vCPU
   - 25 GB SSD

5. **Autenticación:**
   
   **Opción A - Password (MÁS FÁCIL):**
   - Marca "Password"
   - Elige un password fuerte (guárdalo)
   
   **Opción B - SSH Key (MÁS SEGURO):**
   ```bash
   # En tu Mac, ejecutar:
   ssh-keygen -t ed25519 -C "tu@email.com"
   
   # Ver tu clave pública:
   cat ~/.ssh/id_ed25519.pub
   
   # Copiar TODO el contenido
   ```
   - Click "New SSH Key"
   - Pegar contenido
   - Nombre: "Mi Mac"

6. **Hostname:** `seia-monitor`

7. Click **"Create Droplet"**

⏳ Espera 1 minuto...

✅ **Servidor creado**

### 2.3 Anotar la IP

En el panel de DigitalOcean verás la **IP pública** del Droplet.

**Ejemplo:** `164.90.123.45`

📝 **Anótala, la necesitarás**

---

## ✅ **PASO 3: Conectar al Servidor (2 min)**

Abre la Terminal en tu Mac:

```bash
# REEMPLAZA con tu IP
ssh root@TU_IP_AQUI

# Ejemplo:
# ssh root@164.90.123.45
```

**Si usaste password:** Te pedirá el password que configuraste

**Primera conexión:** Te preguntará si confías en el servidor, escribe `yes`

✅ **Conectado al servidor** (verás `root@seia-monitor:~#`)

---

## ✅ **PASO 4: Instalar el Sistema (5 min)**

**Ahora estás dentro del servidor** (en la terminal remota)

### 4.1 Descargar script de instalación

```bash
# REEMPLAZA con tu usuario de GitHub
wget https://raw.githubusercontent.com/TU-USUARIO-GITHUB/seia-monitor/main/deploy_digitalocean.sh

# Dar permisos
chmod +x deploy_digitalocean.sh

# Ejecutar
./deploy_digitalocean.sh
```

### 4.2 Durante la instalación

Te pedirá la **URL de tu repositorio**:

```
URL del repo: https://github.com/TU-USUARIO-GITHUB/seia-monitor.git
```

⏳ **La instalación toma 3-5 minutos** (toma un café ☕)

Verás:
```
[1/9] Actualizando sistema...
[2/9] Instalando dependencias base...
[3/9] Instalando Playwright y Chromium...
...
✅ INSTALACIÓN COMPLETADA
```

✅ **Sistema instalado**

---

## ✅ **PASO 5: Configurar el Sistema (3 min)**

### 5.1 Editar configuración

```bash
cd ~/seia-monitor
nano .env
```

### 5.2 Configurar variables (mínimo necesario)

Usa las flechas del teclado para moverte y edita:

```bash
# Verifica que esté así:
FECHA_DESDE=01/01/2025
SCRAPE_MODE=auto
PLAYWRIGHT_HEADLESS=true

# Teams (opcional - puedes configurarlo después)
# TEAMS_WEBHOOK_URL=https://...
```

**Para guardar:**
1. `Ctrl + X`
2. Presiona `Y` (yes)
3. Presiona `Enter`

✅ **Configuración lista**

---

## ✅ **PASO 6: Probar el Sistema (5 min)**

### 6.1 Primera prueba (dry-run)

```bash
cd ~/seia-monitor
python3 -m seia_monitor run --once --dry-run
```

Deberías ver algo como:

```
⚠ Modo DRY RUN - No se guardarán cambios
Iniciando monitoreo SEIA...
✓ Scraping completado: 494 proyectos encontrados
✓ 5 páginas procesadas
```

### 6.2 Primera ejecución REAL

```bash
python3 -m seia_monitor run --once
```

Esto creará el **snapshot inicial** con todos los proyectos actuales.

```
✓ Scraping completado: 494 proyectos
✓ Guardados en base de datos
✓ Snapshot inicial creado
```

✅ **Sistema funcionando**

---

## ✅ **PASO 7: Verificar Cron (Ejecución Automática)**

### 7.1 Ver cron configurado

```bash
crontab -l
```

Deberías ver:

```
0 8 * * * cd /root/seia-monitor && /usr/bin/python3 -m seia_monitor run --once >> /root/seia-monitor/logs/cron.log 2>&1
```

Esto significa: **Se ejecutará TODOS LOS DÍAS a las 08:00 AM**

### 7.2 Cambiar hora (opcional)

Si quieres cambiar la hora:

```bash
crontab -e
```

Ejemplos:
- `0 9 * * *` - 09:00 AM diario
- `0 18 * * *` - 06:00 PM diario
- `0 8 * * 1-5` - 08:00 AM solo lunes a viernes

✅ **Cron configurado**

---

## 🎉 **¡LISTO! Sistema Funcionando 24/7**

Tu sistema ahora:

✅ Se ejecuta **automáticamente todos los días a las 08:00 AM**  
✅ Monitorea **494 proyectos** desde enero 2025  
✅ Detecta cuando pasan a "**Aprobado**"  
✅ Extrae **detalles completos** automáticamente  
✅ Guarda todo en **base de datos**  
✅ (Opcional) Notifica a **Microsoft Teams**  

---

## 📋 **PASO EXTRA: Configurar Teams (Opcional - 5 min)**

Si quieres recibir notificaciones en Teams:

### 1. En Microsoft Teams:

1. Ir al **canal** donde quieres notificaciones
2. Click en `•••` (más opciones)
3. **Workflows** o **Conectores**
4. Buscar **"Incoming Webhook"**
5. Click **"Configurar"** o **"Add"**
6. Nombre: `SEIA Monitor`
7. Click **"Crear"**
8. **Copiar la URL completa** (empieza con `https://outlook.office.com/webhook/...`)

### 2. En el servidor:

```bash
cd ~/seia-monitor
nano .env
```

Agregar la URL:

```bash
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/TU_URL_AQUI
```

Guardar: `Ctrl + X` → `Y` → `Enter`

### 3. Probar:

```bash
python3 -m seia_monitor test-teams
```

Deberías recibir un mensaje de prueba en Teams ✅

---

## 🔧 **Comandos Útiles**

### Conectarte al servidor (desde tu Mac)

```bash
ssh root@TU_IP
```

### Ver logs en tiempo real

```bash
tail -f ~/seia-monitor/logs/seia_monitor.log
```

### Ver estado del sistema

```bash
cd ~/seia-monitor
python3 -m seia_monitor status
```

### Ejecutar manualmente

```bash
cd ~/seia-monitor
python3 -m seia_monitor run --once
```

### Ver base de datos

```bash
sqlite3 ~/seia-monitor/data/seia_monitor.db
```

Dentro de sqlite:
```sql
-- Ver total de proyectos
SELECT COUNT(*) FROM projects_current;

-- Ver proyectos aprobados
SELECT nombre, estado, titular FROM projects_current 
WHERE estado_normalizado='aprobado' 
LIMIT 10;

-- Salir
.quit
```

### Desconectarte del servidor

```bash
exit
```

---

## ❓ **Problemas Comunes**

### "Permission denied" al conectar por SSH

- Verifica que usaste la IP correcta
- Si usaste SSH key, verifica que esté en `~/.ssh/id_ed25519`

### El scraping no encuentra proyectos

```bash
# Ver logs
tail -50 ~/seia-monitor/logs/seia_monitor.log

# Probar con verbose
python3 -m seia_monitor run --once --verbose
```

### Teams no recibe mensajes

```bash
# Probar webhook
python3 -m seia_monitor test-teams

# Si falla, regenerar webhook en Teams
```

---

## 💰 **Costos**

- **Droplet:** $6 USD/mes
- **Bandwidth:** GRATIS (incluido 1TB)
- **Total:** **$6 USD/mes** (~$72 USD/año)

Puedes pagar con tarjeta de crédito o PayPal.

---

## 🎯 **Checklist Final**

Verifica que todo esté funcionando:

- [ ] Código subido a GitHub
- [ ] Droplet creado en DigitalOcean  
- [ ] Conectado al servidor por SSH
- [ ] Sistema instalado (`./deploy_digitalocean.sh`)
- [ ] Archivo `.env` configurado
- [ ] Primera ejecución exitosa
- [ ] Cron job funcionando (`crontab -l`)
- [ ] Logs verificados (`tail -f logs/seia_monitor.log`)
- [ ] (Opcional) Teams configurado

---

## 📞 **¿Necesitas Ayuda?**

Si algo falla:

1. **Ver logs:** `tail -f ~/seia-monitor/logs/seia_monitor.log`
2. **Ver estado:** `python3 -m seia_monitor status`
3. **Consultar documentación completa:** `README.md`

---

**¡Felicidades! Tu sistema está en producción 🚀**

