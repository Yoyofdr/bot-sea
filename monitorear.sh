#!/bin/bash

# Script para monitorear el estado del sistema SEIA

echo "📊 MONITOR SEIA - Estado del Sistema"
echo "===================================="
echo ""

# Base de datos
if [ -f "data/seia_monitor.db" ]; then
    PROYECTOS=$(sqlite3 data/seia_monitor.db "SELECT COUNT(*) FROM projects_current" 2>/dev/null || echo "Error")
    APROBADOS=$(sqlite3 data/seia_monitor.db "SELECT COUNT(*) FROM projects_current WHERE estado_normalizado='aprobado'" 2>/dev/null || echo "Error")
    EN_CALIFICACION=$(sqlite3 data/seia_monitor.db "SELECT COUNT(*) FROM projects_current WHERE estado_normalizado='en_calificacion_activo'" 2>/dev/null || echo "Error")
    
    echo "📋 Base de Datos:"
    echo "   Total proyectos: $PROYECTOS"
    echo "   Aprobados: $APROBADOS"
    echo "   En Calificación (Activo): $EN_CALIFICACION"
    echo ""
else
    echo "❌ Base de datos no encontrada"
    echo ""
fi

# Logs recientes
if [ -f "logs/seia_monitor.log" ]; then
    echo "📝 Últimas líneas del log:"
    tail -5 logs/seia_monitor.log
    echo ""
else
    echo "⚠️  No hay logs disponibles"
    echo ""
fi

# Cron job
echo "🕐 Cron Job:"
if crontab -l 2>/dev/null | grep -q "seia_monitor"; then
    echo "   ✅ Configurado"
    crontab -l | grep seia_monitor | head -1
else
    echo "   ❌ No configurado"
    echo "   Ejecuta: ./setup_cron.sh"
fi
echo ""

# Webhook de Teams
if grep -q "^TEAMS_WEBHOOK_URL=https" .env 2>/dev/null; then
    echo "📢 Webhook de Teams: ✅ Configurado"
else
    echo "📢 Webhook de Teams: ⚠️  No configurado"
fi
echo ""

echo "===================================="
echo "Para ejecutar manualmente: python3 -m seia_monitor run --once"
echo "Para ver logs completos: tail -f logs/seia_monitor.log"

