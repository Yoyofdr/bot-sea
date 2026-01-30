#!/bin/bash

################################################################################
# Script de Instalación Automática - SEIA Monitor en DigitalOcean
# 
# Este script configura todo el sistema en un Droplet nuevo de Ubuntu 22.04
################################################################################

set -e  # Detener si hay error

echo "🚀 INSTALACIÓN SEIA MONITOR - DIGITALOCEAN"
echo "=========================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. ACTUALIZAR SISTEMA
echo -e "${GREEN}[1/9] Actualizando sistema...${NC}"
sudo apt update
sudo apt upgrade -y
echo ""

# 2. INSTALAR DEPENDENCIAS BASE
echo -e "${GREEN}[2/9] Instalando dependencias base...${NC}"
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    sqlite3 \
    curl \
    wget \
    unzip \
    cron
echo ""

# 3. INSTALAR PLAYWRIGHT Y CHROMIUM
echo -e "${GREEN}[3/9] Instalando Playwright y Chromium...${NC}"
pip3 install playwright
playwright install chromium
sudo playwright install-deps chromium
echo ""

# 4. CREAR DIRECTORIO DEL PROYECTO
echo -e "${GREEN}[4/9] Configurando directorio del proyecto...${NC}"
cd ~
PROJECT_DIR="$HOME/seia-monitor"
echo "Directorio: $PROJECT_DIR"
echo ""

# 5. CLONAR REPOSITORIO (el usuario debe tener el repo listo)
echo -e "${GREEN}[5/9] Clonando repositorio...${NC}"
echo -e "${YELLOW}IMPORTANTE: Necesitas tener el código en GitHub${NC}"
echo "Por favor ingresa la URL de tu repositorio:"
read -p "URL del repo (ej: https://github.com/usuario/seia-monitor.git): " REPO_URL

if [ -d "$PROJECT_DIR" ]; then
    echo "El directorio ya existe. Eliminando..."
    rm -rf "$PROJECT_DIR"
fi

git clone "$REPO_URL" "$PROJECT_DIR"
cd "$PROJECT_DIR"
echo ""

# 6. INSTALAR DEPENDENCIAS PYTHON
echo -e "${GREEN}[6/9] Instalando dependencias Python...${NC}"
pip3 install -r requirements.txt
echo ""

# 7. CREAR ESTRUCTURA DE DIRECTORIOS
echo -e "${GREEN}[7/9] Creando estructura de directorios...${NC}"
mkdir -p data logs
chmod 755 data logs
echo ""

# 8. CONFIGURAR .env
echo -e "${GREEN}[8/9] Configurando archivo .env...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  IMPORTANTE: Debes editar el archivo .env${NC}"
    echo "Ejecuta: nano $PROJECT_DIR/.env"
    echo ""
    echo "Configuraciones necesarias:"
    echo "  - TEAMS_WEBHOOK_URL (opcional)"
    echo "  - FECHA_DESDE=01/01/2025"
    echo ""
fi
echo ""

# 9. CONFIGURAR CRON JOB
echo -e "${GREEN}[9/9] Configurando cron job...${NC}"

# Crear entrada de cron
# Crear entrada de cron (Lunes a Viernes a las 08:00 AM)
CRON_CMD="0 8 * * 1-5 cd $PROJECT_DIR && $(which python3) -m seia_monitor run --once >> $PROJECT_DIR/logs/cron.log 2>&1"

# Verificar si ya existe
if crontab -l 2>/dev/null | grep -q "seia_monitor"; then
    echo "⚠️  Cron job ya existe. Reemplazando..."
    crontab -l | grep -v "seia_monitor" | crontab -
fi

# Agregar nuevo cron
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✅ Cron job configurado para ejecutarse de LUNES a VIERNES a las 08:00 AM"
echo ""

# RESUMEN FINAL
echo ""
echo "=========================================="
echo "✅ INSTALACIÓN COMPLETADA"
echo "=========================================="
echo ""
echo "📁 Directorio: $PROJECT_DIR"
echo "🕐 Cron: Lunes a Viernes a las 08:00 AM"
echo ""
echo "📝 PRÓXIMOS PASOS:"
echo ""
echo "1. Editar configuración:"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "2. Ejecutar primera vez (prueba):"
echo "   cd $PROJECT_DIR"
echo "   python3 -m seia_monitor run --once --dry-run"
echo ""
echo "3. Ejecutar primera vez (real):"
echo "   python3 -m seia_monitor run --once"
echo ""
echo "4. Verificar cron:"
echo "   crontab -l"
echo ""
echo "5. Ver logs:"
echo "   tail -f $PROJECT_DIR/logs/seia_monitor.log"
echo ""
echo "6. Monitorear sistema:"
echo "   cd $PROJECT_DIR && ./monitorear.sh"
echo ""
echo "=========================================="
echo "🎉 ¡Sistema listo para funcionar!"
echo "=========================================="








