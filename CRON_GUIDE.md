# 📅 Guía Rápida de Cron - SEIA Monitor

## 🚀 Instalación Rápida

```bash
./cron_setup.sh
```

Elige opción **`s`** para instalar automáticamente.

---

## ⏰ Horarios Disponibles

### 1. **Una vez al día** (Recomendado) ✅

```cron
0 8 * * 1-5 cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA' && /usr/bin/python3 -m seia_monitor run --once >> '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA/logs/cron.log' 2>&1
```

- **Cuándo**: Lunes a Viernes a las 8:00 AM
- **Zona horaria**: America/Santiago
- **Uso**: Monitoreo diario estándar

### 2. **Cada hora** (Horario laboral)

```cron
0 9-18 * * 1-5 cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA' && /usr/bin/python3 -m seia_monitor run --once >> '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA/logs/cron.log' 2>&1
```

- **Cuándo**: Cada hora entre 9 AM y 6 PM, lunes a viernes
- **Uso**: Monitoreo más frecuente

### 3. **Cada 30 minutos** (Horario laboral)

```cron
*/30 9-18 * * 1-5 cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA' && /usr/bin/python3 -m seia_monitor run --once >> '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA/logs/cron.log' 2>&1
```

- **Cuándo**: Cada 30 minutos entre 9 AM y 6 PM, lunes a viernes
- **Uso**: Monitoreo intensivo

### 4. **Dos veces al día**

```cron
0 8,18 * * 1-5 cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA' && /usr/bin/python3 -m seia_monitor run --once >> '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA/logs/cron.log' 2>&1
```

- **Cuándo**: 8 AM y 6 PM, lunes a viernes
- **Uso**: Balance entre frecuencia y recursos

### 5. **Todos los días** (Incluye fines de semana)

```cron
0 8 * * * cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA' && /usr/bin/python3 -m seia_monitor run --once >> '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA/logs/cron.log' 2>&1
```

- **Cuándo**: Todos los días a las 8 AM
- **Uso**: Monitoreo 7 días a la semana

---

## 🛠️ Comandos Esenciales

### Ver cron jobs instalados
```bash
crontab -l
```

### Editar cron jobs
```bash
crontab -e
```

### Eliminar todos los cron jobs
```bash
crontab -r
```

⚠️ **Cuidado**: Esto eliminará TODOS tus cron jobs, no solo el de SEIA Monitor.

### Eliminar solo el cron job de SEIA Monitor
```bash
crontab -l | grep -v "seia_monitor" | crontab -
```

---

## 📊 Monitoreo y Logs

### Ver logs de cron en tiempo real
```bash
tail -f logs/cron.log
```

### Ver logs de la aplicación en tiempo real
```bash
tail -f logs/seia_monitor.log
```

### Ver últimas 50 líneas del log de cron
```bash
tail -50 logs/cron.log
```

### Ver errores en el log
```bash
grep -i "error\|exception\|fail" logs/cron.log
```

### Ver estadísticas de ejecuciones
```bash
grep "Corrida completada exitosamente" logs/cron.log | wc -l
```

---

## 🧪 Testing

### Test completo antes de instalar cron
```bash
./test_cron.sh
```

### Ejecutar manualmente (simular cron)
```bash
python3 -m seia_monitor run --once
```

### Ejecutar en dry-run (no guarda cambios)
```bash
python3 -m seia_monitor run --once --dry-run
```

### Ver estado de la base de datos
```bash
python3 -m seia_monitor status
```

---

## 📝 Sintaxis de Cron

```
┌───────────── minuto (0 - 59)
│ ┌───────────── hora (0 - 23)
│ │ ┌───────────── día del mes (1 - 31)
│ │ │ ┌───────────── mes (1 - 12)
│ │ │ │ ┌───────────── día de la semana (0 - 6) (0=Domingo)
│ │ │ │ │
│ │ │ │ │
* * * * * comando a ejecutar
```

### Ejemplos de sintaxis

| Expresión | Significado |
|-----------|-------------|
| `0 8 * * *` | Todos los días a las 8:00 AM |
| `0 8 * * 1-5` | Lunes a Viernes a las 8:00 AM |
| `*/30 * * * *` | Cada 30 minutos |
| `0 */2 * * *` | Cada 2 horas |
| `0 8,18 * * *` | A las 8:00 AM y 6:00 PM |
| `0 9-17 * * 1-5` | Cada hora de 9 AM a 5 PM, lunes a viernes |

---

## 🔍 Troubleshooting

### El cron no se ejecuta

1. **Verificar que está instalado**:
   ```bash
   crontab -l
   ```

2. **Verificar permisos**:
   ```bash
   ls -la cron_setup.sh test_cron.sh
   # Deben ser ejecutables (-rwxr-xr-x)
   ```

3. **Verificar logs**:
   ```bash
   tail -50 logs/cron.log
   ```

4. **Verificar que cron está corriendo** (macOS):
   ```bash
   sudo launchctl list | grep cron
   ```

### El cron se ejecuta pero falla

1. **Ver el error en el log**:
   ```bash
   tail -50 logs/cron.log
   ```

2. **Ejecutar manualmente para ver el error**:
   ```bash
   ./test_cron.sh
   ```

3. **Verificar rutas**:
   ```bash
   which python3
   pwd
   ```

### Permisos en macOS (Catalina+)

Si recibes errores de permisos en macOS, puede que necesites dar permisos a `cron` en:

**System Preferences > Security & Privacy > Privacy > Full Disk Access**

Añadir: `/usr/sbin/cron`

---

## 📧 Notificaciones por Email (Opcional)

Si quieres recibir emails cuando el cron falle, agrega esto al inicio de tu crontab:

```cron
MAILTO=tu-email@ejemplo.com

0 8 * * 1-5 cd '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA' && /usr/bin/python3 -m seia_monitor run --once >> '/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA/logs/cron.log' 2>&1
```

⚠️ **Nota**: Requiere configurar `sendmail` en tu sistema.

---

## ✅ Checklist de Instalación

- [ ] Sistema probado manualmente: `python3 -m seia_monitor run --once`
- [ ] Test de cron ejecutado: `./test_cron.sh`
- [ ] Logs verificados: `tail -f logs/cron.log`
- [ ] Cron instalado: `./cron_setup.sh`
- [ ] Cron verificado: `crontab -l`
- [ ] Base de datos con snapshot inicial
- [ ] Webhook de Teams configurado (opcional)

---

## 📚 Recursos

- **Crontab Guru**: https://crontab.guru/ (verificador de sintaxis)
- **Documentación oficial de cron**: `man cron` o `man crontab`
- **README del proyecto**: `README.md`
- **Guía de producción**: `PRODUCCION.md`

---

## 🆘 Soporte

Si tienes problemas:

1. Ejecuta: `python3 verify.py`
2. Revisa: `logs/cron.log` y `logs/seia_monitor.log`
3. Prueba manualmente: `./test_cron.sh`
4. Verifica la configuración: `python3 -m seia_monitor config-check`

---

**Última actualización**: 2026-01-08


