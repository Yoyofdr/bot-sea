"""
Scraper AUTO - Fachada que intenta requests y hace fallback a Playwright.
Scrappea proyectos "Aprobado" y "En Admisión" en dos pasadas y los mergea.
"""

from seia_monitor.config import Config
from seia_monitor.logger import get_logger
from seia_monitor.models import Project, ScrapeMeta
from seia_monitor.scraper_requests import scrape_with_requests
from seia_monitor.scraper_playwright import scrape_with_playwright

logger = get_logger("scraper")

# Valor del campo estadoProyecto en el formulario SEIA para "En Admisión"
ESTADO_EN_ADMISION_FORM = "En Admisión"


def _merge_projects(primary: list[Project], secondary: list[Project]) -> list[Project]:
    """Mergea dos listas de proyectos; primary tiene precedencia por project_id."""
    seen = {p.project_id for p in primary}
    merged = list(primary)
    for p in secondary:
        if p.project_id not in seen:
            merged.append(p)
            seen.add(p.project_id)
    return merged


def _scrape_single_estado(
    config: Config, estado: str, mode: str
) -> tuple[list[Project], ScrapeMeta]:
    """Scrape de un solo estado usando la estrategia indicada."""
    if mode == "playwright":
        return scrape_with_playwright(config, estado=estado)
    if mode == "requests":
        return scrape_with_requests(config, estado=estado)

    # AUTO: intentar requests, fallback a playwright
    try:
        projects, meta = scrape_with_requests(config, estado=estado)
        if meta.success and projects:
            return projects, meta
        logger.warning(f"Requests sin resultados para '{estado}', fallback a Playwright")
    except Exception as e:
        logger.warning(f"Requests falló para '{estado}': {e}, fallback a Playwright")

    return scrape_with_playwright(config, estado=estado)


def scrape_seia(config: Config) -> tuple[list[Project], ScrapeMeta]:
    """
    Scraping inteligente con fallback automático.

    Estrategia:
    1. Scrape de proyectos "Aprobado" (principal)
    2. Scrape de proyectos "En Admisión" (best-effort, no interrumpe si falla)
    3. Merge de ambas listas (dedup por project_id)

    Returns:
        Tupla de (lista de proyectos, metadata del scrape principal)

    Raises:
        Exception: Si el scrape de "Aprobado" falla completamente
    """
    mode = config.SCRAPE_MODE.lower()

    if mode not in ("auto", "requests", "playwright"):
        raise ValueError(
            f"SCRAPE_MODE inválido: {mode}. "
            "Valores válidos: 'auto', 'requests', 'playwright'"
        )

    # ── Scrape principal: Aprobado ────────────────────────────────────────
    logger.info(f"Scraping 'Aprobado' (modo {mode})")
    projects_aprobado, meta = _scrape_single_estado(config, "Aprobado", mode)
    logger.info(f"Aprobado: {len(projects_aprobado)} proyectos scrapeados")

    # ── Scrape secundario: En Admisión (best-effort) ──────────────────────
    projects_admision: list[Project] = []
    try:
        logger.info(f"Scraping 'En Admisión' (modo {mode})")
        admision_projects, _ = _scrape_single_estado(
            config, ESTADO_EN_ADMISION_FORM, mode
        )
        projects_admision = admision_projects
        logger.info(f"En Admisión: {len(projects_admision)} proyectos scrapeados")
    except Exception as e:
        logger.warning(f"Scrape 'En Admisión' falló (se omite): {e}")

    # ── Merge ─────────────────────────────────────────────────────────────
    all_projects = _merge_projects(projects_aprobado, projects_admision)
    meta.total_projects = len(all_projects)

    logger.info(
        f"Total merged: {len(all_projects)} proyectos "
        f"({len(projects_aprobado)} aprobados + {len(projects_admision)} en admisión)"
    )
    return all_projects, meta
