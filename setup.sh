#!/bin/bash
# Script de setup para el sistema SEIA Monitor

set -e

echo "======================================"
echo "SEIA Monitor - Setup"
echo "======================================"
echo ""

# Verificar Python
echo "1. Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION encontrado"
echo ""

# Crear entorno virtual
echo "2. Creando entorno virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Entorno virtual creado"
else
    echo "✓ Entorno virtual ya existe"
fi
echo ""

# Activar entorno virtual
echo "3. Activando entorno virtual..."
source venv/bin/activate
echo "✓ Entorno virtual activado"
echo ""

# Instalar dependencias
echo "4. Instalando dependencias..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✓ Dependencias instaladas"
echo ""

# Instalar Playwright
echo "5. Instalando navegador Playwright..."
playwright install chromium
echo "✓ Playwright instalado"
echo ""

# Configurar .env
echo "6. Configurando variables de entorno..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Archivo .env creado desde .env.example"
    echo ""
    echo "⚠️  IMPORTANTE: Edita el archivo .env con tu configuración:"
    echo "   - TEAMS_WEBHOOK_URL: URL del webhook de Teams"
    echo "   - Otras variables según necesites"
    echo ""
    echo "   Ejecuta: nano .env"
else
    echo "✓ Archivo .env ya existe"
fi
echo ""

# Crear directorios
echo "7. Creando directorios..."
mkdir -p data/debug
mkdir -p logs
echo "✓ Directorios creados"
echo ""

# Ejecutar tests
echo "8. Ejecutando tests..."
if pytest -q; then
    echo "✓ Tests pasaron correctamente"
else
    echo "⚠️  Algunos tests fallaron (puede ser normal en primera instalación)"
fi
echo ""

echo "======================================"
echo "✅ Setup completado!"
echo "======================================"
echo ""
echo "Próximos pasos:"
echo "1. Editar .env con tu webhook de Teams:"
echo "   nano .env"
echo ""
echo "2. Probar el webhook:"
echo "   python -m seia_monitor test-teams"
echo ""
echo "3. Ejecutar en modo dry-run:"
echo "   python -m seia_monitor run --once --dry-run"
echo ""
echo "4. Ver más comandos:"
echo "   python -m seia_monitor --help"
echo ""








