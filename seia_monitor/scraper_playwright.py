"""
Scraper usando Playwright para el SEIA.
Usado como fallback cuando requests no funciona.
"""

import time
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

from seia_monitor.config import Config
from seia_monitor.logger import get_logger
from seia_monitor.models import Project, ScrapeMeta
from seia_monitor.parser import (
    parse_projects_from_html,
    validate_html_has_results,
    deduplicate_projects
)

logger = get_logger("scraper_playwright")


class SEIAPlaywrightScraper:
    """Scraper basado en Playwright para navegación completa del sitio"""
    
    def __init__(self, config: Config):
        self.config = config
        self.debug_dir = config.BASE_DIR / "data" / "debug"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
    
    def _save_debug_info(self, page: Page, prefix: str):
        """Guarda screenshot y HTML para debugging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Screenshot
            screenshot_path = self.debug_dir / f"{prefix}_{timestamp}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"Screenshot guardado: {screenshot_path}")
            
            # HTML
            html_path = self.debug_dir / f"{prefix}_{timestamp}.html"
            html_path.write_text(page.content(), encoding='utf-8')
            logger.info(f"HTML guardado: {html_path}")
        except Exception as e:
            logger.error(f"Error guardando debug info: {e}")
    
    def _fill_and_submit_form(self, page: Page) -> bool:
        """
        Llena y envía el formulario de búsqueda de proyectos aprobados.
        
        Flujo correcto:
        1. Click en "Nueva Búsqueda" para mostrar el formulario
        2. Seleccionar "Aprobado" (value=4) en projectStatus[]
        3. Click en botón de búsqueda
        
        Args:
            page: Página de Playwright
        
        Returns:
            True si se envió exitosamente
        """
        try:
            # Esperar que cargue la página
            page.wait_for_load_state('domcontentloaded')
            time.sleep(2)
            
            # PASO 1: Click en "Nueva Búsqueda" para mostrar el formulario
            try:
                logger.info("Haciendo click en 'Nueva Búsqueda'...")
                page.click('button:has-text("Nueva Búsqueda")')
                time.sleep(3)  # Esperar a que aparezca el formulario
                logger.info("✓ Formulario de búsqueda desplegado")
            except Exception as e:
                logger.warning(f"No se pudo hacer click en 'Nueva Búsqueda': {e}")
                logger.warning("Intentando continuar de todos modos...")
            
            # PASO 2: Seleccionar "Aprobado" (value=4) en projectStatus[]
            # Usamos JavaScript porque page.select_option() da timeout
            estado_selected = False
            try:
                logger.info("Seleccionando 'Aprobado' con JavaScript...")
                result = page.evaluate("""() => {
                    const select = document.querySelector('select[name="projectStatus[]"]');
                    if (!select) return 'Selector no encontrado';
                    select.value = '4';
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                    return 'OK: ' + select.value;
                }""")
                logger.info(f"✓ Estado 'Aprobado' seleccionado via JS: {result}")
                estado_selected = True
                time.sleep(1)  # Dar tiempo para que el cambio se procese
            except Exception as e:
                logger.warning(f"No se pudo seleccionar estado 'Aprobado': {e}")
                logger.warning("Continuando de todos modos...")
            
            if not estado_selected:
                logger.warning("⚠️ ADVERTENCIA: No se seleccionó filtro de Aprobado")
                logger.warning("   Los resultados incluirán proyectos de todos los estados")
            
            # PASO 3: Buscar y clickear botón de búsqueda
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Buscar")',
                'button:has-text("Consultar")',
                'input[value*="Buscar"]',
                '#btnBuscar',
                'input[id="btnBuscar"]',
            ]
            
            for selector in submit_selectors:
                try:
                    button = page.query_selector(selector)
                    if button:
                        logger.debug(f"Botón submit encontrado: {selector}")
                        button.click()
                        logger.info("✓ Formulario enviado")
                        
                        # Esperar que carguen los resultados
                        page.wait_for_load_state('networkidle', timeout=30000)
                        return True
                except PlaywrightTimeout:
                    logger.warning("Timeout esperando resultados")
                except Exception as e:
                    logger.debug(f"Selector {selector} no funcionó: {e}")
                    continue
            
            # Si no encontramos submit, tal vez ya están los resultados
            logger.warning("No se encontró botón submit, verificando si ya hay resultados")
            return True
        
        except Exception as e:
            logger.error(f"Error llenando formulario: {e}")
            return False
    
    def _has_next_page(self, page: Page) -> bool:
        """
        Verifica si hay una página siguiente disponible.
        
        Args:
            page: Página de Playwright
        
        Returns:
            True si hay siguiente página
        """
        try:
            # Selector específico de DataTables para el botón "Next"
            next_button = page.query_selector('button.dt-paging-button.next')
            if not next_button:
                logger.debug("No se encontró botón next de DataTables")
                return False
            
            # Verificar que no esté deshabilitado
            classes = next_button.get_attribute('class') or ''
            is_disabled = 'disabled' in classes
            
            if is_disabled:
                logger.debug("Botón next está deshabilitado - última página")
                return False
            
            return True
        except Exception as e:
            logger.debug(f"Error verificando página siguiente: {e}")
            return False
    
    def _go_to_next_page(self, page: Page) -> bool:
        """
        Navega a la siguiente página de resultados.
        
        Args:
            page: Página de Playwright
        
        Returns:
            True si navegó exitosamente
        """
        try:
            # Selector específico de DataTables
            next_button = page.query_selector('button.dt-paging-button.next')
            if not next_button:
                logger.warning("No se encontró botón next de DataTables")
                return False
            
            # Verificar que no esté deshabilitado
            classes = next_button.get_attribute('class') or ''
            if 'disabled' in classes:
                logger.info("Botón next deshabilitado - última página alcanzada")
                return False
            
            # Capturar info actual ANTES del click
            try:
                info_before = page.locator('div.dt-info').inner_text()
                logger.debug(f"Info antes del click: {info_before}")
            except:
                info_before = ""
            
            logger.info("Haciendo click en botón 'Siguiente' de DataTables")
            
            # Click en el botón
            next_button.click()
            
            # Esperar a que DataTables procese el click (observar cambio en dt-info)
            # DataTables hace recarga AJAX, el indicador de página debe cambiar
            logger.debug("Esperando cambio en indicador de página...")
            
            max_wait = 15  # 15 segundos máximo
            page_changed = False
            
            for i in range(max_wait):
                time.sleep(1)
                try:
                    info_after = page.locator('div.dt-info').inner_text()
                    if info_after != info_before:
                        logger.info(f"✓ Página siguiente cargada: {info_after}")
                        page_changed = True
                        break
                except:
                    pass
            
            if not page_changed:
                logger.warning("⚠️  El indicador de página no cambió después del click")
                return False
            
            # Esperar un poco más para que las filas se rendericen
            time.sleep(2)
            
            # Verificar que haya filas
            page.wait_for_selector('table#datatable-proyectos tbody tr', timeout=10000)
            
            return True
            
        except Exception as e:
            logger.error(f"Error navegando a página siguiente: {e}")
            return False
    
    def scrape(self) -> tuple[list[Project], ScrapeMeta]:
        """
        Ejecuta el scraping completo usando Playwright.
        
        Returns:
            Tupla de (proyectos, metadata)
        """
        start_time = time.time()
        all_projects = []
        errors = []
        pages_scraped = 0
        
        with sync_playwright() as p:
            try:
                # Lanzar navegador con configuración anti-WAF
                browser = p.chromium.launch(
                    headless=self.config.PLAYWRIGHT_HEADLESS,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process'
                    ]
                )
                
                # Crear contexto con headers realistas para evadir WAF
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='es-CL',
                    timezone_id='America/Santiago',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                )
                
                page = context.new_page()
                
                # Inyectar script para ocultar webdriver
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                # Navegar a la página
                logger.info(f"Navegando a {self.config.SEIA_BASE_URL}")
                page.goto(self.config.SEIA_BASE_URL, timeout=60000)
                
                # Llenar y enviar formulario
                if not self._fill_and_submit_form(page):
                    raise Exception("No se pudo enviar el formulario")
                
                # Esperar a que se cargue la tabla de resultados (DataTables con AJAX)
                try:
                    # Esperar a que aparezca al menos una fila en la tabla
                    page.wait_for_selector('table tbody tr', timeout=30000)
                    logger.info("Tabla de resultados cargada")
                except PlaywrightTimeout:
                    logger.warning("Timeout esperando tabla, continuando con lo que hay")
                
                # CRÍTICO: Cambiar selector de DataTables a 100 resultados por página
                try:
                    logger.info("Cambiando selector a 100...")
                    page.wait_for_selector('select[name="datatable-proyectos_length"]', timeout=10000)
                    
                    # Método: Cambiar el select con Playwright (estándar) y esperar pacientemente
                    page.select_option('select[name="datatable-proyectos_length"]', value='100')
                    logger.info("✓ Selector cambiado a 100")
                    
                    # Esperar generosamente a que DataTables procese el cambio
                    # DataTables hace petición AJAX que puede tardar
                    logger.info("Esperando recarga de DataTables (hasta 30 segundos)...")
                    
                    max_wait = 30  #30 segundos máximo
                    success = False
                    last_info = ""
                    
                    for i in range(max_wait):
                        time.sleep(1)
                        try:
                            info_text = page.locator('div.dt-info').inner_text()
                            if info_text != last_info:
                                logger.debug(f"  Info cambió: {info_text}")
                                last_info = info_text
                            
                            # Verificar que muestre 100 registros (o todos si son menos)
                            if '-' in info_text and 'de' in info_text:
                                try:
                                    parts = info_text.split('-')
                                    second_num = int(parts[1].split('de')[0].strip())
                                    total = int(parts[1].split('de')[1].strip())
                                    
                                    # Éxito si muestra 100 O si muestra todos (menos de 100)
                                    if second_num >= 100 or second_num == total:
                                        logger.info(f"✓ DataTables recargado: {info_text}")
                                        success = True
                                        break
                                except ValueError:
                                    pass
                        except Exception as e:
                            pass
                    
                    if not success:
                        logger.warning(f"⚠️  DataTables no recargó a 100. Última info: {last_info}")
                        logger.warning("   Continuando con paginación de 10 en 10...")
                    
                    # Esperar un poco más y contar filas
                    time.sleep(2)
                    row_count = page.locator('table#datatable-proyectos tbody tr').count()
                    logger.info(f"Filas visibles en HTML: {row_count}")
                    
                except Exception as e:
                    logger.error(f"Error cambiando selector a 100: {e}")
                    logger.warning("Continuando con configuración por defecto (10/página)")
                
                # Extraer resultados de la primera página
                html = page.content()
                
                if not validate_html_has_results(html):
                    self._save_debug_info(page, "no_results")
                    raise Exception("No se encontraron resultados en la página")
                
                projects = parse_projects_from_html(html)
                all_projects.extend(projects)
                pages_scraped = 1
                
                logger.info(f"Primera página: {len(projects)} proyectos")
                
                # IMPORTANTE: Solo procesamos la primera página (100 proyectos aprobados)
                # No iteramos páginas adicionales ya que solo monitoreamos los más recientes
                logger.info("Limitando a primera página - solo proyectos aprobados más recientes")
                
                # Iterar páginas siguientes (deshabilitado para monitoreo de aprobados)
                while False and self._has_next_page(page) and pages_scraped < self.config.MAX_PAGES:
                    # Rate limiting
                    time.sleep(self.config.RATE_LIMIT_DELAY)
                    
                    if not self._go_to_next_page(page):
                        logger.warning("No se pudo navegar a siguiente página")
                        break
                    
                    html = page.content()
                    
                    if not validate_html_has_results(html):
                        logger.warning("Página sin resultados válidos")
                        break
                    
                    projects = parse_projects_from_html(html)
                    
                    # Detección de loop
                    new_ids = {p.project_id for p in projects}
                    existing_ids = {p.project_id for p in all_projects}
                    
                    # Debug: mostrar primeros IDs
                    if projects:
                        sample_ids = [p.project_id for p in projects[:3]]
                        logger.info(f"Primeros 3 IDs de esta página: {sample_ids}")
                    
                    duplicates = new_ids.intersection(existing_ids)
                    if new_ids.issubset(existing_ids):
                        logger.warning(f"Página tiene {len(duplicates)} proyectos duplicados (100%), deteniendo")
                        logger.info(f"Ejemplo IDs duplicados: {list(duplicates)[:3]}")
                        break
                    
                    all_projects.extend(projects)
                    pages_scraped += 1
                    
                    logger.info(f"Página {pages_scraped}: {len(projects)} proyectos")
                    
                    # Límite de seguridad
                    if len(all_projects) >= self.config.MAX_PROJECTS_PER_RUN:
                        logger.warning("Alcanzado límite máximo de proyectos")
                        break
                
                # Deduplicar
                all_projects = deduplicate_projects(all_projects)
                
                browser.close()
                
                duration = time.time() - start_time
                
                meta = ScrapeMeta(
                    method='playwright',
                    pages_scraped=pages_scraped,
                    total_projects=len(all_projects),
                    duration_seconds=duration,
                    errors=errors,
                    success=True
                )
                
                logger.info(
                    f"Scraping con Playwright completado: {len(all_projects)} proyectos "
                    f"en {pages_scraped} páginas ({duration:.1f}s)"
                )
                
                return all_projects, meta
            
            except Exception as e:
                duration = time.time() - start_time
                error_msg = f"Error en scraping con Playwright: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                
                # Intentar guardar debug info
                try:
                    if 'page' in locals():
                        self._save_debug_info(page, "error")
                except:
                    pass
                
                try:
                    if 'browser' in locals():
                        browser.close()
                except:
                    pass
                
                meta = ScrapeMeta(
                    method='playwright',
                    pages_scraped=pages_scraped,
                    total_projects=len(all_projects),
                    duration_seconds=duration,
                    errors=errors,
                    success=False
                )
                
                raise Exception(error_msg) from e


def scrape_with_playwright(config: Config) -> tuple[list[Project], ScrapeMeta]:
    """
    Función de entrada para scraping con Playwright.
    
    Args:
        config: Configuración del sistema
    
    Returns:
        Tupla de (proyectos, metadata)
    """
    scraper = SEIAPlaywrightScraper(config)
    return scraper.scrape()

