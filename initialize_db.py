
import sys
import time
from datetime import datetime
from seia_monitor.config import Config
from seia_monitor.storage import SEIAStorage
from seia_monitor.scraper import scrape_seia
from seia_monitor.scraper_detail import scrape_project_details
from seia_monitor.models import Project

def initialize_clean_approved_db():
    config = Config()
    storage = SEIAStorage()
    
    print("Iniciando reconstrucción de base de datos (SOLO APROBADOS)...")
    
    # 1. Limpiar BD actual (pero de forma controlada)
    # Ya borramos el archivo antes, pero nos aseguramos de que SEIAStorage inicialice uno nuevo
    
    # 2. Scrapear SEIA
    print("Paso 1: Scraping de proyectos desde SEIA (esto puede usar Playwright)...")
    try:
        all_projects, scrape_meta = scrape_seia(config)
        print(f"✓ Scrapeados {len(all_projects)} proyectos totales.")
    except Exception as e:
        print(f"✗ Error durante el scraping: {e}")
        return

    # 3. Filtrar SOLO APROBADOS
    print("Paso 2: Filtrando solo proyectos con estado 'Aprobado'...")
    approved_projects = [p for p in all_projects if p.estado_normalizado == "aprobado"]
    print(f"✓ Seleccionados {len(approved_projects)} proyectos aprobados.")

    # 4. Guardar en la base de datos
    print("Paso 3: Guardando proyectos en la base de datos...")
    storage.save_projects(approved_projects, validate=True)
    print("✓ Proyectos guardados.")

    # 5. Opcional: Scrapear detalles para que mañana el reporte sea completo
    # Solo tomamos los 10 primeros para no tardar una eternidad en esta inicialización
    print("Paso 4: Scrapeando detalles de los 5 más recientes (para prueba de mañana)...")
    for i, p in enumerate(approved_projects[:5]):
        if p.url_detalle:
            try:
                print(f"  [{i+1}/5] Scrapeando detalles de: {p.nombre_proyecto[:50]}...")
                details = scrape_project_details(p.url_detalle)
                if details:
                    storage.save_project_details(details)
            except Exception as e:
                print(f"  ✗ Error en detalles: {e}")
            time.sleep(2)

    print("\n====================================================")
    print("✓ RECONSTRUCCIÓN COMPLETADA EXITOSAMENTE")
    print(f"  Base de datos: {config.get_db_path()}")
    print(f"  Proyectos base guardados: {len(approved_projects)}")
    print("  MENSAJE: No se envió ningún correo a los clientes.")
    print("====================================================")

if __name__ == "__main__":
    initialize_clean_approved_db()
