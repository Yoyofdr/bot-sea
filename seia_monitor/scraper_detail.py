"""
Scraper de detalles de proyectos individuales del SEIA.
Extrae información completa de la página de detalle de cada proyecto.
"""

import time
import random
from pathlib import Path
from datetime import datetime
from typing import Optional
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup

from seia_monitor.config import Config
from seia_monitor.logger import get_logger
from seia_monitor.models import ProjectDetails
from seia_monitor.normalizer import normalize_string

logger = get_logger("scraper_detail")


# Headers más realistas para evitar detección
REALISTIC_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}


def _save_debug_info(url: str, html: str, prefix: str = "detail_error"):
    """Guarda HTML para debugging"""
    config = Config()
    debug_dir = config.BASE_DIR / "data" / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = debug_dir / f"{prefix}_{timestamp}.html"
    
    try:
        html_path.write_text(html, encoding='utf-8')
        logger.info(f"HTML de debug guardado: {html_path}")
    except Exception as e:
        logger.error(f"Error guardando HTML de debug: {e}")


def _extract_field_value(soup: BeautifulSoup, label_text: str) -> Optional[str]:
    """
    Extrae el valor de un campo buscando por el texto del label.
    
    Args:
        soup: BeautifulSoup object del HTML
        label_text: Texto del label a buscar (ej: "Monto de Inversión")
    
    Returns:
        El valor del campo o None si no se encuentra
    """
    try:
        # Estrategia SEIA específica: estructura Bootstrap con divs
        # <div class="row">
        #   <div class="col-md-3"><span>Label</span></div>
        #   <div class="col-md-9"><h6>Valor</h6></div>
        # </div>
        
        all_spans = soup.find_all('span')
        for span in all_spans:
            span_text = span.get_text(strip=True)
            if label_text.lower() in span_text.lower():
                # Buscar el contenedor row
                row = span.find_parent('div', class_='row')
                if row:
                    # Buscar el div con el valor (normalmente col-md-9)
                    value_div = row.find('div', class_=lambda x: x and 'col-md-9' in x)
                    if value_div:
                        # El valor puede estar en h6, p, o directamente en el div
                        h6 = value_div.find('h6')
                        if h6:
                            return h6.get_text(strip=True)
                        p = value_div.find('p')
                        if p:
                            return p.get_text(strip=True)
                        return value_div.get_text(strip=True)
        
        # Estrategia 2: Buscar en <h6> o header con el texto
        headers = soup.find_all(['h6', 'h5', 'h4', 'strong', 'b'])
        for header in headers:
            if header.get_text(strip=True) and label_text.lower() in header.get_text(strip=True).lower():
                # El valor puede estar en el siguiente elemento
                next_elem = header.find_next_sibling()
                if next_elem:
                    value = next_elem.get_text(strip=True)
                    if value:
                        return value
        
        # Estrategia 3: Buscar en tablas
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                first_cell = cells[0].get_text(strip=True)
                if label_text.lower() in first_cell.lower():
                    return cells[1].get_text(strip=True)
        
    except Exception as e:
        logger.debug(f"Error extrayendo campo '{label_text}': {e}")
    
    return None


def _extract_description(soup: BeautifulSoup) -> Optional[str]:
    """
    Extrae la descripción completa del proyecto.
    
    Args:
        soup: BeautifulSoup object del HTML
    
    Returns:
        La descripción completa o None si no se encuentra
    """
    try:
        # Estrategia 1: buscar div con clase sg-description-file (Ficha Principal)
        desc_div = soup.find('div', class_=lambda x: x and 'sg-description-file' in x)
        if desc_div:
            # En Ficha Principal el texto está dentro de un div con padding o directamente
            # Intentamos limpiar el texto manteniendo saltos de línea
            desc = desc_div.get_text(separator=' ', strip=True)
            if len(desc) > 20:
                return desc
        
        # Estrategia 2: Buscar contenedor de texto que tenga "El proyecto consiste" o similar
        # En la descripción del SEIA suele empezar así
        content_divs = soup.find_all('div', style=lambda x: x and 'text-align: justify' in x)
        for div in content_divs:
            text = div.get_text(strip=True)
            if len(text) > 100:
                return text

        # Estrategia 3: Buscar por span "Descripción del Proyecto" y obtener el contenido
        all_spans = soup.find_all('span')
        for span in all_spans:
            if 'descripci' in span.get_text(strip=True).lower() and 'proyecto' in span.get_text(strip=True).lower():
                # En Ficha Principal el valor está en la misma fila o en el siguiente div
                row = span.find_parent('div', class_='row')
                if row:
                    value_div = row.find('div', class_=lambda x: x and 'col-md-9' in x)
                    if value_div:
                        desc = value_div.get_text(strip=True)
                        if len(desc) > 20:
                            return desc
        
    except Exception as e:
        logger.error(f"Error extrayendo descripción: {e}")
    
    return None


def _extract_contact_section(soup: BeautifulSoup, section_title: str) -> dict:
    """
    Extrae información de una sección de contacto (Titular o Representante Legal).
    
    Args:
        soup: BeautifulSoup object del HTML
        section_title: Título de la sección (ej: "Titular", "Representante Legal")
    
    Returns:
        Dict con los campos extraídos
    """
    contact_info = {
        'nombre': None,
        'domicilio': None,
        'ciudad': None,
        'telefono': None,
        'fax': None,
        'email': None
    }
    
    try:
        # Buscar el header h2 con el título de la sección
        all_h2 = soup.find_all('h2')
        section_container = None
        
        for h2 in all_h2:
            if section_title.lower() in h2.get_text(strip=True).lower():
                # Encontramos el header, buscar el div contenedor siguiente
                section_container = h2.find_next('div')
                break
        
        if not section_container:
            logger.warning(f"No se encontró sección '{section_title}'")
            return contact_info
        
        # Buscar todos los campos usando la estructura Bootstrap de SEIA
        # <div class="row">
        #   <div class="col-md-3"><span>Label</span></div>
        #   <div class="col-md-9"><h6>Valor</h6></div>
        # </div>
        
        all_rows = section_container.find_all('div', class_='row')
        for row in all_rows:
            # Buscar el label
            label_div = row.find('div', class_=lambda x: x and 'col-md-3' in x)
            value_div = row.find('div', class_=lambda x: x and 'col-md-9' in x)
            
            if label_div and value_div:
                label = label_div.get_text(strip=True).lower()
                value_h6 = value_div.find('h6')
                value = value_h6.get_text(strip=True) if value_h6 else value_div.get_text(strip=True)
                
                # Mapear el campo
                if 'nombre' in label or 'name' in label:
                    contact_info['nombre'] = value
                elif 'domicilio' in label or 'direcci' in label:
                    contact_info['domicilio'] = value
                elif 'ciudad' in label or 'city' in label:
                    contact_info['ciudad'] = value
                elif 'tel' in label or 'phone' in label:
                    contact_info['telefono'] = value
                elif 'fax' in label:
                    contact_info['fax'] = value
                elif 'email' in label or 'e-mail' in label or 'correo' in label:
                    # Extraer el email del link si existe
                    link = value_div.find('a')
                    if link and 'mailto:' in link.get('href', ''):
                        contact_info['email'] = link.get('href').replace('mailto:', '').strip()
                    else:
                        contact_info['email'] = value
    
    except Exception as e:
        logger.error(f"Error extrayendo sección '{section_title}': {e}")
    
    return contact_info


def _extract_field_from_container(container, label_text: str) -> Optional[str]:
    """
    Extrae un campo específico de un contenedor.
    
    Args:
        container: BeautifulSoup element del contenedor
        label_text: Texto del label a buscar
    
    Returns:
        El valor del campo o None
    """
    try:
        # Buscar todos los elementos de texto
        all_tags = container.find_all(True)
        
        for i, tag in enumerate(all_tags):
            tag_text = tag.get_text(strip=True)
            if label_text.lower() in tag_text.lower():
                # El valor puede estar:
                # 1. En el mismo elemento después del label
                if ':' in tag_text or '#' in tag_text:
                    parts = tag_text.split(':' if ':' in tag_text else '#', 1)
                    if len(parts) > 1:
                        value = parts[1].strip()
                        if value:
                            return value
                
                # 2. En el siguiente hermano
                next_sibling = tag.find_next_sibling()
                if next_sibling:
                    value = next_sibling.get_text(strip=True)
                    if value and len(value) < 200:  # Evitar capturar bloques grandes
                        return value
                
                # 3. En el siguiente elemento en la lista
                if i + 1 < len(all_tags):
                    next_tag = all_tags[i + 1]
                    value = next_tag.get_text(strip=True)
                    if value and len(value) < 200:
                        return value
    
    except Exception as e:
        logger.debug(f"Error extrayendo campo '{label_text}' de contenedor: {e}")
    
    return None


def scrape_project_details(url: str, retry_count: int = 2) -> ProjectDetails:
    """
    Extrae los detalles completos de un proyecto desde su página de detalle.
    
    Args:
        url: URL de la página de detalle del proyecto
        retry_count: Número de reintentos en caso de error
    
    Returns:
        ProjectDetails con toda la información extraída
    
    Raises:
        Exception si no se puede scrapear después de los reintentos
    """
    config = Config()
    
    for attempt in range(retry_count + 1):
        try:
            logger.info(f"Scrapeando detalles de: {url} (intento {attempt + 1}/{retry_count + 1})")
            
            with sync_playwright() as p:
                # Lanzar con args anti-detección
                browser = p.chromium.launch(
                    headless=config.PLAYWRIGHT_HEADLESS,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process'
                    ]
                )
                
                # Contexto con características de navegador real
                context = browser.new_context(
                    user_agent=config.USER_AGENT,
                    viewport={'width': 1920, 'height': 1080},
                    locale='es-CL',
                    timezone_id='America/Santiago',
                    extra_http_headers=REALISTIC_HEADERS,
                    ignore_https_errors=True
                )
                
                page = context.new_page()
                
                # Ocultar que somos un bot
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['es-CL', 'es', 'en']
                    });
                    window.chrome = { runtime: {} };
                """)
                
                # Configurar timeout
                page.set_default_timeout(config.REQUEST_TIMEOUT * 1000)
                
                # PASO 1: Primero visitar la página principal para establecer sesión legítima
                logger.info("  → Estableciendo sesión legítima...")
                page.goto('https://seia.sea.gob.cl/', wait_until='networkidle')
                time.sleep(random.uniform(2, 4))
                
                # Simular comportamiento humano en la página principal
                page.evaluate('window.scrollTo(0, 300)')
                time.sleep(random.uniform(1, 2))
                
                # PASO 2: Navegar a busqueda para parecer más humano
                logger.info("  → Navegando a través del sitio...")
                page.goto('https://seia.sea.gob.cl/busqueda/buscarProyecto.php', wait_until='networkidle')
                time.sleep(random.uniform(2, 3))
                
                # PASO 3: Ahora sí ir a la página de detalle
                logger.info("  → Accediendo a detalles del proyecto...")
                
                # Intentar transformar a URL de ficha principal si tenemos ID
                # Esta página es mucho más robusta y contiene toda la info de contacto
                detail_url = url
                if 'id_expediente=' in url:
                    try:
                        project_id_raw = url.split('id_expediente=')[1].split('&')[0]
                        detail_url = f"https://seia.sea.gob.cl/expediente/ficha/fichaPrincipal.php?modo=normal&id_expediente={project_id_raw}"
                        logger.info(f"  → Usando URL de ficha principal: {detail_url}")
                    except Exception:
                        pass

                page.goto(detail_url, wait_until='networkidle')
                
                # Simular comportamiento humano: scroll aleatorio
                time.sleep(random.uniform(1, 2))
                page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.3)')
                time.sleep(random.uniform(1, 2))
                page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.6)')
                time.sleep(random.uniform(0.5, 1))
                page.evaluate('window.scrollTo(0, 0)')
                
                # Esperar que cargue el contenido dinámico con tiempo aleatorio más largo
                time.sleep(random.uniform(3, 6))
                
                # Obtener HTML
                html = page.content()
                
                # Cerrar browser
                browser.close()
            
            # Parsear con BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            
            # Extraer ID del proyecto de la URL
            project_id = None
            if 'id_expediente=' in url:
                project_id = url.split('id_expediente=')[1].split('&')[0]
            
            # Extraer campos principales
            nombre_completo = _extract_field_value(soup, "Proyecto")
            if not nombre_completo:
                # Buscar en el título de la página
                title_tag = soup.find('title')
                if title_tag:
                    nombre_completo = title_tag.get_text(strip=True)
            
            tipo_proyecto = _extract_field_value(soup, "Tipo de Proyecto")
            monto_inversion = _extract_field_value(soup, "Monto de Inversión")
            if not monto_inversion:
                monto_inversion = _extract_field_value(soup, "Monto de Inversion")
            
            descripcion_completa = _extract_description(soup)
            
            # Extraer información de Titular
            titular_info = _extract_contact_section(soup, "Titular")
            
            # Extraer información de Representante Legal
            rep_legal_info = _extract_contact_section(soup, "Representante Legal")
            
            # Crear ProjectDetails
            details = ProjectDetails(
                project_id=project_id or "unknown",
                nombre_completo=nombre_completo or "No disponible",
                tipo_proyecto=tipo_proyecto or "No disponible",
                monto_inversion=monto_inversion,
                descripcion_completa=descripcion_completa,
                titular_nombre=titular_info['nombre'],
                titular_domicilio=titular_info['domicilio'],
                titular_ciudad=titular_info['ciudad'],
                titular_telefono=titular_info['telefono'],
                titular_fax=titular_info['fax'],
                titular_email=titular_info['email'],
                rep_legal_nombre=rep_legal_info['nombre'],
                rep_legal_domicilio=rep_legal_info['domicilio'],
                rep_legal_telefono=rep_legal_info['telefono'],
                rep_legal_fax=rep_legal_info['fax'],
                rep_legal_email=rep_legal_info['email'],
                scraped_at=datetime.now()
            )
            
            # Validar que al menos obtuvimos algunos campos importantes
            if not nombre_completo and not tipo_proyecto and not descripcion_completa:
                logger.warning("No se extrajo información significativa, guardando HTML para debug")
                _save_debug_info(url, html, "detail_incomplete")
            else:
                logger.info(f"Detalles extraídos exitosamente: {nombre_completo[:50] if nombre_completo else 'N/A'}")
            
            return details
        
        except PlaywrightTimeout as e:
            logger.warning(f"Timeout scrapeando {url} (intento {attempt + 1}): {e}")
            if attempt < retry_count:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Esperando {wait_time}s antes de reintentar...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Timeout después de {retry_count + 1} intentos")
        
        except Exception as e:
            logger.error(f"Error scrapeando {url} (intento {attempt + 1}): {e}")
            if attempt < retry_count:
                wait_time = 2 ** attempt
                logger.info(f"Esperando {wait_time}s antes de reintentar...")
                time.sleep(wait_time)
            else:
                # En el último intento, guardar HTML si está disponible
                try:
                    if 'html' in locals():
                        _save_debug_info(url, html, "detail_error")
                except:
                    pass
                raise Exception(f"Error después de {retry_count + 1} intentos: {e}")
    
    raise Exception(f"No se pudo scrapear {url} después de todos los intentos")

