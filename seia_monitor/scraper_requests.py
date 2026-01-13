"""
Scraper usando requests para el SEIA.
Intenta replicar el POST del formulario con reintentos y manejo de errores.
"""

import time
import requests
from typing import Optional
from datetime import datetime

from seia_monitor.config import Config
from seia_monitor.logger import get_logger
from seia_monitor.models import Project, ScrapeMeta
from seia_monitor.parser import (
    parse_projects_from_html,
    validate_html_has_results,
    deduplicate_projects
)

logger = get_logger("scraper_requests")


class SEIARequestsScraper:
    """Scraper basado en requests con manejo de sesión y reintentos"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def _make_request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Optional[requests.Response]:
        """
        Hace una petición HTTP con reintentos exponenciales.
        
        Args:
            method: GET o POST
            url: URL objetivo
            **kwargs: Argumentos adicionales para requests
        
        Returns:
            Response o None si falla
        """
        for attempt in range(self.config.RETRY_MAX_ATTEMPTS):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=self.config.REQUEST_TIMEOUT,
                    **kwargs
                )
                
                # Manejar rate limiting
                if response.status_code == 429:
                    wait_time = self.config.RETRY_INITIAL_DELAY * (
                        self.config.RETRY_BACKOFF_FACTOR ** attempt
                    )
                    logger.warning(f"Rate limit (429), esperando {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                # Errores del servidor
                if response.status_code >= 500:
                    wait_time = self.config.RETRY_INITIAL_DELAY * (
                        self.config.RETRY_BACKOFF_FACTOR ** attempt
                    )
                    logger.warning(
                        f"Error del servidor ({response.status_code}), "
                        f"reintento {attempt + 1}/{self.config.RETRY_MAX_ATTEMPTS}"
                    )
                    time.sleep(wait_time)
                    continue
                
                # Éxito o error del cliente (no reintentar)
                response.raise_for_status()
                return response
            
            except requests.exceptions.Timeout:
                logger.warning(
                    f"Timeout en intento {attempt + 1}/{self.config.RETRY_MAX_ATTEMPTS}"
                )
                if attempt < self.config.RETRY_MAX_ATTEMPTS - 1:
                    time.sleep(self.config.RETRY_INITIAL_DELAY * (
                        self.config.RETRY_BACKOFF_FACTOR ** attempt
                    ))
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Error en petición: {e}")
                if attempt < self.config.RETRY_MAX_ATTEMPTS - 1:
                    time.sleep(self.config.RETRY_INITIAL_DELAY)
        
        return None
    
    def _fetch_page(self, page_num: int = 1) -> Optional[str]:
        """
        Obtiene una página de resultados.
        
        Args:
            page_num: Número de página (1-indexed)
        
        Returns:
            HTML de la página o None si falla
        """
        # Preparar datos del formulario
        # Estos parámetros pueden variar, ajustar según el formulario real
        form_data = {
            'fechaDesde': self.config.FECHA_DESDE,
            'pagina': str(page_num),
            # Campos adicionales comunes en formularios SEIA:
            'buscar': '1',
            'orden': 'fecha',
            # Otros posibles campos (descomentar si son necesarios):
            # 'region': '',
            # 'tipo': '',
            # 'estado': '',
        }
        
        logger.info(f"Obteniendo página {page_num}")
        
        response = self._make_request_with_retry(
            'POST',
            self.config.SEIA_BASE_URL,
            data=form_data,
            allow_redirects=True
        )
        
        if not response:
            logger.error(f"No se pudo obtener página {page_num}")
            return None
        
        if response.status_code != 200:
            logger.error(f"Status code {response.status_code} en página {page_num}")
            return None
        
        html = response.text
        
        # Validar que tenga contenido
        if not validate_html_has_results(html):
            logger.warning(f"Página {page_num} no contiene tabla de resultados válida")
            return None
        
        return html
    
    def _detect_total_pages(self, html: str) -> int:
        """
        Detecta el número total de páginas desde el HTML.
        
        Busca patrones como:
        - "Página 1 de 5"
        - "1-20 de 142 resultados"
        
        Args:
            html: HTML de la primera página
        
        Returns:
            Número de páginas detectadas (mínimo 1)
        """
        import re
        
        # Patrón: "Página X de Y"
        match = re.search(r'P[aá]gina\s+\d+\s+de\s+(\d+)', html, re.IGNORECASE)
        if match:
            total = int(match.group(1))
            logger.info(f"Detectadas {total} páginas totales")
            return total
        
        # Patrón: "X-Y de Z resultados"
        match = re.search(r'(\d+)-(\d+)\s+de\s+(\d+)\s+resultado', html, re.IGNORECASE)
        if match:
            total_items = int(match.group(3))
            items_per_page = int(match.group(2)) - int(match.group(1)) + 1
            total_pages = (total_items + items_per_page - 1) // items_per_page
            logger.info(f"Detectadas {total_pages} páginas ({total_items} items)")
            return total_pages
        
        # Si no se detecta, asumir 1 página
        logger.info("No se detectó paginación, asumiendo 1 página")
        return 1
    
    def scrape(self) -> tuple[list[Project], ScrapeMeta]:
        """
        Ejecuta el scraping completo con paginación.
        
        Returns:
            Tupla de (proyectos, metadata)
        """
        start_time = time.time()
        all_projects = []
        errors = []
        pages_scraped = 0
        
        try:
            # Obtener primera página
            html = self._fetch_page(1)
            if not html:
                raise Exception("No se pudo obtener la primera página")
            
            # Parsear proyectos de la primera página
            projects = parse_projects_from_html(html)
            all_projects.extend(projects)
            pages_scraped = 1
            
            logger.info(f"Primera página: {len(projects)} proyectos")
            
            # Detectar total de páginas
            total_pages = self._detect_total_pages(html)
            total_pages = min(total_pages, self.config.MAX_PAGES)
            
            # Obtener páginas restantes
            for page_num in range(2, total_pages + 1):
                # Rate limiting
                time.sleep(self.config.RATE_LIMIT_DELAY)
                
                html = self._fetch_page(page_num)
                if not html:
                    error_msg = f"Falló página {page_num}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
                
                projects = parse_projects_from_html(html)
                
                # Detección de loop infinito (mismos IDs)
                new_ids = {p.project_id for p in projects}
                existing_ids = {p.project_id for p in all_projects}
                
                if new_ids.issubset(existing_ids):
                    logger.warning(
                        f"Página {page_num} tiene los mismos proyectos, "
                        "deteniendo paginación"
                    )
                    break
                
                all_projects.extend(projects)
                pages_scraped += 1
                
                logger.info(f"Página {page_num}: {len(projects)} proyectos")
                
                # Límite de seguridad
                if len(all_projects) >= self.config.MAX_PROJECTS_PER_RUN:
                    logger.warning("Alcanzado límite máximo de proyectos")
                    break
            
            # Deduplicar
            all_projects = deduplicate_projects(all_projects)
            
            duration = time.time() - start_time
            
            meta = ScrapeMeta(
                method='requests',
                pages_scraped=pages_scraped,
                total_projects=len(all_projects),
                duration_seconds=duration,
                errors=errors,
                success=True
            )
            
            logger.info(
                f"Scraping completado: {len(all_projects)} proyectos "
                f"en {pages_scraped} páginas ({duration:.1f}s)"
            )
            
            return all_projects, meta
        
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Error en scraping con requests: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            
            meta = ScrapeMeta(
                method='requests',
                pages_scraped=pages_scraped,
                total_projects=len(all_projects),
                duration_seconds=duration,
                errors=errors,
                success=False
            )
            
            raise Exception(error_msg) from e


def scrape_with_requests(config: Config) -> tuple[list[Project], ScrapeMeta]:
    """
    Función de entrada para scraping con requests.
    
    Args:
        config: Configuración del sistema
    
    Returns:
        Tupla de (proyectos, metadata)
    """
    scraper = SEIARequestsScraper(config)
    return scraper.scrape()


