#!/usr/bin/env python3
"""
Script de verificación del sistema SEIA Monitor.
Verifica que todos los componentes estén correctamente instalados.
"""

import sys
import os
from pathlib import Path

# Colores para terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text.center(60)}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def check_mark(success):
    return f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"

def main():
    print_header("SEIA Monitor - Verificación del Sistema")
    
    errors = []
    warnings = []
    
    # 1. Verificar Python version
    print(f"1. Verificando versión de Python...")
    py_version = sys.version_info
    if py_version >= (3, 10):
        print(f"   {check_mark(True)} Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        print(f"   {check_mark(False)} Python {py_version.major}.{py_version.minor} (se requiere 3.10+)")
        errors.append("Python 3.10+ requerido")
    
    # 2. Verificar módulos
    print(f"\n2. Verificando módulos instalados...")
    modules = [
        "requests",
        "beautifulsoup4",
        "playwright",
        "dotenv",
        "apscheduler",
        "typer",
        "rich",
        "pytz",
        "lxml",
        "pytest"
    ]
    
    for module in modules:
        try:
            if module == "beautifulsoup4":
                __import__("bs4")
            elif module == "dotenv":
                __import__("dotenv")
            else:
                __import__(module)
            print(f"   {check_mark(True)} {module}")
        except ImportError:
            print(f"   {check_mark(False)} {module}")
            errors.append(f"Módulo {module} no instalado")
    
    # 3. Verificar estructura del proyecto
    print(f"\n3. Verificando estructura del proyecto...")
    base_dir = Path(__file__).parent
    
    required_files = [
        "seia_monitor/__init__.py",
        "seia_monitor/config.py",
        "seia_monitor/cli.py",
        "seia_monitor/runner.py",
        "seia_monitor/scraper.py",
        "seia_monitor/storage.py",
        "requirements.txt",
        "README.md",
        ".env.example"
    ]
    
    for file_path in required_files:
        full_path = base_dir / file_path
        exists = full_path.exists()
        print(f"   {check_mark(exists)} {file_path}")
        if not exists:
            errors.append(f"Archivo faltante: {file_path}")
    
    # 4. Verificar directorios
    print(f"\n4. Verificando directorios...")
    dirs = ["data", "logs", "tests"]
    for dir_name in dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            print(f"   {check_mark(False)} {dir_name}/ (será creado automáticamente)")
            warnings.append(f"Directorio {dir_name} no existe (se creará al ejecutar)")
        else:
            print(f"   {check_mark(True)} {dir_name}/")
    
    # 5. Verificar .env
    print(f"\n5. Verificando configuración...")
    env_path = base_dir / ".env"
    if env_path.exists():
        print(f"   {check_mark(True)} .env existe")
        
        # Leer y verificar variables importantes
        with open(env_path) as f:
            env_content = f.read()
            
        important_vars = [
            "SEIA_BASE_URL",
            "FECHA_DESDE",
            "TEAMS_WEBHOOK_URL"
        ]
        
        for var in important_vars:
            if var in env_content:
                if "YOUR_WEBHOOK_URL_HERE" in env_content and var == "TEAMS_WEBHOOK_URL":
                    print(f"   {YELLOW}⚠{RESET} {var} no configurado (usar .env.example como guía)")
                    warnings.append(f"{var} no está configurado correctamente")
                else:
                    print(f"   {check_mark(True)} {var} configurado")
            else:
                print(f"   {check_mark(False)} {var} faltante")
                warnings.append(f"{var} no está en .env")
    else:
        print(f"   {check_mark(False)} .env no existe")
        errors.append("Archivo .env no existe (copiar desde .env.example)")
    
    # 6. Verificar importación del módulo
    print(f"\n6. Verificando módulo seia_monitor...")
    try:
        sys.path.insert(0, str(base_dir))
        import seia_monitor
        print(f"   {check_mark(True)} Módulo se puede importar")
        print(f"   {check_mark(True)} Versión: {seia_monitor.__version__}")
    except ImportError as e:
        print(f"   {check_mark(False)} Error importando módulo: {e}")
        errors.append("No se puede importar seia_monitor")
    
    # 7. Verificar Playwright
    print(f"\n7. Verificando Playwright...")
    try:
        from playwright.sync_api import sync_playwright
        print(f"   {check_mark(True)} Playwright instalado")
        
        # Verificar navegador
        playwright_browsers = Path.home() / ".cache" / "ms-playwright"
        if playwright_browsers.exists():
            print(f"   {check_mark(True)} Navegadores instalados")
        else:
            print(f"   {YELLOW}⚠{RESET} Navegadores no instalados")
            warnings.append("Ejecutar: playwright install chromium")
    except ImportError:
        print(f"   {check_mark(False)} Playwright no instalado")
        errors.append("Playwright no instalado")
    
    # 8. Resumen
    print_header("Resumen")
    
    if not errors and not warnings:
        print(f"{GREEN}✓ Todas las verificaciones pasaron exitosamente!{RESET}\n")
        print("Próximos pasos:")
        print("  1. Si .env no está configurado: nano .env")
        print("  2. Probar webhook: python -m seia_monitor test-teams")
        print("  3. Ejecutar dry-run: python -m seia_monitor run --once --dry-run")
        return 0
    
    if warnings:
        print(f"{YELLOW}⚠ Advertencias ({len(warnings)}):{RESET}")
        for warning in warnings:
            print(f"  • {warning}")
        print()
    
    if errors:
        print(f"{RED}✗ Errores ({len(errors)}):{RESET}")
        for error in errors:
            print(f"  • {error}")
        print()
        print("Para instalar dependencias:")
        print("  pip install -r requirements.txt")
        print("  playwright install chromium")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())


