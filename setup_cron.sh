#!/bin/bash

# Script para configurar cron job para SEIA Monitor

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH=$(which python3)

echo "🔧 CONFIGURACIÓN DE CRON JOB"
echo "=============================="
echo ""
echo "Directorio del proyecto: $PROJECT_DIR"
echo "Python: $PYTHON_PATH"
echo ""

# Crear entrada de cron (ejecutar a las 08:00 AM todos los días)
CRON_COMMAND="0 8 * * * cd $PROJECT_DIR && $PYTHON_PATH -m seia_monitor run --once >> $PROJECT_DIR/logs/cron.log 2>&1"

echo "Comando cron que se agregará:"
echo "$CRON_COMMAND"
echo ""

# Verificar si ya existe
if crontab -l 2>/dev/null | grep -q "seia_monitor"; then
    echo "⚠️  Ya existe un cron job para seia_monitor"
    echo ""
    echo "Cron jobs actuales:"
    crontab -l | grep seia_monitor
    echo ""
    read -p "¿Deseas reemplazarlo? (s/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "Cancelado"
        exit 0
    fi
    
    # Remover entrada anterior
    crontab -l | grep -v "seia_monitor" | crontab -
fi

# Agregar nueva entrada
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

echo ""
echo "✅ Cron job configurado exitosamente"
echo ""
echo "📋 Cron jobs actuales para seia_monitor:"
crontab -l | grep seia_monitor
echo ""
echo "🕐 El sistema se ejecutará automáticamente todos los días a las 08:00 AM"
echo ""
echo "Para ver los logs: tail -f $PROJECT_DIR/logs/cron.log"
echo "Para remover el cron: crontab -e (y eliminar la línea)"
echo ""

