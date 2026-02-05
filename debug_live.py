
import logging
import sys
from seia_monitor.scraper_playwright import SEIAPlaywrightScraper
from seia_monitor.scraper_detail import scrape_project_details
from seia_monitor.config import Config

# Config logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("debug_repro")

def debug_latest_approved():
    config = Config()
    
    # 1. Scrape listing to find latest approved projects
    logger.info("Scraping listing to find latest projects...")
    scraper = SEIAPlaywrightScraper(config)
    projects, _ = scraper.scrape()
    
    if not projects:
        logger.error("No projects found!")
        return
        
    # Take the top 3 projects
    latest_projects = projects[:3]
    logger.info(f"Found {len(latest_projects)} projects. Checking details for top 3...")
    
    for p in latest_projects:
        logger.info(f"\n--- Checking Project: {p.nombre_proyecto} (ID: {p.project_id}) ---")
        logger.info(f"URL Original: {p.url_detalle}")
        
        try:
            # 2. Scrape details using our logic
            details = scrape_project_details(p.url_detalle)
            
            # 3. Print what we found
            print(f"  > Nombre Ext: {details.nombre_completo}")
            print(f"  > Tipo: {details.tipo_proyecto}")
            print(f"  > Inversión: {details.monto_inversion}")
            print(f"  > Descripción (len={len(details.descripcion_completa or '')}): {details.descripcion_completa[:100]}...")
            print(f"  > Titular: {details.titular_nombre}")
            print(f"  > Email: {details.titular_email}")
            print(f"  > Rep Legal: {details.rep_legal_nombre}")
            print(f"  > Email RL: {details.rep_legal_email}")
            
            # Verify if it failed
            if not details.monto_inversion or not details.titular_nombre:
                logger.error("  ❌ FAILED to extract key fields!")
            else:
                logger.info("  ✅ Extraction looks clean.")
                
        except Exception as e:
            logger.error(f"  ❌ Exception scaping details: {e}")

if __name__ == "__main__":
    debug_latest_approved()
