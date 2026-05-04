"""
Scraper para detectar el primer ICSARA de un proyecto en el SEIA.

Flujo:
1. Navega a la ficha principal del proyecto
2. Hace click en "Expediente de Evaluación de Impacto Ambiental"
3. Busca documentos tipo ICSARA en la lista resultante
4. Retorna la fecha del primero si existe, None si no hay ICSARA aún
"""

import time
import random
from datetime import datetime
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup

from seia_monitor.config import Config
from seia_monitor.logger import get_logger

logger = get_logger("scraper_icsara")

REALISTIC_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


def _build_ficha_url(url_detalle: str) -> str:
    """
    Construye la URL de ficha principal a partir de la URL de detalle.
    La URL de ficha usa modo=ficha, que expone las pestañas del expediente.
    """
    if 'id_expediente=' in url_detalle:
        project_id_raw = url_detalle.split('id_expediente=')[1].split('&')[0]
        return (
            f"https://seia.sea.gob.cl/expediente/ficha/fichaPrincipal.php"
            f"?modo=ficha&id_expediente={project_id_raw}"
        )
    return url_detalle


def _extract_icsara_date(html: str) -> Optional[str]:
    """
    Parsea el HTML de la sección de expediente buscando documentos ICSARA.

    Estrategias:
    1. Buscar filas de tabla que contengan "ICSARA" en cualquier celda
    2. Buscar spans/divs que contengan "ICSARA"
    3. Buscar por texto parcial "icsara" (case-insensitive)

    Returns:
        Fecha del primer ICSARA como string, o None si no existe.
    """
    soup = BeautifulSoup(html, 'lxml')

    # Estrategia 1: Buscar en filas de tabla
    rows = soup.find_all('tr')
    icsara_rows = []
    for row in rows:
        row_text = row.get_text(separator=' ', strip=True)
        if 'icsara' in row_text.lower():
            icsara_rows.append(row)

    if icsara_rows:
        # Ordenar por fecha si hay múltiples — buscar la más antigua (primer ICSARA)
        # Intentar extraer fecha de cada fila
        dated_rows = []
        for row in icsara_rows:
            cells = row.find_all(['td', 'th'])
            for cell in cells:
                text = cell.get_text(strip=True)
                # Patrones de fecha: dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd
                import re
                date_match = re.search(
                    r'(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})',
                    text
                )
                if date_match:
                    dated_rows.append(date_match.group(1))
                    break

        if dated_rows:
            # Retornar la primera fecha encontrada (orden original = cronológico en SEIA)
            return dated_rows[0]

        # Si no se extrajo fecha, retornar texto completo de la primera fila ICSARA
        first_row_text = icsara_rows[0].get_text(separator=' | ', strip=True)
        logger.warning(f"ICSARA encontrado pero sin fecha clara: {first_row_text[:100]}")
        return f"Fecha no extraída — {first_row_text[:80]}"

    # Estrategia 2: Buscar en cualquier elemento con texto ICSARA
    all_elements = soup.find_all(string=lambda t: t and 'icsara' in t.lower())
    if all_elements:
        # Buscar una fecha cercana al primer elemento
        import re
        for elem in all_elements:
            parent = elem.find_parent()
            if not parent:
                continue
            # Buscar fecha en el ancestro más cercano
            for ancestor in [parent, parent.find_parent(), parent.find_parent().find_parent() if parent.find_parent() else None]:
                if not ancestor:
                    continue
                ancestor_text = ancestor.get_text(separator=' ', strip=True)
                date_match = re.search(
                    r'(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})',
                    ancestor_text
                )
                if date_match:
                    return date_match.group(1)
        return "Fecha no extraída"

    return None


def check_first_icsara(
    url_detalle: str,
    project_id: str,
    retry_count: int = 1
) -> Optional[str]:
    """
    Verifica si un proyecto tiene su primer ICSARA dictado.

    Args:
        url_detalle: URL de detalle del proyecto
        project_id: ID del proyecto (para logs)
        retry_count: Reintentos en caso de fallo

    Returns:
        Fecha del primer ICSARA como string si existe, None si no hay ICSARA aún.
        Lanza Exception si no se pudo acceder al expediente.
    """
    config = Config()
    ficha_url = _build_ficha_url(url_detalle)

    for attempt in range(retry_count + 1):
        try:
            logger.info(
                f"Verificando ICSARA de {project_id} "
                f"(intento {attempt + 1}/{retry_count + 1})"
            )

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=config.PLAYWRIGHT_HEADLESS,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                    ]
                )
                try:
                    context = browser.new_context(
                        user_agent=config.USER_AGENT,
                        viewport={'width': 1920, 'height': 1080},
                        locale='es-CL',
                        timezone_id='America/Santiago',
                        extra_http_headers=REALISTIC_HEADERS,
                        ignore_https_errors=True
                    )
                    page = context.new_page()
                    page.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    """)
                    page.set_default_timeout(config.REQUEST_TIMEOUT * 1000)

                    # Paso 1: Establecer sesión en la página principal
                    logger.info(f"  → Estableciendo sesión...")
                    page.goto('https://seia.sea.gob.cl/', wait_until='networkidle')
                    time.sleep(random.uniform(1, 2))

                    # Paso 2: Navegar a la ficha del proyecto (modo=ficha expone pestañas)
                    logger.info(f"  → Cargando ficha: {ficha_url}")
                    page.goto(ficha_url, wait_until='networkidle')
                    time.sleep(random.uniform(1, 2))

                    # Paso 3: Buscar y hacer click en "Expediente de Evaluación"
                    logger.info("  → Buscando pestaña Expediente de Evaluación...")
                    expediente_clicked = False

                    # Intentar diferentes selectores para el link/tab del expediente
                    selectors = [
                        'a:has-text("Expediente de Evaluación")',
                        'a:has-text("Expediente")',
                        'button:has-text("Expediente de Evaluación")',
                        'li:has-text("Expediente de Evaluación") a',
                        '[href*="expediente"]',
                    ]
                    for selector in selectors:
                        try:
                            element = page.locator(selector).first
                            if element.count() > 0:
                                element.click()
                                expediente_clicked = True
                                logger.info(f"  → Click en expediente con selector: {selector}")
                                break
                        except Exception:
                            continue

                    if not expediente_clicked:
                        # Intentar buscar por texto parcial en todos los links
                        links = page.locator('a').all()
                        for link in links:
                            try:
                                link_text = link.inner_text()
                                if 'expediente' in link_text.lower() and 'evaluaci' in link_text.lower():
                                    link.click()
                                    expediente_clicked = True
                                    logger.info(f"  → Click en link: {link_text[:60]}")
                                    break
                            except Exception:
                                continue

                    if not expediente_clicked:
                        logger.warning(f"  → No se encontró pestaña de expediente para {project_id}")
                        return None

                    # Paso 4: Esperar a que cargue el contenido del expediente
                    time.sleep(random.uniform(2, 3))
                    try:
                        page.wait_for_load_state('networkidle', timeout=10000)
                    except Exception:
                        pass

                    # Paso 5: Obtener HTML y buscar ICSARA
                    html = page.content()
                finally:
                    browser.close()

            fecha_icsara = _extract_icsara_date(html)

            if fecha_icsara:
                logger.info(f"  → ICSARA encontrado: {fecha_icsara}")
            else:
                logger.info(f"  → Sin ICSARA aún para {project_id}")

            return fecha_icsara

        except PlaywrightTimeout as e:
            logger.warning(f"Timeout en {project_id} (intento {attempt + 1}): {e}")
            if attempt < retry_count:
                time.sleep(2 ** attempt)
            else:
                raise Exception(f"Timeout después de {retry_count + 1} intentos: {e}")

        except Exception as e:
            logger.error(f"Error verificando ICSARA de {project_id} (intento {attempt + 1}): {e}")
            if attempt < retry_count:
                time.sleep(2 ** attempt)
            else:
                raise

    return None
