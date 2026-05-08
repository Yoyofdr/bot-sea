"""
Scraper para detectar el primer ICSARA de un proyecto en el SEIA.

Flujo:
1. Navega a la ficha principal del proyecto (modo=ficha)
2. Extrae el href del link "Expediente de Evaluación" y navega directamente
   (si el href es JS, hace click como fallback)
3. Busca documentos tipo ICSARA en la tabla resultante
4. Retorna la fecha del primer ICSARA (más antigua), o None si no hay ninguno

Errores de navegación (tab no encontrado, timeout) lanzan Exception
para distinguirlos de "sin ICSARA aún" (retorno None).
"""

import re
import time
import random
from datetime import datetime as dt
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup

from seia_monitor.config import Config
from seia_monitor.logger import get_logger

logger = get_logger("scraper_icsara")

ICSARA_RE = re.compile(r'i\.?c\.?s\.?a\.?r\.?a\.?', re.IGNORECASE)
DATE_RE = re.compile(r'(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})')

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


def _parse_date(text: str) -> Optional[dt]:
    """Intenta parsear una fecha de texto en varios formatos. Retorna None si falla."""
    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%Y/%m/%d'):
        try:
            return dt.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _extract_icsara_date(html: str) -> Optional[str]:
    """
    Parsea el HTML del expediente buscando documentos ICSARA.

    Detecta "ICSARA" e "I.C.S.A.R.A." (regex flexible).
    Si hay varios, retorna la fecha más antigua (primer ICSARA).

    Returns:
        Fecha del primer ICSARA como string, o None si no hay ICSARA.
    """
    soup = BeautifulSoup(html, 'lxml')

    # Estrategia 1: Filas de tabla que contengan ICSARA
    icsara_rows = [
        row for row in soup.find_all('tr')
        if ICSARA_RE.search(row.get_text(separator=' ', strip=True))
    ]

    if icsara_rows:
        dated: list[tuple[dt, str]] = []
        raw_dates: list[str] = []

        for row in icsara_rows:
            for cell in row.find_all(['td', 'th']):
                m = DATE_RE.search(cell.get_text(strip=True))
                if m:
                    raw_dates.append(m.group(1))
                    parsed = _parse_date(m.group(1))
                    if parsed:
                        dated.append((parsed, m.group(1)))
                    break

        if dated:
            dated.sort(key=lambda x: x[0])
            return dated[0][1]

        if raw_dates:
            return raw_dates[0]

        first_row_text = icsara_rows[0].get_text(separator=' | ', strip=True)
        logger.warning(f"ICSARA encontrado pero sin fecha: {first_row_text[:100]}")
        return f"sin fecha — {first_row_text[:80]}"

    # Estrategia 2: Cualquier elemento con texto ICSARA (fuera de tabla)
    all_elements = soup.find_all(string=lambda t: t and ICSARA_RE.search(t))
    if all_elements:
        for elem in all_elements:
            parent = elem.find_parent()
            if not parent:
                continue
            grandparent = parent.find_parent()
            great = grandparent.find_parent() if grandparent else None
            for ancestor in [parent, grandparent, great]:
                if not ancestor:
                    continue
                m = DATE_RE.search(ancestor.get_text(separator=' ', strip=True))
                if m:
                    return m.group(1)
        return "sin fecha"

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

                    # Paso 3: Localizar el link al Expediente de Evaluación y navegar
                    logger.info("  → Buscando link Expediente de Evaluación...")
                    expediente_navigated = False

                    def _navigate_to_expediente(element) -> bool:
                        """
                        Intenta navegar al expediente desde un elemento <a>.
                        Prefiere navegar directamente via href; hace click como fallback.
                        Retorna True si navegó con éxito.
                        """
                        try:
                            href = element.get_attribute('href')
                        except Exception:
                            href = None

                        if href and not href.lower().startswith('javascript'):
                            if not href.startswith('http'):
                                base = 'https://seia.sea.gob.cl'
                                href = (
                                    f"{base}{href}" if href.startswith('/')
                                    else f"{base}/expediente/ficha/{href}"
                                )
                            logger.info(f"  → Navegando directo a: {href}")
                            page.goto(href, wait_until='networkidle')
                        else:
                            logger.info("  → Click en tab de expediente")
                            element.click()
                            try:
                                page.wait_for_load_state('networkidle', timeout=15000)
                            except Exception:
                                pass
                        return True

                    selectors = [
                        'a:has-text("Expediente de Evaluación")',
                        'button:has-text("Expediente de Evaluación")',
                        'li:has-text("Expediente de Evaluación") a',
                    ]
                    for selector in selectors:
                        try:
                            element = page.locator(selector).first
                            if element.count() > 0:
                                expediente_navigated = _navigate_to_expediente(element)
                                logger.info(f"  → Expediente cargado (selector: {selector})")
                                break
                        except Exception as e_sel:
                            logger.debug(f"  Selector '{selector}' falló: {e_sel}")
                            continue

                    if not expediente_navigated:
                        links = page.locator('a').all()
                        for link in links:
                            try:
                                link_text = link.inner_text()
                                if 'expediente' in link_text.lower() and 'evaluaci' in link_text.lower():
                                    expediente_navigated = _navigate_to_expediente(link)
                                    logger.info(f"  → Expediente cargado via link: {link_text[:60]}")
                                    break
                            except Exception:
                                continue

                    if not expediente_navigated:
                        raise RuntimeError(
                            f"No se encontró la pestaña 'Expediente de Evaluación' "
                            f"para {project_id} en {ficha_url}"
                        )

                    # Paso 4: Esperar a que aparezca la tabla de documentos
                    time.sleep(random.uniform(1, 2))
                    try:
                        page.wait_for_selector('table', timeout=10000)
                    except Exception:
                        logger.warning("  → Tabla de documentos no apareció, usando HTML disponible")

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
