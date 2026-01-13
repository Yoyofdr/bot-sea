#!/bin/bash
# Script de prueba para verificar que el comando cron funciona correctamente

set -e

PROJECT_DIR="/Users/rodrigofernandezdelrio/Desktop/Proyecto SEA"
PYTHON_BIN="/usr/bin/python3"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  TEST DE CRON - Simulando ejecución automática"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Este script ejecuta el mismo comando que usará cron,"
echo "para verificar que todo funciona correctamente."
echo ""

# Verificar que el directorio de logs existe
if [ ! -d "$PROJECT_DIR/logs" ]; then
    echo "⚠️  Creando directorio logs..."
    mkdir -p "$PROJECT_DIR/logs"
fi

# Crear archivo de log de prueba
TEST_LOG="$PROJECT_DIR/logs/cron_test.log"

echo "📝 Ejecutando comando:"
echo "   cd '$PROJECT_DIR' && $PYTHON_BIN -m seia_monitor run --once"
echo ""
echo "📄 Log: $TEST_LOG"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ejecutar el comando como lo haría cron
cd "$PROJECT_DIR" && $PYTHON_BIN -m seia_monitor run --once >> "$TEST_LOG" 2>&1

EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Comando ejecutado exitosamente (exit code: $EXIT_CODE)"
else
    echo "❌ Error al ejecutar el comando (exit code: $EXIT_CODE)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Últimas 20 líneas del log:"
echo ""
tail -20 "$TEST_LOG"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ¡Todo listo para instalar el cron!"
    echo ""
    echo "Para instalar ejecuta:"
    echo "   ./cron_setup.sh"
    echo ""
else
    echo "⚠️  Hay un error. Revisa el log completo:"
    echo "   cat $TEST_LOG"
    echo ""
fi


