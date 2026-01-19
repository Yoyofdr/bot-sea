"""
Scraper AUTO - Fachada que intenta requests y hace fallback a Playwright.
"""

from seia_monitor.config import Config
from seia_monitor.logger import get_logger
from seia_monitor.models import Project, ScrapeMeta
from seia_monitor.scraper_requests import scrape_with_requests
from seia_monitor.scraper_playwright import scrape_with_playwright

logger = get_logger("scraper")


def scrape_seia(config: Config) -> tuple[list[Project], ScrapeMeta]:
    """
    Scraping inteligente con fallback automático.
    
    Estrategia:
    1. Si mode='requests' o 'auto': intenta con requests
    2. Si requests falla y mode='auto': fallback a playwright
    3. Si mode='playwright': usa playwright directamente
    
    Args:
        config: Configuración del sistema
    
    Returns:
        Tupla de (lista de proyectos, metadata)
    
    Raises:
        Exception: Si ambos métodos fallan o el método forzado falla
    """
    mode = config.SCRAPE_MODE.lower()
    
    # Modo solo Playwright
    if mode == 'playwright':
        logger.info("Usando Playwright (modo forzado)")
        return scrape_with_playwright(config)
    
    # Modo solo requests
    if mode == 'requests':
        logger.info("Usando requests (modo forzado)")
        return scrape_with_requests(config)
    
    # Modo AUTO: intentar requests, fallback a playwright
    if mode == 'auto':
        logger.info("Modo AUTO: intentando primero con requests")
        
        try:
            projects, meta = scrape_with_requests(config)
            
            # Validar que el resultado es razonable
            if meta.success and len(projects) > 0:
                logger.info(
                    f"✓ Requests exitoso: {len(projects)} proyectos "
                    f"en {meta.pages_scraped} páginas"
                )
                return projects, meta
            else:
                logger.warning(
                    "Requests no retornó resultados válidos, "
                    "intentando con Playwright"
                )
        
        except Exception as e:
            logger.warning(f"Requests falló: {e}")
            logger.info("Fallback automático a Playwright")
        
        # Fallback a Playwright
        try:
            logger.info("Iniciando scraping con Playwright...")
            projects, meta = scrape_with_playwright(config)
            
            if meta.success and len(projects) > 0:
                logger.info(
                    f"✓ Playwright exitoso: {len(projects)} proyectos "
                    f"en {meta.pages_scraped} páginas"
                )
                return projects, meta
            else:
                raise Exception("Playwright no retornó resultados válidos")
        
        except Exception as e:
            error_msg = f"Ambos métodos fallaron. Último error: {e}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    # Modo desconocido
    raise ValueError(
        f"SCRAPE_MODE inválido: {mode}. "
        "Valores válidos: 'auto', 'requests', 'playwright'"
    )






