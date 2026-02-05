
import logging
import sys
from seia_monitor.scraper_detail import scrape_project_details

# Config logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("debug_specific")

def debug_specific_projects():
    ids = ["2167639261", "2167609791"]
    
    for pid in ids:
        url = f"https://seia.sea.gob.cl/expediente/ficha/fichaPrincipal.php?modo=normal&id_expediente={pid}"
        logger.info(f"\n--- Checking Project ID: {pid} ---")
        
        try:
            details = scrape_project_details(url)
            
            print(f"DETAILS_START_{pid}")
            print(f"Nombre: {details.nombre_completo}")
            print(f"Monto: {details.monto_inversion}")
            print(f"Desc: {details.descripcion_completa[:50]}...")
            print(f"Titular: {details.titular_nombre}")
            print(f"Email: {details.titular_email}")
            print(f"RL Nombre: {details.rep_legal_nombre}")
            print(f"RL Email: {details.rep_legal_email}")
            print(f"DETAILS_END_{pid}")
            
        except Exception as e:
            logger.error(f"Failed to scrape {pid}: {e}")

if __name__ == "__main__":
    debug_specific_projects()
