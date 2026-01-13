#!/bin/bash
# Script para configurar el cron de monitoreo SEIA
# Este script muestra las instrucciones y puede instalar automáticamente

set -e

PROJECT_DIR="/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA"
PYTHON_BIN="/usr/bin/python3"
USER=$(whoami)

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  CONFIGURACIÓN DE CRON - SEIA MONITOR${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${BLUE}📁 Directorio del proyecto:${NC} $PROJECT_DIR"
echo -e "${BLUE}🐍 Python:${NC} $PYTHON_BIN"
echo -e "${BLUE}👤 Usuario:${NC} $USER"
echo ""

# Crear entrada de cron (8:00 AM Chile, lunes a viernes)
CRON_ENTRY="0 8 * * 1-5 cd '$PROJECT_DIR' && $PYTHON_BIN -m seia_monitor run --once >> '$PROJECT_DIR/logs/cron.log' 2>&1"

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  OPCIÓN 1: Instalación Automática${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Se instalará el siguiente cron job:"
echo ""
echo -e "${GREEN}$CRON_ENTRY${NC}"
echo ""
echo "⏰ Horario: Lunes a Viernes a las 8:00 AM (America/Santiago)"
echo "📝 Logs: $PROJECT_DIR/logs/cron.log"
echo ""

read -p "¿Deseas instalar automáticamente? (s/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[SsYy]$ ]]; then
    echo ""
    echo "📥 Instalando cron job..."
    
    # Verificar si ya existe
    if crontab -l 2>/dev/null | grep -q "seia_monitor"; then
        echo -e "${YELLOW}⚠️  Ya existe un cron job para seia_monitor${NC}"
        read -p "¿Deseas reemplazarlo? (s/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
            echo "❌ Instalación cancelada"
            exit 0
        fi
        # Remover entrada anterior
        crontab -l 2>/dev/null | grep -v "seia_monitor" | crontab -
    fi
    
    # Agregar nueva entrada
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    
    echo ""
    echo -e "${GREEN}✅ ¡Cron job instalado exitosamente!${NC}"
    echo ""
    echo "Para verificar:"
    echo "  crontab -l"
    echo ""
else
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  OPCIÓN 2: Instalación Manual${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "1. Abre el editor de crontab:"
    echo ""
    echo "   crontab -e"
    echo ""
    echo "2. Agrega la siguiente línea al final:"
    echo ""
    echo -e "${GREEN}$CRON_ENTRY${NC}"
    echo ""
    echo "3. Guarda y cierra el editor"
    echo ""
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  OTROS HORARIOS DISPONIBLES${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Cada hora (9 AM - 6 PM, lunes a viernes):"
echo "  0 9-18 * * 1-5 cd '$PROJECT_DIR' && $PYTHON_BIN -m seia_monitor run --once >> '$PROJECT_DIR/logs/cron.log' 2>&1"
echo ""
echo "Cada 30 minutos (horario laboral):"
echo "  */30 9-18 * * 1-5 cd '$PROJECT_DIR' && $PYTHON_BIN -m seia_monitor run --once >> '$PROJECT_DIR/logs/cron.log' 2>&1"
echo ""
echo "Todos los días a las 8 AM (incluye fines de semana):"
echo "  0 8 * * * cd '$PROJECT_DIR' && $PYTHON_BIN -m seia_monitor run --once >> '$PROJECT_DIR/logs/cron.log' 2>&1"
echo ""
echo "Dos veces al día (8 AM y 6 PM, lunes a viernes):"
echo "  0 8,18 * * 1-5 cd '$PROJECT_DIR' && $PYTHON_BIN -m seia_monitor run --once >> '$PROJECT_DIR/logs/cron.log' 2>&1"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  COMANDOS ÚTILES${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Ver cron jobs instalados:"
echo "  crontab -l"
echo ""
echo "Editar cron jobs:"
echo "  crontab -e"
echo ""
echo "Eliminar todos los cron jobs:"
echo "  crontab -r"
echo ""
echo "Ver logs de cron:"
echo "  tail -f '$PROJECT_DIR/logs/cron.log'"
echo ""
echo "Ver logs de la aplicación:"
echo "  tail -f '$PROJECT_DIR/logs/seia_monitor.log'"
echo ""
echo "Ejecutar manualmente:"
echo "  python3 -m seia_monitor run --once"
echo ""
echo "Verificar próxima ejecución:"
echo "  python3 -m seia_monitor status"
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ¡CONFIGURACIÓN COMPLETA!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""


