"""
Motor de detección de cambios entre snapshots de proyectos.
Detecta nuevos proyectos aprobados y eventos de admisión (nuevos o transiciones).
"""

from datetime import datetime
from typing import Set

from seia_monitor.models import Project, ChangeEvent, ChangeResult
from seia_monitor.logger import get_logger

logger = get_logger("diff")


def detect_changes(
    previous: list[Project],
    current: list[Project]
) -> ChangeResult:
    """
    Detecta cambios relevantes entre dos snapshots.

    Detecta:
    - Proyectos nuevos (IDs no vistos antes) con estado "aprobado"
    - Proyectos nuevos (IDs no vistos antes) con estado "en_admision"
    - Proyectos existentes que transicionaron a estado "en_admision"

    Args:
        previous: Lista de proyectos del snapshot anterior
        current: Lista de proyectos del snapshot actual

    Returns:
        ChangeResult con los tres tipos de eventos
    """
    previous_ids: Set[str] = {p.project_id for p in previous}
    current_ids: Set[str] = {p.project_id for p in current}
    new_ids = current_ids - previous_ids

    # ── Nuevos IDs aprobados ──────────────────────────────────────────────
    nuevos = [
        p for p in current
        if p.project_id in new_ids and p.estado_normalizado == "aprobado"
    ]
    logger.info(f"Detectados {len(nuevos)} proyectos aprobados nuevos")

    # ── Nuevos IDs en admisión ────────────────────────────────────────────
    nuevos_en_admision = [
        p for p in current
        if p.project_id in new_ids and p.estado_normalizado == "en_admision"
    ]
    logger.info(f"Detectados {len(nuevos_en_admision)} proyectos nuevos en admisión")

    # ── Transiciones a en_admision en IDs ya conocidos ────────────────────
    previous_map = {p.project_id: p for p in previous}
    transiciones_admision: list[ChangeEvent] = []
    for p in current:
        if p.project_id not in previous_ids:
            continue
        prev = previous_map[p.project_id]
        if (
            prev.estado_normalizado != "en_admision"
            and p.estado_normalizado == "en_admision"
        ):
            event = ChangeEvent(
                project_id=p.project_id,
                nombre_proyecto=p.nombre_proyecto,
                estado_anterior=prev.estado,
                estado_nuevo=p.estado,
                estado_anterior_normalizado=prev.estado_normalizado,
                estado_nuevo_normalizado=p.estado_normalizado,
                region=p.region,
                url_detalle=p.url_detalle,
                timestamp=datetime.now(),
                is_relevant=True,
            )
            transiciones_admision.append(event)
    logger.info(f"Detectadas {len(transiciones_admision)} transiciones a en_admisión")

    # ── Proyectos eliminados (solo log) ───────────────────────────────────
    removed_ids = previous_ids - current_ids
    if removed_ids:
        logger.info(f"Proyectos ya no presentes: {len(removed_ids)}")

    result = ChangeResult(
        nuevos=nuevos,
        cambios_relevantes=[],
        todos_los_cambios=transiciones_admision[:],
        nuevos_en_admision=nuevos_en_admision,
        transiciones_admision=transiciones_admision,
    )

    logger.info(str(result))
    return result


def deduplicate_changes(changes: list[ChangeEvent]) -> list[ChangeEvent]:
    """
    Deduplica cambios por project_id.
    
    Si hay múltiples cambios para el mismo proyecto, mantiene el último.
    
    Args:
        changes: Lista de cambios potencialmente con duplicados
    
    Returns:
        Lista sin duplicados
    """
    seen = {}
    
    for change in changes:
        # Mantener el último (más reciente)
        seen[change.project_id] = change
    
    unique = list(seen.values())
    
    if len(unique) < len(changes):
        logger.info(f"Deduplicados {len(changes) - len(unique)} cambios")
    
    return unique

